# -*- coding: utf-8 -*-

import base64
import json
import os
import signal
import unittest
from io import BytesIO
from unittest import mock

from flask import Flask, g

import flask_pluginkit._web as _web
from flask_pluginkit import PluginManager, blueprint


class FakeRedis(object):
    """Minimal fake redis client implementing get/setex."""

    def __init__(self, data=None):
        self.data = data or {}
        self.setex_calls = []

    def get(self, name):
        return self.data.get(name)

    def setex(self, name, time, value):
        self.setex_calls.append((name, time, value))
        self.data[name] = value


class OfficialPluginsTest(unittest.TestCase):
    def setUp(self):
        _web._official_plugins_cache.update(ts=0, data=None)
        self.app = Flask("official-test")
        self.app.config.update(
            TESTING=True,
            PLUGINKIT_TEST=True,
            PLUGINKIT_AUTH_METHOD="FUNC",
            PLUGINKIT_AUTH_FUNC=lambda: True,
        )
        PluginManager(self.app)
        self.app.register_blueprint(blueprint)
        self.client = self.app.test_client()

    def _fake_hub_response(self):
        return BytesIO(
            json.dumps(
                {
                    "success": True,
                    "data": [
                        {
                            "name": "Demo Plugin",
                            "pypi": "flask-pluginkit-demo",
                            "github": "staugur/flask-pluginkit-demo",
                            "ctime": "2026-01-01",
                            "tag": "demo",
                        },
                        {
                            "name": "Not On PyPI",
                            "pypi": "",
                            "github": "https://github.com/staugur/flask-pluginkit-not-on-pypi",
                            "ctime": "2026-02-01",
                            "tag": "",
                        },
                        {"name": "", "pypi": "", "github": ""},
                        "not-a-dict",
                    ],
                }
            ).encode("utf-8")
        )

    def _fake_github_contents_response(self):
        """Fake a GitHub Contents API response for awesome/list.json."""
        payload = [
            {
                "name": "Demo Plugin",
                "pypi": "flask-pluginkit-demo",
                "github": "staugur/flask-pluginkit-demo",
                "ctime": "2026-01-01",
                "tag": "demo",
            },
            {
                "name": "Not On PyPI",
                "pypi": "",
                "github": "https://github.com/staugur/flask-pluginkit-not-on-pypi",
                "ctime": "2026-02-01",
                "tag": "",
            },
        ]
        content = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        return BytesIO(
            json.dumps(
                {
                    "name": "list.json",
                    "path": "awesome/list.json",
                    "content": content,
                    "encoding": "base64",
                }
            ).encode("utf-8")
        )

    def _fake_pypi_response(self):
        return BytesIO(
            json.dumps(
                {
                    "info": {
                        "name": "flask-pluginkit-demo",
                        "version": "0.1.0",
                        "summary": "A demo plugin",
                        "home_page": "https://example.com/demo",
                        "author": "staugur",
                        "license": "BSD-3-Clause",
                        "docs_url": "https://example.com/docs",
                        "requires_python": ">=3.8",
                    },
                    "releases": {},
                    "urls": [],
                }
            ).encode("utf-8")
        )

    def test_list_official_plugins(self):
        hub = self._fake_hub_response()
        pypi = self._fake_pypi_response()
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [hub, pypi]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total_count"], 2)
        self.assertFalse(data["data"]["cached"])
        plugin = data["data"]["plugins"][0]
        self.assertEqual(plugin["name"], "Demo Plugin")
        self.assertEqual(plugin["pypi"], "flask-pluginkit-demo")
        self.assertEqual(
            plugin["github"], "https://github.com/staugur/flask-pluginkit-demo"
        )
        self.assertEqual(plugin["ctime"], "2026-01-01")
        self.assertEqual(plugin["tag"], "demo")
        self.assertEqual(plugin["full_name"], "staugur/flask-pluginkit-demo")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertEqual(plugin["license"], "BSD-3-Clause")
        self.assertEqual(plugin["home_page"], "https://example.com/demo")
        self.assertEqual(plugin["docs_url"], "https://example.com/docs")
        self.assertEqual(plugin["author"], "staugur")

    def test_list_official_plugins_empty_pypi(self):
        """An empty pypi field means not published on PyPI, no request made."""
        hub = self._fake_hub_response()
        pypi = self._fake_pypi_response()
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [hub, pypi]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        plugin = data["data"]["plugins"][1]
        self.assertEqual(plugin["name"], "Not On PyPI")
        self.assertEqual(plugin["pypi"], "")
        self.assertEqual(plugin["version"], "")
        self.assertEqual(plugin["home_page"], "")
        #: hub request + pypi lookup for the first plugin only
        self.assertEqual(m.call_count, 2)

    def test_list_official_plugins_all_empty_pypi(self):
        """No pypi field anywhere skips the PyPI API entirely."""
        hub = BytesIO(
            json.dumps(
                {
                    "success": True,
                    "data": [
                        {
                            "name": "Git Only Plugin",
                            "pypi": "",
                            "github": "staugur/git-only",
                        }
                    ],
                }
            ).encode("utf-8")
        )
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [hub]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total_count"], 1)
        plugin = data["data"]["plugins"][0]
        self.assertEqual(plugin["name"], "Git Only Plugin")
        self.assertEqual(plugin["pypi"], "")
        self.assertEqual(plugin["version"], "")
        #: only the hub request, no PyPI API call at all
        self.assertEqual(m.call_count, 1)

    def test_list_official_plugins_full_name_from_github(self):
        """A github field allows installing from the GitHub URL.

        full_name is the ``owner/repo`` identifier extracted from either a
        full GitHub URL or a bare ``owner/repo`` string, used by the web
        manager to build the ``git+https://github.com/<full_name>`` URL.
        """
        hub = BytesIO(
            json.dumps(
                {
                    "success": True,
                    "data": [
                        {
                            "name": "Git Only Plugin",
                            "pypi": "",
                            "github": "staugur/git-only",
                        },
                        {
                            "name": "Full URL Plugin",
                            "pypi": "",
                            "github": "https://github.com/staugur/full-url",
                        },
                        {
                            "name": "No Source Plugin",
                            "pypi": "",
                            "github": "",
                        },
                    ],
                }
            ).encode("utf-8")
        )
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [hub]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        plugins = {p["name"]: p for p in data["data"]["plugins"]}
        self.assertEqual(
            plugins["Git Only Plugin"]["github"],
            "https://github.com/staugur/git-only",
        )
        self.assertEqual(plugins["Git Only Plugin"]["full_name"], "staugur/git-only")
        self.assertEqual(
            plugins["Full URL Plugin"]["github"],
            "https://github.com/staugur/full-url",
        )
        self.assertEqual(plugins["Full URL Plugin"]["full_name"], "staugur/full-url")
        #: neither a PyPI package nor a GitHub repo, the entry is skipped
        self.assertEqual(data["data"]["total_count"], 2)
        self.assertNotIn("No Source Plugin", plugins)

    def test_list_official_plugins_pypi_miss(self):
        """A pypi 404 for one plugin must not abort the whole listing."""
        hub = self._fake_hub_response()
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [
                hub,
                _web.urllib2.HTTPError(
                    "https://pypi.org/pypi/flask-pluginkit-demo/json",
                    404,
                    "Not Found",
                    None,
                    None,
                ),
            ]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        plugin = data["data"]["plugins"][0]
        self.assertEqual(plugin["name"], "Demo Plugin")
        self.assertEqual(plugin["pypi"], "flask-pluginkit-demo")
        self.assertEqual(plugin["version"], "")

    def test_list_official_plugins_fallback(self):
        """A failing hub API falls back to the GitHub Contents API."""
        fallback = self._fake_github_contents_response()
        pypi = self._fake_pypi_response()
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [
                _web.urllib2.HTTPError(
                    "https://hub.saintic.com/openservice/flask-pluginkit",
                    404,
                    "Not Found",
                    None,
                    None,
                ),
                fallback,
                pypi,
            ]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total_count"], 2)
        self.assertEqual(data["data"]["plugins"][0]["name"], "Demo Plugin")
        self.assertEqual(data["data"]["plugins"][0]["pypi"], "flask-pluginkit-demo")

    def test_list_official_plugins_real_list_file(self):
        """The real awesome/list.json (name + github only, no pypi/ctime/tag)
        must be compatible: missing optional fields default to empty strings
        and no PyPI request is made without a pypi field.
        """
        list_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "awesome",
            "list.json",
        )
        with open(list_file, "rb") as fh:
            payload = json.loads(fh.read().decode("utf-8"))
        content = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        fallback = BytesIO(
            json.dumps(
                {
                    "name": "list.json",
                    "path": "awesome/list.json",
                    "content": content,
                    "encoding": "base64",
                }
            ).encode("utf-8")
        )
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [
                _web.urllib2.HTTPError(
                    "https://hub.saintic.com/openservice/flask-pluginkit",
                    404,
                    "Not Found",
                    None,
                    None,
                ),
                fallback,
            ]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total_count"], 1)
        plugin = data["data"]["plugins"][0]
        self.assertEqual(plugin["name"], "flask-pluginkit-demo")
        self.assertEqual(plugin["pypi"], "")
        self.assertEqual(
            plugin["github"], "https://github.com/saintic/flask-pluginkit-demo"
        )
        self.assertEqual(plugin["full_name"], "saintic/flask-pluginkit-demo")
        self.assertEqual(plugin["ctime"], "")
        self.assertEqual(plugin["tag"], "")
        #: hub 404 + fallback only, no PyPI request without a pypi field
        self.assertEqual(m.call_count, 2)

    def test_list_official_plugins_hub_invalid_fallback_ok(self):
        """An invalid hub payload is treated as unreachable and falls back."""
        invalid = BytesIO(json.dumps({"success": False}).encode("utf-8"))
        fallback = self._fake_github_contents_response()
        pypi = self._fake_pypi_response()
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [invalid, fallback, pypi]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total_count"], 2)

    def test_list_official_plugins_both_unavailable(self):
        """Hub and fallback both failing reports the service as unavailable."""
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [
                _web.urllib2.HTTPError(
                    "https://hub.saintic.com/openservice/flask-pluginkit",
                    404,
                    "Not Found",
                    None,
                    None,
                ),
                _web.urllib2.HTTPError(
                    "https://api.github.com/repos/staugur/Flask-PluginKit/contents/awesome/list.json",
                    500,
                    "Internal Server Error",
                    None,
                    None,
                ),
            ]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 71000)
        self.assertIn("unavailable", data["msg"])

    def test_list_official_plugins_cached(self):
        hub = self._fake_hub_response()
        pypi = self._fake_pypi_response()
        with mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [hub, pypi]
            self.client.post("/api?Action=listOfficialPlugins")
            count = m.call_count
            rv = self.client.post("/api?Action=listOfficialPlugins")
            self.assertEqual(m.call_count, count)
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertTrue(data["data"]["cached"])

    def test_list_official_plugins_redis_write(self):
        fake_redis = FakeRedis()
        hub = self._fake_hub_response()
        pypi = self._fake_pypi_response()
        with mock.patch(
            "flask_pluginkit._web._get_redis_client", return_value=fake_redis
        ), mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            m.side_effect = [hub, pypi]
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(len(fake_redis.setex_calls), 1)
        name, ttl, value = fake_redis.setex_calls[0]
        self.assertEqual(name, _web._OFFICIAL_REDIS_KEY)
        self.assertEqual(ttl, _web._OFFICIAL_REDIS_TTL)

    def test_list_official_plugins_redis_hit(self):
        fake_redis = FakeRedis(
            {
                _web._OFFICIAL_REDIS_KEY: json.dumps(
                    {"total_count": 1, "plugins": [{"name": "flask-pluginkit-demo"}]}
                )
            }
        )
        with mock.patch(
            "flask_pluginkit._web._get_redis_client", return_value=fake_redis
        ), mock.patch("flask_pluginkit._web.urllib2.urlopen") as m:
            rv = self.client.post("/api?Action=listOfficialPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertTrue(data["data"]["cached"])
        self.assertEqual(m.call_count, 0)


class GithubTopicPluginsTest(unittest.TestCase):
    def setUp(self):
        #: clear the module-level cache so every test really hits the API
        _web._github_topic_cache.update(ts=0, data=None)
        self.app = Flask("web-test")
        self.app.config.update(
            TESTING=True,
            PLUGINKIT_TEST=True,
            PLUGINKIT_AUTH_METHOD="FUNC",
            PLUGINKIT_AUTH_FUNC=lambda: True,
        )
        PluginManager(self.app)
        self.app.register_blueprint(blueprint)
        self.client = self.app.test_client()

    def _fake_api_response(self):
        return json.dumps(
            {
                "total_count": 3,
                "items": [
                    {
                        "name": "flask-pluginkit-demo",
                        "full_name": "staugur/flask-pluginkit-demo",
                        "description": "A demo plugin",
                        "html_url": "https://github.com/staugur/flask-pluginkit-demo",
                        "homepage": "",
                        "stargazers_count": 10,
                        "forks_count": 2,
                        "language": "Python",
                        "license": {"spdx_id": "BSD-3-Clause"},
                        "default_branch": "master",
                        "updated_at": "2026-01-01T00:00:00Z",
                        "archived": True,
                    },
                    {
                        "name": "unrelated-plugin",
                        "full_name": "staugur/unrelated-plugin",
                        "description": "Not a flask-pluginkit plugin",
                        "html_url": "https://github.com/staugur/unrelated-plugin",
                        "homepage": "",
                        "stargazers_count": 99,
                        "forks_count": 9,
                        "language": "Go",
                        "license": {"spdx_id": "MIT"},
                        "default_branch": "main",
                        "updated_at": "2026-06-01T00:00:00Z",
                        "archived": False,
                    },
                    {
                        "name": "flask_pluginkit_lib",
                        "full_name": "staugur/flask_pluginkit_lib",
                        "description": "A lower-stars plugin",
                        "html_url": "https://github.com/staugur/flask_pluginkit_lib",
                        "homepage": "",
                        "stargazers_count": 5,
                        "forks_count": 0,
                        "language": "Python",
                        "license": {"spdx_id": "MIT"},
                        "default_branch": "main",
                        "updated_at": "2026-05-01T00:00:00Z",
                        "archived": False,
                    },
                ],
            }
        ).encode("utf-8")

    def _fake_result(self):
        return {
            "topic": _web._GITHUB_TOPIC,
            "total_count": 1,
            "plugins": [
                {
                    "name": "flask-pluginkit-demo",
                    "full_name": "staugur/flask-pluginkit-demo",
                    "description": "A demo plugin",
                    "url": "https://github.com/staugur/flask-pluginkit-demo",
                    "homepage": "",
                    "stars": 10,
                    "forks": 2,
                    "language": "Python",
                    "license": "BSD-3-Clause",
                    "default_branch": "master",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "archived": False,
                }
            ],
        }

    def test_list_plugins(self):
        resp = BytesIO(self._fake_api_response())
        with mock.patch("flask_pluginkit._web.urllib2.urlopen", return_value=resp):
            rv = self.client.post("/api?Action=listPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        #: only repositories matching the name prefixes are kept
        self.assertEqual(data["data"]["total_count"], 2)
        self.assertEqual(len(data["data"]["plugins"]), 2)
        self.assertEqual(data["data"]["topic"], "flask-pluginkit")
        self.assertFalse(data["data"]["cached"])
        #: sorted by stars descending
        self.assertEqual(
            [p["stars"] for p in data["data"]["plugins"]], [10, 5]
        )
        plugin = data["data"]["plugins"][0]
        self.assertEqual(plugin["full_name"], "staugur/flask-pluginkit-demo")
        self.assertEqual(plugin["stars"], 10)
        self.assertEqual(plugin["license"], "BSD-3-Clause")
        self.assertTrue(plugin["archived"])
        #: the underscore-prefixed repo is also collected
        self.assertEqual(
            data["data"]["plugins"][1]["full_name"], "staugur/flask_pluginkit_lib"
        )

    def test_list_plugins_cached(self):
        resp = BytesIO(self._fake_api_response())
        with mock.patch("flask_pluginkit._web.urllib2.urlopen", return_value=resp) as m:
            self.client.post("/api?Action=listPlugins")
            rv = self.client.post("/api?Action=listPlugins")
        data = rv.get_json()
        self.assertEqual(m.call_count, 1)
        self.assertEqual(data["code"], 0)
        self.assertTrue(data["data"]["cached"])

    def test_list_plugins_error(self):
        with mock.patch(
            "flask_pluginkit._web.urllib2.urlopen",
            side_effect=Exception("network unreachable"),
        ):
            rv = self.client.post("/api?Action=listPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 70000)
        self.assertIn("network unreachable", data["msg"])

    def test_list_plugins_redis_write(self):
        """A redis client on flask.g receives the result with a 7-day TTL."""
        fake_redis = FakeRedis()
        resp = BytesIO(self._fake_api_response())
        with mock.patch(
            "flask_pluginkit._web._get_redis_client", return_value=fake_redis
        ), mock.patch(
            "flask_pluginkit._web.urllib2.urlopen", return_value=resp
        ):
            rv = self.client.post("/api?Action=listPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(len(fake_redis.setex_calls), 1)
        name, ttl, value = fake_redis.setex_calls[0]
        self.assertEqual(name, _web._GITHUB_TOPIC_REDIS_KEY)
        self.assertEqual(ttl, _web._GITHUB_TOPIC_REDIS_TTL)
        self.assertEqual(json.loads(value)["total_count"], 2)

    def test_list_plugins_redis_hit(self):
        """A redis hit skips the GitHub API entirely."""
        fake_redis = FakeRedis(
            {_web._GITHUB_TOPIC_REDIS_KEY: json.dumps(self._fake_result())}
        )
        with mock.patch(
            "flask_pluginkit._web._get_redis_client", return_value=fake_redis
        ), mock.patch(
            "flask_pluginkit._web.urllib2.urlopen"
        ) as m:
            rv = self.client.post("/api?Action=listPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertTrue(data["data"]["cached"])
        self.assertEqual(m.call_count, 0)

    def test_list_plugins_redis_errors_ignored(self):
        """Redis failures must not block the API list."""
        class BrokenRedis(object):
            def get(self, name):
                raise Exception("redis down")

            def setex(self, name, time, value):
                raise Exception("redis down")

        resp = BytesIO(self._fake_api_response())
        with mock.patch(
            "flask_pluginkit._web._get_redis_client", return_value=BrokenRedis()
        ), mock.patch(
            "flask_pluginkit._web.urllib2.urlopen", return_value=resp
        ):
            rv = self.client.post("/api?Action=listPlugins")
        data = rv.get_json()
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["total_count"], 2)

    def test_get_redis_client_detects_g_redis(self):
        fake_redis = FakeRedis()
        with self.app.test_request_context("/api?Action=listPlugins"):
            g.redis = fake_redis
            self.assertIs(_web._get_redis_client(), fake_redis)

    def test_get_redis_client_detects_g_redis_client(self):
        fake_redis = FakeRedis()
        with self.app.test_request_context("/api?Action=listPlugins"):
            g.redis_client = fake_redis
            self.assertIs(_web._get_redis_client(), fake_redis)

    def test_get_redis_client_returns_none_without_redis(self):
        with self.app.test_request_context("/api?Action=listPlugins"):
            self.assertIsNone(_web._get_redis_client())

    def test_install_plugin_invalid(self):
        rv = self.client.post("/api?Action=installPlugin")
        data = rv.get_json()
        self.assertEqual(data["code"], 61000)

        rv = self.client.post(
            "/api?Action=installPlugin", data={"full_name": "staugur/flask-pluginkit-demo"}
        )
        data = rv.get_json()
        self.assertEqual(data["code"], 61000)


class ReloadAppTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask("reload-test")
        self.app.config.update(
            TESTING=True,
            PLUGINKIT_TEST=True,
            PLUGINKIT_AUTH_METHOD="FUNC",
            PLUGINKIT_AUTH_FUNC=lambda: True,
            ENV="production",
            PLUGINKIT_GUNICORN_ENABLED=True,
            PLUGINKIT_PROCESSNAME="app:app",
        )
        PluginManager(self.app)
        self.app.register_blueprint(blueprint)
        self.client = self.app.test_client()

    def test_is_gunicorn_master(self):
        self.assertTrue(
            _web._is_gunicorn_master("gunicorn: master [app:app]", "app:app")
        )
        self.assertFalse(
            _web._is_gunicorn_master("gunicorn: master [other]", "app:app")
        )
        self.assertFalse(_web._is_gunicorn_master("", "app:app"))
        #: processname has no default value, missing config never matches
        self.assertFalse(
            _web._is_gunicorn_master("gunicorn: master [app:app]", None)
        )

    def test_is_uwsgi_master(self):
        #: default processname is uwsgi, matched via comm or cmdline
        self.assertTrue(_web._is_uwsgi_master("", "uwsgi"))
        self.assertTrue(_web._is_uwsgi_master("uwsgi --ini app.ini", ""))
        self.assertTrue(_web._is_uwsgi_master("python -m uwsgi --ini app.ini", ""))
        self.assertFalse(_web._is_uwsgi_master("", "other"))
        self.assertFalse(_web._is_uwsgi_master("", ""))
        #: substring of a token must not match (e.g. gunicorn master named
        #: ``uwsgi_app:app`` must not be mistaken for uWSGI)
        self.assertFalse(
            _web._is_uwsgi_master("gunicorn: master [uwsgi_app:app]", "gunicorn")
        )
        self.assertFalse(
            _web._is_uwsgi_master("gunicorn: master [my-uwsgi]", "gunicorn")
        )
        #: a configured custom processname
        self.assertTrue(_web._is_uwsgi_master("", "custom-name", "custom-name"))

    def test_read_proc_info(self):
        m1 = mock.mock_open(read_data=b"gunicorn: master [app:app]\x00\x00\x00")
        m2 = mock.mock_open(read_data=b"gunicorn")

        def fake_open(path, *args, **kwargs):
            if b"cmdline" in str(path).encode():
                return m1()
            return m2()

        with mock.patch("builtins.open", side_effect=fake_open):
            cmdline, comm = _web._read_proc_info(999)
        self.assertEqual(cmdline, "gunicorn: master [app:app]")
        self.assertEqual(comm, "gunicorn")

    def test_read_proc_info_unreadable(self):
        with mock.patch("builtins.open", side_effect=IOError("no such process")):
            cmdline, comm = _web._read_proc_info(999)
        self.assertEqual(cmdline, "")
        self.assertEqual(comm, "")

    def test_reload_app_rejected_when_proc_unreadable(self):
        #: no /proc or no permission -> refuse to reload
        with mock.patch("flask_pluginkit._web._read_proc_info", return_value=("", "")):
            rv = self.client.post("/api?Action=reloadApp")
        data = rv.get_json()
        self.assertEqual(data["code"], 20001)

    def test_reload_app_rejected_when_name_mismatch(self):
        #: master title exists but does not match the configured processname
        with mock.patch(
            "flask_pluginkit._web._read_proc_info",
            return_value=("gunicorn: master [other]", "gunicorn"),
        ):
            rv = self.client.post("/api?Action=reloadApp")
        data = rv.get_json()
        self.assertEqual(data["code"], 20001)

    def test_reload_app_sends_sighup_to_master(self):
        #: gunicorn master matched -> schedule SIGHUP on the parent pid
        with mock.patch(
            "flask_pluginkit._web._read_proc_info",
            return_value=("gunicorn: master [app:app]", "gunicorn"),
        ), mock.patch("flask_pluginkit._web.os.kill") as kill, mock.patch(
            "flask_pluginkit._web.thread.start_new_thread"
        ) as start_thread, mock.patch("flask_pluginkit._web.sleep"):
            rv = self.client.post("/api?Action=reloadApp")
            data = rv.get_json()
            self.assertEqual(data["code"], 0)
            start_thread.assert_called_once()
            reload_fn, reload_args = start_thread.call_args[0]
            self.assertEqual(len(reload_args), 1)
            #: the master pid must be the parent pid passed as an int
            self.assertIsInstance(reload_args[0], int)
            #: executing the scheduled reload sends SIGHUP to the master
            reload_fn(*reload_args)
            kill.assert_called_once_with(reload_args[0], signal.SIGHUP)


if __name__ == "__main__":
    unittest.main()
