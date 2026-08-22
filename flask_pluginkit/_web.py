# -*- coding: utf-8 -*-
"""
flask_pluginkit._web
~~~~~~~~~~~~~~~~~~~~

The server-side plugin management blueprint.

:copyright: (c) 2019 by staugur.
:license: BSD 3-Clause, see LICENSE for more details.
"""

import _thread as thread
import base64
import json
import os
import re
import signal
from time import sleep, time
from collections import OrderedDict, deque
from tempfile import NamedTemporaryFile

from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    current_app,
    g,
    request,
    jsonify,
    render_template,
    make_response,
    Response,
)

try:
    import semver

    _parse_version = semver.Version.parse
except ImportError:  # pragma: no cover
    _parse_version = None

from .utils import allowed_uploaded_plugin_suffix, check_url, pip_list
from ._installer import PluginInstaller
from ._compat import urllib2
from .version import __version__

#: Blueprint instance for managing plugins
#:
#: ..versionadded:: 3.3.0
blueprint = Blueprint(
    "flask_pluginkit",
    "flask_pluginkit",
    template_folder="templates",
    static_folder="static",
)

#: FIFO message queue
#:
#: ..versionadded:: 3.3.0
_queue = deque()

#: GitHub topic plugins cache
#:
#: The web manager calls the GitHub Search API to list repositories with the
#: fixed topic ``flask-pluginkit`` (https://github.com/topics/flask-pluginkit).
#: To avoid hitting the GitHub API rate limit (60 requests/hour
#: unauthenticated), the result is cached in memory for 8 hours; when a redis
#: client is detected on ``flask.g`` (e.g. ``g.redis``), the result is also
#: written to redis with a 7-day TTL.
#:
#: .. versionadded:: 3.12.0
_github_topic_cache = {"ts": 0, "data": None}

#: Fixed GitHub topic name
_GITHUB_TOPIC = "flask-pluginkit"

#: Only repositories whose name starts with one of these prefixes
#: (case-insensitive) are collected.
_GITHUB_TOPIC_NAME_PREFIXES = ("flask-pluginkit-", "flask_pluginkit_")

#: In-memory cache TTL (seconds), 8 hours
_GITHUB_TOPIC_CACHE_TTL = 8 * 60 * 60

#: Redis cache TTL (seconds), 7 days
_GITHUB_TOPIC_REDIS_TTL = 7 * 24 * 60 * 60

#: Redis cache key
_GITHUB_TOPIC_REDIS_KEY = "flask_pluginkit_github_topic"

#: Attribute names on flask.g that may hold a redis client
_GITHUB_TOPIC_REDIS_G_ATTRS = ("redis", "redis_client")

#: Official plugins hub API URL
#:
#: The web manager reads the official plugins list from this URL and
#: enriches each plugin with metadata from the PyPI JSON API. This is the
#: official URL provided by the author and is fixed - it cannot be changed
#: via configuration. When this API is unreachable, the raw plugin list on
#: the official repository is used as a fallback (see
#: :data:`_HUB_FALLBACK_URL`).
#:
#: .. versionadded:: 3.12.0
_HUB_API_URL = "https://hub.saintic.com/openservice/flask-pluginkit"

#: Fallback official plugins list, the GitHub Contents API
#:
#: Used when the hub API (see :data:`_HUB_API_URL`) is unreachable. The
#: GitHub Contents API returns the file metadata with a base64-encoded
#: ``content`` field, which is decoded and parsed as the plugins list.
#:
#: .. versionadded:: 3.12.0
_HUB_FALLBACK_URL = (
    "https://api.github.com/repos/staugur/Flask-PluginKit/contents/awesome/list.json"
)

#: Official plugins in-memory cache, cleared every 8 hours
#:
#: .. versionadded:: 3.12.0
_official_plugins_cache = {"ts": 0, "data": None}

#: In-memory cache TTL (seconds), 8 hours
_OFFICIAL_CACHE_TTL = 8 * 60 * 60

#: Redis cache TTL (seconds), 7 days
_OFFICIAL_REDIS_TTL = 7 * 24 * 60 * 60

#: Redis cache key
_OFFICIAL_REDIS_KEY = "flask_pluginkit_official_plugins"

#: Latest GitHub release cache, ``{full_name: {"ts": ..., "version": ...}}``
#:
#: The latest release of each plugin repository is read from the GitHub
#: Releases API and cached in memory for 8 hours, so listing the plugins
#: never hammers the API rate limit (60 requests/hour unauthenticated).
#:
#: .. versionadded:: 3.12.0
_release_cache = {}

#: In-memory cache TTL (seconds), 8 hours
#:
#: .. versionadded:: 3.12.0
_RELEASE_CACHE_TTL = 8 * 60 * 60

