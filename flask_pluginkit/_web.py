# -*- coding: utf-8 -*-
"""
    flask_pluginkit._web
    ~~~~~~~~~~~~~~~~~~~~

    The server-side plugin management blueprint.

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

import _thread as thread
from time import sleep
from collections import OrderedDict, deque
from werkzeug.utils import secure_filename
from tempfile import NamedTemporaryFile
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
from .utils import allowed_uploaded_plugin_suffix, check_url
from ._installer import PluginInstaller


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


def _get_conf(config_name):
    return current_app.config.get(config_name)


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
            try:
                import os
                import signal
                import psutil
            except ImportError:
                res.update(code=20000, msg="No dependent modules(psutil) installed")
            else:
                ENV = _get_conf("ENV")
                PROCESSNAME = _get_conf("PLUGINKIT_PROCESSNAME")
                UWSGI_ENABLED = _get_conf("PLUGINKIT_UWSGI_ENABLED")
                GUNICORN_ENABLED = _get_conf("PLUGINKIT_GUNICORN_ENABLED")

                #: get gunicorn or uwsgi masterpid
                pid = os.getppid()
                p = psutil.Process(pid)

                def reload(pid):
                    """reload gunicorn or uwsgi"""
                    sleep(3)
                    os.kill(pid, signal.SIGHUP)

                if (
                    ENV == "production"
                    and GUNICORN_ENABLED is True
                    and p.name() == "gunicorn: master [%s]" % PROCESSNAME
                ):
                    #: reload gunicorn
                    thread.start_new_thread(reload, (pid,))
                    res.update(code=0)

                elif (
                    ENV == "production"
                    and UWSGI_ENABLED is True
                    and p.name() == (PROCESSNAME or "uwsgi")
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
            else:
                msg = "Unsuccessfully obtained file or format is not allowed"
                res.update(code=50000, msg=msg)
        elif Action == "downloadPlugin":
            url = request.form.get("url")
            if check_url(url):
                pi = PluginInstaller(pm.plugins_abspath)
                res = pi.addPlugin(method="remote", url=url)
            else:
                res.update(code=60000, msg="Please fill in the correct URL")
        elif Action == "installPackage":
            package_or_url = request.form.get("package_or_url")

            def _install(package_or_url):
                pi = PluginInstaller(pm.plugins_abspath)
                resp = pi.addPlugin(method="pip", package_or_url=package_or_url)
                if resp["code"] == 0:
                    _queue.append("Install is successful")
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
