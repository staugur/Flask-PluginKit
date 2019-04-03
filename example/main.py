# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.example.main
    ~~~~~~~~~~~~~~

    Entrance

    Docstring conventions:
    http://flask.pocoo.org/docs/0.10/styleguide/#docstrings

    Comments:
    http://flask.pocoo.org/docs/0.10/styleguide/#comments

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

from flask import g, render_template, render_template_string
from flask_pluginkit import Flask, PluginManager, blueprint, push_dcp

__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__doc__ = 'An example for Flask-PluginKit'


# 初始化定义application
app = Flask(__name__)
#app.config["PLUGINKIT_AUTHMETHOD"] = "BOOL"
app.config["PLUGINKIT_AUTHMETHOD"] = "BASIC"
app.config["PLUGINKIT_AUTHREALM"] = "Flask-PluginKit Welcome"
app.config["PLUGINKIT_AUTHUSERS"] = dict(admin="admin")

# 初始化插件管理器(自动扫描并加载运行)
plugin = PluginManager(app, s3="local", plugin_packages=["flask_pluginkit_demo"])

# 注册flask-pluginkit的蓝图
app.register_blueprint(blueprint, url_prefix="/PluginManager")


@app.before_request_top
def br():
    g.signin = True
    print(app.url_map)


@app.route("/")
def index():
    def set_dcp():
        return render_template_string("<p><a href=\"{{ url_for('index') }}\">dcp return</a></p>")
    push_dcp('example', set_dcp)
    app.logger.info(app.static_folder)
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)