#: Installed-packages cache, refreshed every 5 minutes.
#:
#: Marking plugins as installed/upgradable runs ``pip list`` (a subprocess
#: that takes a noticeable amount of time), so without a cache every listing
#: request would pay that cost again even when the plugin list itself is
#: served from cache. The map is kept for a few minutes and dropped whenever
#: an install happens, so a freshly installed plugin shows up almost
#: immediately instead of waiting for the TTL to expire.
#:
#: .. versionadded:: 3.12.0
_installed_cache = {"ts": 0, "data": {}, "target_dir": ""}

#: Installed-packages cache TTL (seconds), 5 minutes
#:
#: .. versionadded:: 3.12.0
_INSTALLED_CACHE_TTL = 300

#: User agent string for HTTP requests
#:
#: .. versionadded:: 3.12.0
_USER_AGENT = f"Flask-PluginKit/{__version__}"


def _invalidate_installed_cache():
    """Drop the cached installed-packages map.

    Called after any action that installs a plugin (install, upload,
    download) so the next listing re-runs ``pip list`` and reflects the new
    state immediately instead of waiting for the TTL to expire.

    .. versionadded:: 3.12.0
    """
    _installed_cache.update(ts=0, data={}, target_dir="")


def _get_redis_client():
    """Detect a redis client attached to flask.g.

    Returns the first non-None value found among ``g.redis`` and
    ``g.redis_client``, or None when no redis client is available.
    """
    for name in _GITHUB_TOPIC_REDIS_G_ATTRS:
        client = getattr(g, name, None)
        if client is not None:
            return client
    return None


def _redis_get(client, key=_GITHUB_TOPIC_REDIS_KEY):
    """Read a cached plugins result from redis, return None on miss/failure."""
    try:
        value = client.get(key)
    except Exception:
        return None
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _redis_set(
    client, result, key=_GITHUB_TOPIC_REDIS_KEY, ttl=_GITHUB_TOPIC_REDIS_TTL
):
    """Write a cached plugins result to redis with a TTL.

    Redis is best-effort: failures are silently ignored.
    """
    try:
        if hasattr(client, "setex"):
            client.setex(key, ttl, json.dumps(result))
        elif hasattr(client, "set"):
            client.set(key, json.dumps(result), ex=ttl)
    except Exception:
        pass


def _github_urlopen(req, timeout=10, use_proxy=True):
    """Open a GitHub API request, optionally through a proxy.

    When the ``PLUGINKIT_PROXY`` config item is set (e.g.
    ``http://127.0.0.1:7890``) the request is routed through that proxy,
    which is handy in networks where the GitHub API is blocked or slow.
    The official hub API and PyPI requests do not go through the proxy
    (``use_proxy=False`` or simply not calling this helper).

    .. versionadded:: 3.12.0
    """
    proxy = ""
    if use_proxy:
        proxy = _get_conf("PLUGINKIT_PROXY") or ""
    if proxy:
        opener = urllib2.build_opener(
            urllib2.ProxyHandler({"http": proxy, "https": proxy})
        )
        return opener.open(req, timeout=timeout)
    return urllib2.urlopen(req, timeout=timeout)


