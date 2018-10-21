插件概述
--------

插件是一个本地目录，它应该位于程序plugins目录下，且是一个合法的python包，即：plugins下包含 ``__init__.py`` 文件，插件也包含 ``__init__.py`` , 这个文件标识了目录是一个包，同时也标识了这个插件，是核心代码，插件入口。

术语表
------

* tep - 模板扩展点
* bep - 蓝图扩展点
* cep - 上下文扩展点
* yep - CSS样式扩展点
* sep - 信号扩展点

核心代码
--------

这里是一个最迷你的代码::

    # -*- coding: utf-8 -*-

    #：你的插件名称，必须和插件目录名称等保持一致.
    __name__        = "Demo"
    #: 插件描述信息,什么用处.
    __description__ = "A Plugin Demo"
    #: 插件作者
    __author__      = "Mr.tao <staugur@saintic.com>"
    #: 插件版本
    __version__     = "0.1.1"

    #: 返回插件主类
    def getPluginClass():
        return PluginDemoMain

    #: 插件主类, 请保证getPluginClass准确返回此类
    class PluginDemoMain(object):

        def run(self):
            pass


这里还有一个完整的例子，包含了Flask-PluginKit的完整功能，`点击查看 <https://github.com/staugur/Flask-PluginKit/tree/master/example/plugins/example>`_

代码解析
--------

参考上面迷你代码，这是一个插件所需要的最少的代码，包含元数据(__meta__)和插件类(由getPluginClass函数返回)。

元数据(__meta__)完整列表::

    #: 你的插件名称，必须和插件目录名称等保持一致.
    __name__        = "Demo"
    #: 插件描述信息,什么用处.
    __description__ = "A Plugin Demo"
    #: 插件作者
    __author__      = "Mr.tao <staugur@saintic.com>"
    #: 插件版本
    __version__     = "0.1.1"
    #: 插件主页
    __url__         = "https://github.com/staugur/Flask-PluginKit"
    #: 插件许可证
    __license__     = "MIT"
    #: 插件许可证文件，你的插件目录下应该有个名叫LICENSE的许可证文件
    __license_file__= "LICENSE"
    #: 插件自述文件，你的插件目录下应该有个README的描述说明文件
    __readme_file__ = "README"
    #: 插件状态, enabled、disabled
    __state__       = "enabled"

插件类::

    def getPluginClass():
        return YourPluginClass

    class YourPluginClass(object):

        def run(self):
            pass

        def register_tep(self):
            """注册模板入口, 返回扩展点名称及扩展的代码, 其中include点必须是实际的HTML文件, string点是HTML代码、字符串等."""
            return dict()

        def register_cep(self):
            """注册上下文入口, 返回扩展点名称及执行的函数"""
            return dict()

        def register_bep(self):
            """注册蓝图入口, 返回蓝图路由前缀及蓝图名称"""
            return dict()

        def register_yep(self):
            """注册样式扩展点，返回扩展点及对应css文件"""
            return dict()

插件类详解
----------

插件类可以是继承自程序的某个基类，run、register_*至少存在一个方能加载为插件，以便于插件类使用程序基类接口，不过你可能需要在 ``__init__.py`` 顶处导入::

    #: 若想引用程序基类需先导入这个模块
    from __future__ import absolute_import

方法: run -> 仅插件加载时运行此方法
***********************************

    环境: 非web

    用法: 普通方法

方法: register_tep -> 注册模板上下文
*************************************

    环境: web请求上下文、模板中使用

    用法: 
        * 要求返回字典，格式是: dict(扩展点=HTML字符串或模板文件)
        * 以.html .htm结尾即模板文件，模板文件应该在插件包/templates下

方法: register_cep -> 注册请求上下文
*************************************

    环境: web请求上下文、注册到flask钩子

    用法: 
        * 要求返回字典，格式是: dict(扩展点=function)，目前支持三种扩展点: before_request_hook、after_request_hook、teardown_request_hook
        * 三种扩展点分别是请求前、请求后(返回前)、请求后(返回前，无论是否发生异常)
        * before_reqest_hook还可以拦截请求，设置属性is_before_request_return=True，使用make_response、jsonify等响应函数或Response构造响应类

方法: register_bep -> 注册蓝图上下文
*************************************

    环境: web请求上下文

    用法: 注册蓝图，要求返回字典，dict(blueprint=蓝图类, prefix=蓝图挂载点(比如/example))

方法: register_yep -> 注册静态css文件
*************************************

    环境: web请求上下文、模板中使用

    用法: 要求返回字典，类似于register_tep，格式是: dict(扩展点=CSS文件)，CSS文件应该在插件包/static下

简单存储
*************************************

v1.3.0支持简单存储服务，其配置姑且命名s3，初始化 ``PluginManager`` 时传递s3，值为local(本地文件)、redis(需要传递s3_redis参数，即redis_url)，目前仅支持这两种。
不过您也可以自定义存储类，要求是继承自 :class:`~flask_pluginkit.utils.BaseStorage`, 执行 ``storage`` 函数时传入 ``sf(继承的类)`` 和 ``args(继承类参数，如果有的话)``。

加载逻辑
--------

插件加载在 ``flask run`` 时完成, 加载类是 :class:`~flask_pluginkit.PluginManager`, 它的析构函数支持你传递plugins_base(默认程序目录)、plugins_folder(插件所在目录)设置插件绝对路径目录，还支持工厂模式，更多参数参见API文档。

流程如下:
**********

    1. 通过 ``init_app`` 完成实例构造，初始化参数。
    2. 扫描插件目录，符合插件规则的包将被动态加载。
    3. 加载插件信息，写入到所有插件列表。
    4. Flask-PluginKit设置支持多模板文件夹、多静态文件夹（插件目录下）。
    5. Flask-PluginKit注册全局模板函数 ``emit_tep`` 和 ``emit_yep``, 分别是渲染模板上下文和CSS上下文。
    6. 注册所有启用插件的蓝图扩展点BEP。
    7. 使用before_request装饰器注册所有启用插件的上下文扩展点CEP。
    8. 将 ``PluginManager`` 附加到app中，完成加载，等待使用。


