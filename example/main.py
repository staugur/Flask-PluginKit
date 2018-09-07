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

import logging
logging.basicConfig(level=logging.DEBUG,
                format='[ %(levelname)s ] %(asctime)s %(filename)s:%(threadName)s:%(process)d:%(lineno)d %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                filename='huaban.log',
                filemode='a')

from flask import render_template_string
from flask_pluginkit import PluginManager
from flask_multistatic import MultiStaticFlask as Flask

__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__doc__ = 'An example for Flask-PluginKit'
__version__ = '0.1.0'


# 初始化定义application
app = Flask(__name__)

# 初始化插件管理器(自动扫描并加载运行)
plugin = PluginManager(app)

@app.route("/")
def index():
    app.logger.info(app.static_folder)
    return render_template_string("<h1>Hello World!</h1>{{ get_tep_string('tep2') }}")

if __name__ == '__main__':
    app.run(debug=True)
