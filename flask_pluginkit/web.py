# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.web
    ~~~~~~~~~~~~~~~~~~~

    web: The server-side plugin management blueprint.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import time
from functools import wraps
from flask import Blueprint, current_app, g, request, jsonify, render_template, make_response, Response
from .utils import PY2

if PY2:
    import thread
else:
    import _thread as thread

#: Blueprint instance for managing plugins
#:
#: .. versionadded:: 0.1.6
blueprint = Blueprint('flask_pluginkit', __name__, template_folder='templates')


@blueprint.before_request
def pluginkit_beforerequest():
    """blueprint access auth"""
    authMethod = current_app.config.get("PLUGINKIT_AUTHMETHOD")
    authResult = dict(msg=None, code=1, method=authMethod)

    def authTipmsg(authResult, code=403):
        """make response message"""
        return "%s Authentication failed [%s]: %s [%s]" % (code, authResult["method"], authResult["msg"], authResult["code"])

    if authMethod == "BOOL":
        """Boolean Auth"""
        if hasattr(g, "signin") and g.signin is True:
            authResult.update(code=0)
        else:
            authResult.update(code=10000, msg="Invalid authentication field")
    elif authMethod == "BASIC":
        """HTTP Basic Auth"""

        #: the realm parameter is reserved for defining protection spaces and
        #: it's used by the authentication schemes to indicate a scope of protection.
        #:
        #: .. versionadded:: 1.2.0
        authRealm = current_app.config.get("PLUGINKIT_AUTHREALM") or "Flask-PluginKit Login Required"

        #: User and password configuration, format {user:pass, user:pass},
        #: if format error, all authentication failure by default.
        #:
        #: .. versionadded:: 1.2.0
        authUsers = current_app.config.get("PLUGINKIT_AUTHUSERS")

        def verify_auth(username, password):
            """Check the user and password"""
            if isinstance(authUsers, dict) and username in authUsers:
                return password == authUsers[username]
            return False

        def not_authenticated():
            """Sends a 401 response that enables basic auth"""
            return Response(authTipmsg(authResult, 401), 401,
                            {'WWW-Authenticate': 'Basic realm="%s"' % authRealm})

        #: Intercepts authentication and denies access if it fails
        auth = request.authorization
        if not auth or not verify_auth(auth.username, auth.password):
            authResult.update(code=10001, msg="Invalid username or password")
            return not_authenticated()
        else:
            authResult.update(code=0)
    else:
        authResult.update(code=0, msg="No authentication required", method=None)

    #: return response if code != 0
    if authResult["code"] != 0:
        return make_response(authTipmsg(authResult)), 403

    #: get all plugins based flask-pluginkit
    if hasattr(current_app, "extensions") and "pluginkit" in current_app.extensions:
        g.plugin_manager = current_app.extensions["pluginkit"]
        g.plugins = g.plugin_manager.get_all_plugins


@blueprint.route("/")
def index():
    #: plugins web manager page
    return render_template("manager.html")


@blueprint.route("/api", methods=["POST"])
def api():
    #: plugin api action
    res = dict(msg=None, code=1)
    if hasattr(g, "plugin_manager"):
        Action = request.args.get("Action")
        plugin_name = request.args.get("plugin_name")
        if Action == "enablePlugin":
            try:
                g.plugin_manager.enable_plugin(plugin_name)
            except Exception as e:
                res.update(msg="enable plugin failed:" + str(e), code=30000)
            else:
                res.update(code=0)
        elif Action == "disablePlugin":
            try:
                g.plugin_manager.disable_plugin(plugin_name)
            except Exception as e:
                res.update(msg="disable plugin failed:" + str(e), code=40000)
            else:
                res.update(code=0)
        elif Action == "reloadApp":
            """reload web app
            environment:
                Currently only support overloading using gunicorn applications
            requirement:
                App Config, ENV=False GUNICORN_ENABLED=True GUNICORN_PROCESSNAME=Real runtime process name
            """
            try:
                import os
                import signal
                import psutil
            except ImportError:
                res.update(msg="No dependent modules installed", code=20000)
            else:
                #: gunicorn app config
                ENV = current_app.config.get("ENV")
                GUNICORN_ENABLED = current_app.config.get("PLUGINKIT_GUNICORN_ENABLED")
                GUNICORN_PROCESSNAME = current_app.config.get("PLUGINKIT_GUNICORN_PROCESSNAME")

                #: support uwsgi reloading process, don't need to set up process name,
                #: the default name is uwsgi cannot be modified
                #:
                #: .. versionadded:: 1.0.2
                UWSGI_ENABLED = current_app.config.get("PLUGINKIT_UWSGI_ENABLED")

                #: gunicorn or uwsgi masterpid
                pid = os.getppid()
                p = psutil.Process(pid)

                def reload(pid):
                    """reload gunicorn or uwsgi
                    .. versionadded:: 1.0.2
                    """
                    time.sleep(3)
                    os.kill(pid, signal.SIGHUP)

                if ENV == "production" and GUNICORN_ENABLED is True and GUNICORN_PROCESSNAME == p.name():
                    #: reload gunicorn
                    thread.start_new_thread(reload, (pid, ))
                    res.update(code=0)
                elif ENV == "production" and UWSGI_ENABLED is True and "uwsgi" == p.name():
                    #: reload uwsgi
                    thread.start_new_thread(reload, (pid, ))
                    res.update(code=0)
                else:
                    res.update(msg="According to the rules are not allowed to restart", code=20001)
    else:
        res.update(msg="Environment is not effective", code=10000)
    return jsonify(res)