def _list_github_topic_plugins():
    """List repositories with the ``flask-pluginkit`` GitHub topic.

    Returns ``(result, cached)``, where ``result`` is a dict containing the
    topic, total count and a list of plugin repositories fetched from the
    GitHub Search API (same data shown on
    https://github.com/topics/flask-pluginkit). Only repositories whose name
    starts with ``flask-pluginkit-`` or ``flask_pluginkit_`` (case-insensitive)
    are collected.

    The result is served from the in-memory cache (8 hours) first, then from
    redis (7 days) when a redis client is detected on ``flask.g``, and only
    falls back to the GitHub API on a full cache miss. When the API is
    queried, both caches are refreshed.

    Configuration:
        - ``PLUGINKIT_PROXY``: optional HTTP(S) proxy for GitHub API
          requests (e.g. ``http://127.0.0.1:7890``), useful when the GitHub
          API is blocked or slow in the deployment network. The GitHub API
          base URL is fixed to the official ``https://api.github.com`` and
          is not configurable.

    .. versionadded:: 3.12.0
    """
    api = "https://api.github.com"
    now = int(time())
    data = _github_topic_cache.get("data")
    if data and now - _github_topic_cache["ts"] < _GITHUB_TOPIC_CACHE_TTL:
        return data, True
    redis_client = _get_redis_client()
    if redis_client is not None:
        data = _redis_get(redis_client)
        if data:
            _github_topic_cache.update(ts=now, data=data)
            return data, True
    url = (
        "{0}/search/repositories?q=topic:{1}"
        "&sort=stars&order=desc&per_page=30".format(api, _GITHUB_TOPIC)
    )
    req = urllib2.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": _USER_AGENT,
        },
    )
    try:
        with _github_urlopen(req) as f:
            resp = json.loads(f.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError("Fetch GitHub topic plugins failed: %s" % e)
    plugins = []
    for item in resp.get("items") or []:
        name = item.get("name") or ""
        lowered = name.lower()
        if not any(lowered.startswith(p) for p in _GITHUB_TOPIC_NAME_PREFIXES):
            continue
        license_name = (item.get("license") or {}).get("spdx_id")
        full_name = item.get("full_name") or ""
        plugins.append(
            {
                "name": name,
                "full_name": full_name,
                "description": item.get("description") or "",
                "url": item.get("html_url"),
                "homepage": item.get("homepage") or "",
                "stars": item.get("stargazers_count") or 0,
                "forks": item.get("forks_count") or 0,
                "language": item.get("language") or "",
                "license": license_name or "",
                "default_branch": item.get("default_branch") or "",
                "updated_at": item.get("updated_at") or "",
                "archived": item.get("archived") or False,
                "latest_version": _get_latest_release_version(full_name),
            }
        )
    plugins.sort(key=lambda p: p["stars"], reverse=True)
    result = {
        "topic": _GITHUB_TOPIC,
        "total_count": len(plugins),
        "plugins": plugins,
    }
    _github_topic_cache.update(ts=now, data=result)
    if redis_client is not None:
        _redis_set(redis_client, result)
    return result, False


def _normalize_github_url(url):
    """Normalize a GitHub URL/identifier from the hub data.

    The hub API may return a full URL (``https://github.com/owner/repo``) or
    a bare ``owner/repo`` string. Accepts both and returns a full
    ``https://github.com/...`` URL, or an empty string when ``url`` is empty.

    .. versionadded:: 3.12.0
    """
    if not url:
        return ""
    url = str(url).strip()
    if url.startswith(("https://github.com/", "http://github.com/")):
        return url
    if url.startswith("github.com/"):
        return "https://" + url
    if "/" in url:
        return "https://github.com/" + url
    return url


def _github_full_name(url):
    """Extract the ``owner/repo`` identifier from a GitHub URL.

    The hub data may carry the github field as a full URL
    (``https://github.com/owner/repo``) or a bare ``owner/repo`` string.
    The normalized URL (see :func:`_normalize_github_url`) always points at
    a repository, so its last two path segments are the identifier used for
    installation via ``git+https://github.com/<full_name>``.

    .. versionadded:: 3.12.0
    """
    url = _normalize_github_url(url)
    if not url:
        return ""
    parts = url.rstrip("/").split("/")
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    return ""


def _version_gt(newer, older):
    """Return True when ``newer`` is a newer version than ``older``.

    Uses ``semver`` (declared in ``setup.py``) when available and falls
    back to comparing the numeric dot-segments of both versions, so tags
    like ``v1.2.3`` and plain ``1.2.3`` can be compared.

    .. versionadded:: 3.12.0
    """
    if not newer or not older:
        return False
    if _parse_version is not None:
        try:
            return _parse_version(newer) > _parse_version(older)
        except Exception:
            pass

    def _num_key(version):
        return [int(x) for x in re.findall(r"\d+", version)]

    try:
        return _num_key(newer) > _num_key(older)
    except Exception:
        return False


def _get_latest_release_version(full_name):
    """Return the latest release version of a GitHub repository, or ''.

    Queries the GitHub Releases API (``/repos/<full_name>/releases/latest``)
    and returns the release ``tag_name`` with a leading ``v`` stripped. The
    result is cached in memory for 8 hours; any failure (no releases yet,
    rate limit, network error) yields an empty string so the plugin listing
    never fails because of it.

    .. versionadded:: 3.12.0
    """
    full_name = (full_name or "").strip("/")
    if not full_name:
        return ""
    now = int(time())
    cached = _release_cache.get(full_name)
    if cached and now - cached["ts"] < _RELEASE_CACHE_TTL:
        return cached["version"]
    version = ""
    try:
        req = urllib2.Request(
            "https://api.github.com/repos/{0}/releases/latest".format(full_name),
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": _USER_AGENT,
            },
        )
        with _github_urlopen(req) as f:
            resp = json.loads(f.read().decode("utf-8"))
        tag = (resp.get("tag_name") or "").strip()
        if tag:
            version = re.sub(r"^[vV]", "", tag).strip()
    except Exception:
        version = ""
    _release_cache[full_name] = {"ts": now, "version": version}
    return version


