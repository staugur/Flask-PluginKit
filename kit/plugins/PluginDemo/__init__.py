# -*- coding: utf-8 -*-
"""
    Flask-Plugin-Development-Kit.plugins.PluginDemo
    ~~~~~~~~~~~~~~

    This is a demo for plugin.
    Your Plugin Description.

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

#: Importing these two modules is the first and must be done.
#: 首先导入这两个必须模块
from __future__ import absolute_import
from libs.base import PluginBase
#: Import the other modules here, and if it's your own module, use the relative Import. eg: from .lib import Lib
#: 在这里导入其他模块, 如果有自定义包, 使用相对导入, 如: from .lib import Lib


#：Your plug-in name must be consistent with the plug-in directory name.
#：你的插件名称，必须和插件目录名称等保持一致.
__name__        = "PluginDemo"
#: Plugin describes information. What does it do?
#: 插件描述信息,什么用处.
__description__ = "A demo"
#: Plugin Author
#: 插件作者
__author__      = "Mr.tao <staugur@saintic.com>"
#: Plugin Version
#: 插件版本
__version__     = "0.1" 
#: Plugin Url
#: 插件主页
__url__         = "https://www.saintic.com"
#: Plugin License
#: 插件许可证
__license__     = "MIT"
#: Plugin License File
#: 插件许可证文件
__license_file__= "LICENSE"
#: Plugin Readme File
#: 插件自述文件
__readme_file__ = "README"
#: Plugin state, enabled or disabled
#: 插件状态, enabled、disabled
__state__       = "enabled"

#: Blueprint Examples
from flask import Blueprint, request
from flask_restful import Api, Resource

#: Example No.1
plugin_blueprint = Blueprint("PluginDemo", "PluginDemo")
@plugin_blueprint.route("/")
def plugin():
    return "plugin demo"

#: Example No.2
class ApiDemo(Resource):
    def get(self):
        return True

#: 暂时设定仅支持一个蓝图扩展点
api = Api(plugin_blueprint)
api.add_resource(ApiDemo, '/api', '/api/', endpoint='ApiDemoPoint')

#: 返回插件主类
def getPluginClass():
    return PluginDemoMain

#: 插件主类, 不强制要求名称与插件名一致, 保证getPluginClass准确返回此类
class PluginDemoMain(PluginBase):
    """ 继承自PluginBase基类 """

    def run(self):
        """ 插件一般运行入口 """
        self.logger.info("I am PluginDemoMain, run!")

    def register_tep(self):
        """注册模板入口, 返回扩展点名称及扩展的代码, 其中include点必须是实际的HTML文件, string点是HTML代码、字符串等."""
        tep = {"base_front_navigation_include": "PluginDemo/PluginDemo.html", "base_front_footer_string": "<!--<br/><a href='', title=''>PluginDemo generate</a>-->"}
        return tep

    def _hook(self, **kwargs):
        self.logger.debug("I am a demo for after cep, get redis all keys")

    def register_cep(self):
        """注册上下文入口, 返回扩展点名称及执行的函数"""
        cep = {"after_request_hook": self._hook}
        return cep

    def register_bep(self):
        """注册蓝图入口, 返回蓝图路由前缀及蓝图名称"""
        bep = {"prefix": "/pluginDemo", "blueprint": plugin_blueprint}
        return bep
