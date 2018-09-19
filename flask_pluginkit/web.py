# -*- coding: utf-8 -*-
"""
    Flask-PluginKit
    ~~~~~~~~~~~~~~

    blueprint: Web server-side plugin management.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

from flask import Blueprint, current_app, g, request, jsonify, render_template

blueprint = Blueprint('flask_pluginkit', __name__, template_folder='templates')

@blueprint.before_request
def get_plugins():
    # get all plugins based flask-pluginkit
    if hasattr(current_app, "plugin_manager"):
        g.plugin_manager = current_app.plugin_manager
        g.plugins = g.plugin_manager.get_all_plugins

@blueprint.route("/")
def index():
    # plugins web manager page
    return render_template("manager.html")

@blueprint.route("/api", methods=["POST"])
def api():
    # plugin api action
    res = dict(msg=None, code=1)
    if hasattr(g, "plugin_manager"):
        Action = request.args.get("Action")
        plugin_name = request.args.get("plugin_name")
        if Action == "enablePlugin":
            try:
                g.plugin_manager.enable_plugin(plugin_name)
            except Exception,e:
                res.update(msg="enable plugin failed:" + str(e), code=30000)
            else:
                res.update(code=0)
        elif Action == "disablePlugin":
            try:
                g.plugin_manager.disable_plugin(plugin_name)
            except Exception,e:
                res.update(msg="disable plugin failed:" + str(e), code=40000)
            else:
                res.update(code=0)
        elif Action == "reloadApp":
            """reload web app
            environment:
                Currently only support overloading using gunicorn applications
            requirement:
                App Config, DEBUG=False GUNICORN_ENABLED=True GUNICORN_PROCESSNAME=Real runtime process name
            """
            try:
                import os, signal, psutil
            except ImportError:
                res.update(msg="No dependent modules installed", code=20000)
            else:
                # gunicorn app config
                DEBUG = current_app.config.get("DEBUG")
                GUNICORN_ENABLED = current_app.config.get("GUNICORN_ENABLED")
                GUNICORN_PROCESSNAME = current_app.config.get("GUNICORN_PROCESSNAME")
                # gunicorn masterpid
                pid = os.getppid()
                p = psutil.Process(pid)
                if DEBUG == False and GUNICORN_ENABLED == True and GUNICORN_PROCESSNAME == p.name():
                    # reload gunicorn
                    os.kill(pid, signal.SIGHUP)
                    res.update(code=0)
                else:
                    res.update(msg="According to the rules are not allowed to restart", code=20001)
    else:
        res.update(msg="Environment is not effective", code=10000)
    return jsonify(res)
