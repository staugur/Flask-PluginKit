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

from flask import g, render_template
from flask_pluginkit import PluginManager, blueprint
from flask_multistatic import MultiStaticFlask as Flask

__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__doc__ = 'An example for Flask-PluginKit'


# 初始化定义application
app = Flask(__name__)
app.config["PLUGINKIT_AUTHMETHOD"] = "BOOL"

# 初始化插件管理器(自动扫描并加载运行)
plugin = PluginManager(app)

# 注册flask-pluginkit的蓝图
app.register_blueprint(blueprint, url_prefix="/PluginManager")

@app.before_request
def br():
    g.signin = True

@app.route("/")
def index():
    app.logger.info(app.static_folder)
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