def _get_pypi_package_info(package_name):
    """Query the PyPI JSON API for the latest version metadata.

    Returns the ``info`` dict (name, version, summary, home_page, author,
    license, docs_url, requires_python, project_urls, ...) or None when the
    package does not exist on PyPI.

    .. versionadded:: 3.12.0
    """
    url = "https://pypi.org/pypi/{0}/json".format(package_name)
    req = urllib2.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        },
    )
    try:
        with urllib2.urlopen(req, timeout=10) as f:
            resp = json.loads(f.read().decode("utf-8"))
    except urllib2.HTTPError as e:
        if e.code == 404:
            return None
        raise RuntimeError("Fetch PyPI package failed: %s" % e)
    except Exception as e:
        raise RuntimeError("Fetch PyPI package failed: %s" % e)
    return resp.get("info") or {}


def _fetch_official_plugins(url, use_proxy=False):
    """Fetch the raw official plugins list from a hub URL.

    Returns a list of plugin dicts (each carrying ``name`` / ``github`` /
    ``ctime`` / ``tag``), or None when the URL is unreachable (HTTP 4xx /
    5xx, timeout, network error) or returns an invalid payload. When
    ``use_proxy`` is True (the GitHub Contents fallback), the request is
    routed through the optional ``PLUGINKIT_PROXY`` proxy. Accepted payload
    shapes:

    - ``{"success": true, "data": [...]}`` (hub API),
    - ``{"data": [...]}``,
    - a plain JSON array,
    - the GitHub Contents API response (base64-encoded ``content`` field),
      whose decoded payload is one of the shapes above.

    .. versionadded:: 3.12.0
    """
    req = urllib2.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with _github_urlopen(req, use_proxy=use_proxy) as f:
            resp = json.loads(f.read().decode("utf-8"))
    except Exception:
        return None
    if (
        isinstance(resp, dict)
        and resp.get("encoding") == "base64"
        and resp.get("content")
    ):
        #: GitHub Contents API: decode the base64 file content first
        try:
            decoded = base64.b64decode(resp["content"]).decode("utf-8")
        except Exception:
            return None
        try:
            resp = json.loads(decoded)
        except (TypeError, ValueError):
            return None
    if isinstance(resp, (list, tuple)):
        return resp
    if isinstance(resp, dict) and isinstance(resp.get("data"), (list, tuple)):
        return resp["data"]
    return None


