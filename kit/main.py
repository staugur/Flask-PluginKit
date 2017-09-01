# -*- coding: utf-8 -*-
"""
    Flask-Plugin-Development-Kit.main
    ~~~~~~~~~~~~~~

    Entrance

    Docstring conventions:
    http://flask.pocoo.org/docs/0.10/styleguide/#docstrings

    Comments:
    http://flask.pocoo.org/docs/0.10/styleguide/#comments

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import jinja2
import os.path
from config import GLOBAL
from flask import Flask, request, g
from libs.plugins import PluginManager


__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__doc__ = 'Web program plugin development kit based on flask.'
__version__ = '0.0.1'


# 初始化定义application
app = Flask(__name__)

# 初始化插件管理器(自动扫描并加载运行)
plugin = PluginManager()

# 自定义添加多模板文件夹
loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader([p.get("plugin_tpl_path") for p in plugin.get_enabled_plugins if os.path.isdir(
        os.path.join(app.root_path, p["plugin_tpl_path"]))]),
])
app.jinja_loader = loader

# 注册全局模板扩展点
for tep_name, tep_func in plugin.get_all_tep.iteritems():
    app.add_template_global(tep_func, tep_name)


# 注册蓝图扩展点
for bep in api.plugin.get_all_bep:
    prefix = bep["prefix"]
    app.register_blueprint(bep["blueprint"], url_prefix=prefix)


@app.before_request
def before_request():
    # 上下文扩展点之请求前
    before_request_hook = plugin.get_all_cep.get("before_request_hook")
    for cep_func in before_request_hook():
        cep_func(request=request, g=g)


@app.after_request
def after_request(response):
    # 上下文扩展点之请求后(返回前)
    after_request_hook = plugin.get_all_cep.get("after_request_hook")
    for cep_func in after_request_hook():
        cep_func(request=request, response=response)
    return response

if __name__ == '__main__':
    Host = GLOBAL.get('Host')
    Port = GLOBAL.get('Port')
    app.run(host=Host, port=int(Port), debug=True)
