插件概述
--------

插件可以是一个本地目录，它应该位于程序plugins目录下，且是一个合法的python包，即：plugins下包含 ``__init__.py`` 文件，插件也包含 ``__init__.py`` , 这个文件标识了目录是一个包，同时也标识了这个插件，是核心代码，插件入口。

但请注意：插件亦可以是一个第三方包，您可以使用pip安装它，而不必放到程序当前目录！第三方插件的格式也应该同本地目录一般，详细见 `#第三方插件 <#third-party-plugin>`_


术语表
------

* tep - 模板扩展点
* hep - 钩子扩展点
* bep - 蓝图扩展点
* yep - 样式扩展点
* dcp - 动态连接点

核心代码
--------

这里是一个最迷你的代码::

    # -*- coding: utf-8 -*-

    #: 你的插件名称，不严格要求和插件目录名称保持一致.
    #: Your plugin name is not strictly required to be consistent with the plugin directory name.
    __plugin_name__ = "Demo"

    #: 插件描述信息,什么用处.
    #: What is the use of plug-in description information.
    __description__ = "A Plugin Demo"

    #: 插件作者
    #: Plugin Author
    __author__ = "Mr.tao <staugur@saintic.com>"

    #: 插件版本
    #: Plugin Version
    __version__ = "0.1.1"

    #: 返回插件主类
    #: (eturns the plugin main class.
    def getPluginClass():
        return PluginDemoMain

    #: 插件主类, 请保证getPluginClass准确返回此类
    #: (The plugin main class, please ensure that getPluginClass returns this class exactly.)
    class PluginDemoMain(object):

        def run(self):
            pass


这里还有一个完整的例子，包含了Flask-PluginKit的完整功能，`点击查看 <https://github.com/staugur/Flask-PluginKit/tree/master/example/pypi/flask_pluginkit_demo>`_

代码解析
--------

参考上面迷你代码，这是一个插件所需要的最少的代码，包含元数据(__meta__)和插件类(由getPluginClass函数返回)。

元数据(__meta__)完整列表::

    #: 你的插件名称，不严格要求和插件目录名称保持一致.
    #: Your plugin name is not strictly required to be consistent with the plugin directory name.
    __plugin_name__ = "Demo"

    #: 插件描述信息,什么用处.
    #: What is the use of plug-in description information.
    __description__ = "A Plugin Demo"

    #: 插件作者
    #: Plugin Author
    __author__ = "Mr.tao <staugur@saintic.com>"

    #: 插件版本
    #: Plugin Version
    __version__ = "0.1.1"

    #: 插件主页
    #: Plugin Homepage
    __url__ = "https://github.com/staugur/Flask-PluginKit"

    #: 插件许可证
    #: Plugin LICENSE
    __license__ = "MIT"

    #: 插件许可证文件，你的插件目录下应该有个名叫LICENSE的许可证文件
    #: The plugin LICENSE file. Your plugin directory should have a LICENSE file called LICENSE.
    __license_file__= "LICENSE"

    #: 插件自述文件，你的插件目录下应该有个README的描述说明文件
    #: The plugin profile should have a README description file in your plugin directory.
    __readme_file__ = "README"
    
    #: 插件状态, enabled、disabled
    #: The plugin Status, enabled or disabled.
    __state__ = "enabled"

插件类::

    def getPluginClass():
        return YourPluginClass

    class YourPluginClass(object):

        def run(self):
            pass

        def register_tep(self):
            """注册模板入口, 返回扩展点名称及扩展的代码, 其中include点必须是实际的HTML文件, string点是HTML代码、字符串等."""
            return dict()

        def register_hep(self):
            """注册钩子上下文入口, 返回扩展点名称及执行的函数"""
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
    #: If you want to refer to the program base class, you need to pilot the module.
    from __future__ import absolute_import

方法: run -> 仅插件加载时运行此方法
***********************************

    环境: 非web

    用法: 普通方法