def _list_official_plugins():
    """List plugins collected on the official hub API.

    Returns ``(result, cached)``, where ``result`` is a dict containing the
    total count and a list of plugins fetched from the hub API
    (``https://hub.saintic.com/openservice/flask-pluginkit``). The hub API
    responds with ``{"success": true, "data": [...]}`` and each item carries
    the plugin name plus an optional PyPI package name (``pypi``), the python
    module that can be imported directly (``module``) and a github URL /
    ctime / tag.

    Only plugins with a non-empty ``pypi`` field are queried against the
    PyPI JSON API (``https://pypi.org/pypi/<pypi>/json``) to enrich the
    plugin card with home_page, license, version, docs_url, author, summary
    and requires_python; an empty ``pypi`` field means the plugin is not
    published on PyPI and no request is made. A failing PyPI lookup for a
    single plugin does not abort the whole listing.

    A non-empty ``github`` field is normalized to a full
    ``https://github.com/owner/repo`` URL and also exposed as ``full_name``
    (``owner/repo``), so the web manager can install the plugin from the
    GitHub URL via ``git+https://github.com/<full_name>`` (pip VCS install)
    when it is not published on PyPI. Entries with neither a ``pypi`` nor a
    ``github`` field are skipped: such a plugin cannot be installed at all.

    When the hub API is unreachable or returns an invalid payload, the
    ``awesome/list.json`` file on the official repository via the GitHub
    Contents API
    (``https://api.github.com/repos/staugur/Flask-PluginKit/contents/awesome/list.json``)
    is used as a fallback. When both sources fail, a RuntimeError is raised
    so the caller can report the service as unavailable.

    The result is served from the in-memory cache (8 hours) first, then from
    redis (7 days) when a redis client is detected on ``flask.g``, and only
    falls back to the hub API on a full cache miss. When the API is queried,
    both caches are refreshed.

    The official plugins list is read from the fixed hub URL (see
    :data:`_HUB_API_URL`), which is provided by the author and cannot be
    configured; the fallback request to the GitHub Contents API goes
    through the optional ``PLUGINKIT_PROXY`` proxy.

    .. versionadded:: 3.12.0
    """
    api = _HUB_API_URL
    now = int(time())
    data = _official_plugins_cache.get("data")
    if data and now - _official_plugins_cache["ts"] < _OFFICIAL_CACHE_TTL:
        return data, True
    redis_client = _get_redis_client()
    if redis_client is not None:
        data = _redis_get(redis_client, _OFFICIAL_REDIS_KEY)
        if data:
            _official_plugins_cache.update(ts=now, data=data)
            return data, True
    plugins_data = _fetch_official_plugins(api)
    if plugins_data is None:
        #: hub API unreachable, fall back to the raw list on the repository
        #: (a GitHub API request, routed through the optional proxy)
        plugins_data = _fetch_official_plugins(_HUB_FALLBACK_URL, use_proxy=True)
    if plugins_data is None:
        raise RuntimeError("Official plugins service is unavailable")
    plugins = []
    for item in plugins_data:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        if not name:
            continue
        pypi = (item.get("pypi") or "").strip()
        module = (item.get("module") or "").strip()
        github = _normalize_github_url(item.get("github"))
        if not pypi and not github:
            #: no installable source (PyPI package or GitHub repo), skip
            continue
        plugin = {
            "name": name,
            "pypi": pypi,
            "module": module,
            "github": github,
            "full_name": _github_full_name(github),
            "ctime": item.get("ctime") or "",
            "tag": item.get("tag") or "",
            "version": "",
            "latest_version": "",
            "summary": "",
            "home_page": "",
            "author": "",
            "license": "",
            "docs_url": "",
            "requires_python": "",
            "project_urls": {},
        }
        if pypi:
            #: only plugins published on PyPI carry versioned metadata
            try:
                info = _get_pypi_package_info(pypi)
            except Exception:
                info = None
            if info:
                for field in (
                    "version",
                    "summary",
                    "home_page",
                    "author",
                    "license",
                    "docs_url",
                    "requires_python",
                ):
                    plugin[field] = info.get(field) or ""
                plugin["project_urls"] = info.get("project_urls") or {}
            #: the PyPI version is the latest published version
            plugin["latest_version"] = plugin["version"]
        elif plugin["full_name"]:
            #: no PyPI release, read the latest tag from the GitHub API
            plugin["latest_version"] = _get_latest_release_version(plugin["full_name"])
        plugins.append(plugin)
    result = {"total_count": len(plugins), "plugins": plugins}
    _official_plugins_cache.update(ts=now, data=result)
    if redis_client is not None:
        _redis_set(redis_client, result, _OFFICIAL_REDIS_KEY, _OFFICIAL_REDIS_TTL)
    return result, False


def _pip_name_key(name):
    """Normalize a package name the way pip does (PEP 503).

    Pip normalizes names by lowercasing and collapsing runs of ``-``,
    ``_`` and ``.`` into a single hyphen, so ``Flask_PluginKit.demo`` and
    ``flask-pluginkit-demo`` refer to the same distribution.

    .. versionadded:: 3.12.0
    """
    return re.sub(r"[-_.]+", "-", (name or "").lower()).strip("-")


def _installed_packages_map():
    """Return a ``{normalized_name: version}`` map of installed packages.

    The map is built from ``pip list`` (``utils.pip_list``) honoring the
    ``PLUGINKIT_PIP_TARGET_DIR`` configuration so plugins installed into a
    custom target directory are detected as well. Any failure while running
    pip yields the last known map (or an empty map on the first call)
    instead of aborting the listing.

    The result is cached in memory for ``_INSTALLED_CACHE_TTL`` seconds;
    ``pip list`` spawns a subprocess and is expensive, so the cache keeps
    every listing request fast. Install actions call
    :func:`_invalidate_installed_cache` so a freshly installed plugin is
    detected on the next request rather than after the TTL expires.

    .. versionadded:: 3.12.0
    """
    pip_target_dir = _get_conf("PLUGINKIT_PIP_TARGET_DIR") or ""
    now = int(time())
    if (
        _installed_cache.get("target_dir") == pip_target_dir
        and now - _installed_cache["ts"] < _INSTALLED_CACHE_TTL
    ):
        return _installed_cache["data"]
    try:
        installed = pip_list(target_dir=pip_target_dir)
    except Exception:
        #: keep the last known map on failure instead of aborting the listing
        return _installed_cache.get("data") or {}
    if not isinstance(installed, dict):
        return _installed_cache.get("data") or {}
    result = {_pip_name_key(name): version for name, version in installed.items()}
    _installed_cache.update(ts=now, data=result, target_dir=pip_target_dir)
    return result


