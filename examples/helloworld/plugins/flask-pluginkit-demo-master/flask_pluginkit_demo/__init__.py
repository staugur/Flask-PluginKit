# -*- coding: utf-8 -*-
"""
    flask-pluginkit-demo
    ~~~~~~~~~~~~~~~~~~~~~

    This is a demo for plugin.
    Your Plugin Description.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

#: Importing these two modules is the first and must be done.
#: 首先导入这两个必须模块
from __future__ import absolute_import
#: Import the other modules here, and if it's your own module,
#: use the relative Import. eg: from .lib import Lib
#: 在这里导入其他模块, 如果有自定义包, 使用相对导入, 如: from .lib import Lib
from .plugin import plugin_blueprint, api_limit

#: Your plug-in name must be consistent with the plug-in directory name.
#: 你的插件名称，不严格要求和插件目录名称保持一致.
__plugin_name__ = "demo"
#: Plugin describes information. What does it do?
#: 插件描述信息,什么用处.
__description__ = "A Plugin Third Demo"
#: Plugin Author
#: 插件作者
__author__ = "Mr.tao <staugur@saintic.com>"
#: Plugin Version
#: 插件版本
__version__ = "0.2.0"
#: Plugin Url
#: 插件主页
__url__ = "https://github.com/flask-pluginkit/demo"
#: Plugin License
#: 插件许可证
__license__ = "BSD"
#: Plugin License File
#: 插件许可证文件
__license_file__ = "LICENSE"
#: Plugin Readme File
#: 插件自述文件
__readme_file__ = "README.md"
#: Plugin state, enabled or disabled
#: 插件状态, enabled、disabled
__state__ = "enabled"


def register():
    return {
        "tep": {"html": "demo/demo.html", "code": "<p>hello third-demo(from html code)</p>"},
        "hep": {
            "after_request": lambda *args, **kwargs: len(args) + len(kwargs),
            "before_request": api_limit
        },
        "bep": {"prefix": "/demo", "blueprint": plugin_blueprint}
    }