方法: register_tep -> 注册模板扩展点，提供模板文件或HTML代码
*************************************************************

    环境: web请求上下文、模板中使用

    用法: 
        * 要求返回字典，格式是: dict(扩展点=HTML字符串或模板文件)
        * 以.html .htm结尾即模板文件，模板文件应该在"插件包/templates"下
        * 非模板文件支持解析HTML代码，不支持jinja2过滤器、函数等
        * 建议您在插件templates下新建目录存放html文件，因为flask-pluginkit仅加载插件下templates目录，且不保证模板冲突，新建目录可以避免与其他插件模板文件冲突，导致无法正常引用。
        * 支持模板排序，您需要初始化 ``PluginManager`` 时传入 ``stpl=True`` 即可支持。register_tep时，格式是:排序数字@模板代码或文件

    示例-注册::

        # 插件类中
        def register_tep(self):
            return dict(base_header="example/header.html", base_footer="Copyright 2018.")

        # 如上，您需要在插件目录下新建"templates/example"目录，并将header.html放入目录中，若不存在会引发 ``flask_pluginkit.exceptions.PluginError`` 异常。

    示例-使用::

        # 使用模板扩展点需要在HTML中渲染或在蓝图中通过 ``render_template`` 返回响应。

        # 模板中。假设以下文件名为base.html是基础模板(插件目录/templates/example/base.html)，通过 ``emit_tep`` 引用，可以传入额外数据

        <html>
        <head>
            {{ emit_tep("base_header") }}
        </head>
        <body>
            {{ emit_tep("base_footer", extra=dict(a=1, b=True, c=[])) }}
        </body>
        </html>

        ## PS: 亦可在其他模板中继承此base.html模板, {% extends "example/base.html" %}, 切记对于模板来说根目录是"插件下/templates"目录，所以强烈建议在此目录下新建子目录。

        # 蓝图中。
        from flask import Blueprint, render_template

        plugin_blueprint = Blueprint("example", "example")
        # 同 plugin_blueprint = Blueprint("example", "example", template_folder="templates")

        @plugin_blueprint.route("/")
        def plugin():
            return render_template("example/base.html")

方法: register_hep -> 注册钩子扩展点，在flask钩子中注册函数
************************************************************

    环境: web请求上下文、注册到flask钩子

    用法: 
        * 要求返回字典，格式是: dict(扩展点=function)，目前支持三种扩展点: before_request_hook、after_request_hook、teardown_request_hook
        * 三种扩展点对应的钩子分别是请求前、请求后(返回前)、请求后(返回前，无论是否发生异常)
        * before_reqest_hook还可以拦截请求，设置属性is_before_request_return=True，使用make_response、jsonify等响应函数或Response构造响应类
        * 建议您在插件类中单独写一个方法，并传递给扩展点，其中after_request_hook会传入 ``response`` 参数，teardown_request_hook会传入 ``exception`` 参数，您扩展点的函数必须支持传入，并可以自行使用。

    示例::

        from flask import request, g

        # 插件类中
        def set_login(self):
            g.login_in = request.args.get("username") == "admin"

        def register_hep(self):
            return {"after_request_hook": lambda resp: resp, "before_request_hook": self.set_login}

        # 如上，您的程序在运行后，每次请求前都会执行before_request_hook的self.set_login函数，请求后返回前会执行after_request_hook的匿名函数。

方法: register_bep -> 注册蓝图扩展点，用来注册一个蓝图
*******************************************************

    环境: web请求上下文

    用法: 注册蓝图，要求返回字典，dict(blueprint=蓝图类, prefix=蓝图挂载点(比如/example))

    示例::

        from flask import Blueprint

        plugin_blueprint = Blueprint("example", "example")

        # 插件类中
        def register_bep(self):
            return dict(blueprint=plugin_blueprint, prefix="/example")

        # 如上，您的程序将会多一个蓝图，URL路径是/example。

方法: register_yep -> 注册静态扩展点，提供模板所需引入的css样式
****************************************************************

    环境: web请求上下文、模板中使用

    用法: 要求返回字典，类似于register_tep，格式是: dict(扩展点=CSS文件)，CSS文件应该在"插件包/static"目录下。

    示例-注册::

        # 插件类中
        def register_yep(self):
            return {"base": "example/demo.css"}

        # 如上，您的插件目录下应该创建"static/example"目录，并将demo.css放入其中，若不存在同样会引发 ``flask_pluginkit.exceptions.PluginError`` 异常。

    示例-使用::

        # 同注册模板上下文的使用方法，使用 ``emit_yep`` 渲染。

        <html>
        <head>
            {{ emit_yep("base") }}
        </head>
        <body>
            代码
        </body
        </html>

简单存储
********

v1.3.0支持简单存储服务，其配置姑且命名s3，初始化 ``PluginManager`` 时传递s3，值为local(本地文件)、redis(需要传递s3_redis参数，即redis_url)，目前仅支持这两种。
不过您也可以自定义存储类，要求是继承自 :class:`~flask_pluginkit.BaseStorage`, 执行 ``storage`` 函数时传入 ``sf(继承的类)`` 和 ``args(继承类参数，如果有的话)``。

使用简单存储有两种情况，一是在app应用上下文及请求上下文中，二是在程序中独立使用::

    # 第一种情况, web环境中, PluginManager加载插件类中集成了 `storage` 方法，附加到app.extensions['pluginkit']中，调用它使用以下:

    from flask import current_app
    current_app.extensions['pluginkit'].storage()

    # 第二种情况

    from flask_pluginkit import LocalStorage

    # 插件类中
    def run(self):
        self.s3 = LocalStorage()

    # 两者使用同个文件或同个redis库时数据一致