def _attach_installed_state(plugins):
    """Attach the installed status to a copy of each plugin dict.

    Each plugin in ``plugins`` is shallow-copied and extended with
    ``installed`` (bool) and ``installed_version`` (str, empty when not
    installed). Matching is done against the PyPI package name (``pypi``),
    the importable python module (``module``) and finally the plugin name
    (``name``), which lets community plugins discovered from the GitHub
    topic be matched by their repository name as well.

    ``upgrade_available`` (bool) is True only when the plugin is installed
    and a newer version exists: for PyPI plugins that is the version fetched
    from the PyPI JSON API, for GitHub-only plugins the latest release tag
    (``latest_version``), compared with ``semver`` semantics.

    The remote plugin list is cached, but the installed status must always
    be fresh, so the cached dicts are never mutated in place.

    .. versionadded:: 3.12.0
    """
    installed = _installed_packages_map()
    enriched = []
    for plugin in plugins:
        item = dict(plugin)
        item["installed"] = False
        item["installed_version"] = ""
        item["upgrade_available"] = False
        if installed:
            for candidate in (
                plugin.get("pypi") or "",
                plugin.get("module") or "",
                plugin.get("name") or "",
            ):
                version = installed.get(_pip_name_key(candidate))
                if version:
                    item["installed"] = True
                    item["installed_version"] = version
                    break
        latest = (item.get("latest_version") or "").strip()
        if (
            item["installed"]
            and latest
            and _version_gt(latest, item["installed_version"])
        ):
            item["upgrade_available"] = True
        enriched.append(item)
    return enriched


def _get_conf(config_name):
    return current_app.config.get(config_name)


def _read_proc_info(pid):
    """Read the cmdline and comm of a process from /proc.

    Returns ``(cmdline, comm)``, both empty strings when the process cannot
    be inspected (e.g. non-Linux platform or missing permissions). This is a
    lightweight psutil-free replacement; Gunicorn and uWSGI run on Linux in
    production, which is the only environment where reloading is allowed.

    .. versionadded:: 3.12.0
    """
    cmdline = comm = ""
    try:
        with open("/proc/{0}/cmdline".format(pid), "rb") as f:
            cmdline = f.read().replace(b"\x00", b" ").decode("utf-8", "ignore").strip()
    except (IOError, OSError):
        pass
    try:
        with open("/proc/{0}/comm".format(pid), "rb") as f:
            comm = f.read().decode("utf-8", "ignore").strip()
    except (IOError, OSError):
        pass
    return cmdline, comm


def _is_gunicorn_master(cmdline, processname):
    """Match the Gunicorn master process title.

    Gunicorn sets its master process title to ``gunicorn: master [<name>]``
    (it shows up in /proc/<pid>/cmdline because setproctitle rewrites argv).
    ``processname`` is the name inside ``[]`` and has no default value, so a
    match requires both a valid master title and the configured name.
    """
    if not processname:
        return False
    if not cmdline:
        return False
    return cmdline.startswith("gunicorn: master [{0}]".format(processname))


def _is_uwsgi_master(cmdline, comm, processname=None):
    """Match the uWSGI master process.

    ``processname`` defaults to ``uwsgi``; the master is matched when the
    process name (comm) equals it or the command line contains it as a
    whole token (the latter also covers ``python -m uwsgi`` style startups).
    Using token-exact matching avoids false positives such as a Gunicorn
    master titled ``gunicorn: master [uwsgi_app:app]`` being mistaken for
    uWSGI merely because the substring ``uwsgi`` appears in its name.
    """
    processname = processname or "uwsgi"
    if comm == processname:
        return True
    if cmdline and processname in cmdline.split():
        return True
    return False


