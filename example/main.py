# -*- coding: utf-8 -*-
"""
    Flask-Plugin-Development-Kit.main
    ~~~~~~~~~~~~~~

    Entrance

    Docstring conventions:
    http://flask.pocoo.org/docs/0.10/styleguide/#docstrings

    Comments:
    http://flask.pocoo.org/docs/0.10/styleguide/#comments

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

from flask import Flask, render_template_string
from libs.plugins import PluginManager

__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__doc__ = 'Web program plugin development kit based on flask.'
__version__ = '0.1.0'


# 初始化定义application
app = Flask(__name__)

# 初始化插件管理器(自动扫描并加载运行)
plugin = PluginManager(app)

@app.route("/")
def index():
    return render_template_string("<h1>Hello World!</h1>{{ get_tep_string('tep2') }}")

if __name__ == '__main__':
    app.run(debug=True)