动态连接点(dcp)
*****************

动态连接点，动态注册并执行函数将结果返回给模板使用。您可以通过 :func:`flask_pluginkit.push_dcp` 推送给标识点一个函数，在模板中通过 ``emit_dcp`` 执行并获取执行结果(即HTML代码)。

用法::

    ``emit_dcp`` 可以像 ``emit_tep`` 一样传入额外数据(context)，并且在函数中调用。

    ``push_dcp`` 传入标识点、函数和定位，需要在请求上下文中执行::
        event: 标识点，有效字符串
        callback: 普通函数、匿名函数，目前版本不可是类方法
        position: 定位，默认right插入event末尾，left插入event首位，在 ``emit_dcp`` 中可以体验输出效果

    请注意： 每次使用 ``emit_dcp`` 后都会清空此标识点的函数！

使用案例::

    from flask import render_template

    from flask_pluginkit import Flask, PluginManager, push_dcp

    app = Flask(__name__)

    PluginManager(app)

    def test(extra):
        return extra + 'test'

    @app.route("/")
    def index():
        push_dcp("event", test, "left")
        return render_template("index.html")

    # index.html
    {{ emit_dcp('event', extra='template') }}

加载逻辑
--------

插件加载在程序启动时完成, 加载类是 :class:`~flask_pluginkit.PluginManager`, 它的析构函数支持你传递plugins_base(默认程序目录)、plugins_folder(插件所在目录)设置插件绝对路径目录，还支持工厂模式，更多参数参见API文档。

流程如下:
**********

    1. 通过 ``init_app`` 完成实例构造，初始化参数。
    2. 扫描插件目录，符合插件规则的包将被动态加载。
    3. 加载插件信息，依次运行 ``run`` -> ``register_tep`` -> ``register_hep`` -> ``register_bep`` -> ``register_yep`` 等方法, 写入到所有插件列表。
    4. Flask-PluginKit设置支持多模板文件夹、多静态文件夹（插件目录下）。
    5. Flask-PluginKit注册全局模板函数 ``emit_tep``、``emit_yep``、``emit_dcp``, 分别是渲染模板上下文、CSS上下文、渲染动态连接点。
    6. 注册所有启用插件的蓝图扩展点BEP。
    7. 使用before_request等装饰器注册所有启用插件的钩子扩展点。
    8. 将 ``PluginManager`` 附加到app中，完成加载，可以使用 ``app.extensions['pluginkit']`` 调用 ``PluginManager`` 类中方法。


Third party plugin
-------------------

第三方插件是指非程序子目录、来自于pip或easy_install等安装的本地模块。

第三方插件解放使用，程序可以不用将插件代码放到子目录，只需要使用 `pip install` 安装到本地机器上，然后在 `PluginManager` 初始化时传入 `plugin_packages` 参数即可。

这意味着，任何人都可以编写一个包，发布到pypi；使用者写好 `requirements.txt` 并安装依赖，在初始化中调用，一气呵成，而几乎不用担心后续第三方插件升级。


调用：
*******
::

    from flask_pluginkit import Flask, PluginManager
    app = Flask(__name__)
    plugin_manager = PluginManager(app, plugin_packages=["flask_pluginkit_demo"])


如何编写第三方插件：
********************

    1. 首先根据上方 `代码解析 <#id12>`_ 和 `插件类详解 <#id13>`_ 写一个包，参见 `核心代码 <#id10>`_ ，要写在 `__init__.py` 中。


    2. 第一步中实际上就是编写本地插件的过程，本步骤需要编写 `setup.py` ，使本地插件能发布到pypi中供其他人使用::

        from setuptools import setup
        setup(
            name='flask_pluginkit_demo',
            packages=['flask_pluginkit_demo',],
            include_package_data=True,
           ...
        )

    3. 如果你的插件包含模板目录templates或静态目录static等，需要再编写一个额外的清单文件 `MANIFEST.in`::

        recursive-include flask_pluginkit_demo/templates *
        recursive-include flask_pluginkit_demo/static *

    4. 测试发布

        4.1 打包：python setup.py sdist bdist_wheel   #更多参数自行调整

        4.2 到这里，可以使用 `pip install .` 在本地测试是否正常安装。

        4.3 本地测试通过，可以发布到test.pypi.org，这是官方pypi的测试站，里面的包不会被轻易使用，命令是： `twine upload --repository-url https://test.pypi.org/legacy/ dist/*`

        4.4 测试站可以看看界面描述等等是否符合心中要求，没问题就发布到正式站，pypi.org，命令是： `twine upload dist/*`

    5. 示例
        `pypi demo <https://github.com/staugur/Flask-PluginKit/tree/master/example/pypi/>`_