@blueprint.before_request
def pluginkit_webmanager_auth():
    """You must have validation to access this page."""
    authMethod = _get_conf("PLUGINKIT_AUTH_METHOD")
    authAidMethod = _get_conf("PLUGINKIT_AUTH_AID_METHOD")
    authResult = dict(msg="Unverified", code=1, method=authMethod)

    def authTipmsg(authResult, code=403):
        return "%s Authentication failed [%s]: %s [%s]" % (
            code,
            authResult["method"],
            authResult["msg"],
            authResult["code"],
        )

    if authMethod == "BOOL":
        AUTHBOOLFIELD = _get_conf("PLUGINKIT_AUTH_BOOLFIELD") or "signin"
        if getattr(g, AUTHBOOLFIELD, None) is True:
            authResult.update(code=0)

    elif authMethod == "BASIC":
        #: the realm parameter is reserved for defining protection spaces and
        #: it's used by the authentication schemes to indicate a scope of
        #: protection.
        AUTHREALM = (
            _get_conf("PLUGINKIT_AUTH_REALM") or "Flask-PluginKit Login Required"
        )

        #: User and password configuration, format {user:pass, user:pass},
        #: if format error, all authentication failure by default.
        AUTHUSERS = _get_conf("PLUGINKIT_AUTH_USERS")

        def verify_auth(username, password):
            """Check the user and password"""
            if isinstance(AUTHUSERS, dict) and username in AUTHUSERS:
                return password == AUTHUSERS[username]
            return False

        def not_authenticated():
            """Sends a 401 response that enables basic auth"""
            return Response(
                authTipmsg(authResult, 401),
                401,
                {"WWW-Authenticate": 'Basic realm="%s"' % AUTHREALM},
            )

        #: Intercepts authentication and denies access if it fails
        auth = request.authorization
        if not auth or not verify_auth(auth.username, auth.password):
            authResult.update(msg="Invalid username or password")
            return not_authenticated()
        else:
            authResult.update(code=0)

    elif authMethod == "TOKEN":
        AUTHTOKEN = _get_conf("PLUGINKIT_AUTH_TOKENFIELD") or "AccessToken"
        AUTHCHECKTOKEN = _get_conf("PLUGINKIT_AUTH_CHECKTOKEN")
        if AUTHTOKEN and callable(AUTHCHECKTOKEN):
            ak = request.headers.get(AUTHTOKEN)
            if ak and AUTHCHECKTOKEN(ak):
                authResult.update(code=0)

    elif authMethod == "FUNC":
        AUTHFUNC = _get_conf("PLUGINKIT_AUTH_FUNC")
        if callable(AUTHFUNC):
            if AUTHFUNC():
                authResult.update(code=0)

    if authAidMethod == "IP":
        ip = request.headers.get("X-Real-Ip", request.remote_addr)
        BLACKLIST = _get_conf("PLUGINKIT_AUTH_IP_BLACKLIST") or []
        WHITELIST = _get_conf("PLUGINKIT_AUTH_IP_WHITELIST") or []
        if isinstance(BLACKLIST, (list, tuple)) and isinstance(
            WHITELIST, (list, tuple)
        ):
            if ip in WHITELIST and ip not in BLACKLIST:
                authResult.update(code=0)

    if hasattr(current_app, "extensions") and "pluginkit" in current_app.extensions:
        from flask_pluginkit import __version__ as version

        g.pluginkit = current_app.extensions["pluginkit"]
        metadata = OrderedDict()
        metadata["version"] = version
        metadata["plugins_count"] = len(g.pluginkit.get_all_plugins)
        g.pluginkit_metadata = metadata
    else:
        authResult.update(
            code=-1,
            msg="It is not a web application based on Flask-PluginKit.",
        )

    if authResult["code"] != 0:
        return make_response(authTipmsg(authResult)), 403


@blueprint.route("/")
def index():
    #: plugins web manager page
    return render_template("manager.html")


@blueprint.route("/api", methods=["POST"])
def api():
    #: plugin api action
    pm = current_app.extensions["pluginkit"]
    res = dict(msg=None, code=1)
    if hasattr(g, "pluginkit"):
        Action = request.args.get("Action")
        plugin_name = request.args.get("plugin_name")
        if Action == "enablePlugin":
            try:
                g.pluginkit.enable_plugin(plugin_name)
            except Exception as e:
                res.update(msg="enable plugin failed:" + str(e), code=30000)
            else:
                res.update(code=0)
        elif Action == "disablePlugin":
            try:
                g.pluginkit.disable_plugin(plugin_name)
            except Exception as e:
                res.update(msg="disable plugin failed:" + str(e), code=40000)
            else:
                res.update(code=0)
        elif Action == "reloadApp":
            """reload web app
            WSGI:
                Gunicorn, uWSGI
            Required current_app.config:
                ENV='production'
                PLUGINKIT_PROCESSNAME='Real runtime process name'
                - for Gunicorn
                    PLUGINKIT_GUNICORN_ENABLED=True
                - for uWSGI
                    PLUGINKIT_UWSGI_ENABLED=True
            """
            ENV = _get_conf("ENV")
            PROCESSNAME = _get_conf("PLUGINKIT_PROCESSNAME")
            UWSGI_ENABLED = _get_conf("PLUGINKIT_UWSGI_ENABLED")
            GUNICORN_ENABLED = _get_conf("PLUGINKIT_GUNICORN_ENABLED")

            #: get gunicorn or uwsgi masterpid, inspect it via /proc
            pid = os.getppid()
            cmdline, comm = _read_proc_info(pid)

            def reload(pid):
                """reload gunicorn or uwsgi"""
                sleep(3)
                os.kill(pid, signal.SIGHUP)

            if (
                ENV == "production"
                and GUNICORN_ENABLED is True
                and _is_gunicorn_master(cmdline, PROCESSNAME)
            ):
                #: reload gunicorn
                thread.start_new_thread(reload, (pid,))
                res.update(code=0)

            elif (
                ENV == "production"
                and UWSGI_ENABLED is True
                and _is_uwsgi_master(cmdline, comm, PROCESSNAME)
            ):
                #: reload uwsgi
                thread.start_new_thread(reload, (pid,))
                res.update(code=0)

            else:
                res.update(
                    code=20001,
                    msg="According to the rules are not allowed to reload",
                )
        elif Action == "uploadPlugin":
            f = request.files.get("file")
            if f and allowed_uploaded_plugin_suffix(f.filename):
                suffix = "." + secure_filename(f.filename).split(".")[-1]
                with NamedTemporaryFile(
                    mode="w+b", prefix="fpk-web-", suffix=suffix, delete=False
                ) as fp:
                    fp.write(f.stream.read())
                    filename = fp.name
                pi = PluginInstaller(pm.plugins_abspath)
                res = pi.addPlugin(method="local", filepath=filename, remove=True)
                if res["code"] == 0:
                    _invalidate_installed_cache()
            else:
                msg = "Unsuccessfully obtained file or format is not allowed"
                res.update(code=50000, msg=msg)
        elif Action == "downloadPlugin":
            url = request.form.get("url")
            if check_url(url):
                pi = PluginInstaller(pm.plugins_abspath)
                res = pi.addPlugin(method="remote", url=url)
                if res["code"] == 0:
                    _invalidate_installed_cache()
            else:
                res.update(code=60000, msg="Please fill in the correct URL")
        elif Action == "listPlugins":
            #: List plugins discovered from the GitHub topic
            try:
                data, cached = _list_github_topic_plugins()
            except Exception as e:
                res.update(code=70000, msg=str(e))
            else:
                data = dict(data)
                data["cached"] = cached
                data["plugins"] = _attach_installed_state(data["plugins"])
                res.update(code=0, data=data)
        elif Action == "listOfficialPlugins":
            #: List plugins collected on the official hub API
            try:
                data, cached = _list_official_plugins()
            except Exception as e:
                res.update(code=71000, msg=str(e))
            else:
                data = dict(data)
                data["cached"] = cached
                data["plugins"] = _attach_installed_state(data["plugins"])
                res.update(code=0, data=data)
        elif Action == "installPlugin":
            #: Install a plugin discovered from the GitHub topic by
            #: downloading the repository archive of its default branch.
            full_name = request.form.get("full_name")
            default_branch = request.form.get("default_branch")
            if full_name and "/" in full_name and default_branch:
                repo_name = full_name.split("/")[-1]
                url = (
                    "https://codeload.github.com/{0}/zip/refs/heads/{1}"
                    "?plugin_filename={2}.zip".format(
                        full_name, default_branch, repo_name
                    )
                )
                if check_url(url):
                    pi = PluginInstaller(pm.plugins_abspath)
                    res = pi.addPlugin(method="remote", url=url)
                    if res["code"] == 0:
                        _queue.append("Install {} is successful".format(repo_name))
                        _invalidate_installed_cache()
                else:
                    res.update(code=60000, msg="Invalid repository URL")
            else:
                res.update(code=61000, msg="Invalid repository parameter")
        elif Action == "installPackage":
            package_or_url = request.form.get("package_or_url")
            #: pip target directory for persistent third-party plugin installs
            pip_target_dir = _get_conf("PLUGINKIT_PIP_TARGET_DIR") or ""

            def _install(package_or_url):
                pi = PluginInstaller(pm.plugins_abspath)
                resp = pi.addPlugin(
                    method="pip",
                    package_or_url=package_or_url,
                    target_dir=pip_target_dir,
                )
                if resp["code"] == 0:
                    _queue.append("Install is successful")
                    _invalidate_installed_cache()
                else:
                    _queue.append(resp["msg"])

            thread.start_new_thread(_install, (package_or_url,))
            res.update(code=0)
    else:
        res.update(msg="Environment is not effective", code=10000)

    return jsonify(res)


@blueprint.route("/msg")
def msg():
    try:
        msg = _queue.popleft()
    except IndexError:
        msg = ""
    accept = request.headers.get("Accept")
    if accept and "application/json" in accept:
        return jsonify(dict(code=0, msg=msg))
    else:
        # SSE（server-sent events）
        res = make_response("retry: 10000\ndata: %s\n\n" % msg)
        res.headers["Content-Type"] = "text/event-stream"
        res.headers["Cache-Control"] = "no-cache"
        res.headers["Connection"] = "keep-alive"
        return res
