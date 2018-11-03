安装使用
--------

先安装(Installation)，再初始化(Initialization)

::

    $ pip install Flask-PluginKit

第一种方法：普通模式(Usage)

::

    from flask_pluginkit import PluginManager
    plugin = PluginManager(app)

第二种方法：工厂模式(The factory pattern)

::

    from flask_pluginkit import PluginManager
    plugin = PluginManager()
    plugin.init_app(app)

插件结构
--------

安装完成后，您可以开发第一个插件。最小的插件需要至少拥有自己的目录，目录必须包含\ ``__init__.py``\ 文件，否则不认为这是一个插件包！

您的插件核心代码应该写在\ ``__init__.py``\ 文件中，包含注册插件所需的元数据。

一个最简单的插件可能是这样的：

::

    plugins/example/
    ├── __init__.py

一个复杂的插件也可能是这样的：

::

    plugins/example/
    ├── __init__.py
    ├── static
    │   └── example
    │       └── demo.css
    └── templates
        └── example
            └── demo.html

Hello World!
------------

这是一个示例应用，代码\ `在这里 <https://github.com/staugur/flask-pluginkit/tree/master/example>`__\ 。

这个示例中的演示插件(位于plugins/example)，它基本上已经包含了Flask-PluginKit目前所提供的所有功能点，它本来就是一个帮助插件，可以复制修改一份建立属于您的插件。

-  安装依赖包，\ ``pip install -r requirements.txt``
-  运行它，\ ``python main.py``\ ，首页大概是这样：

    |image0|

    温馨提示：红色部分，就是plugins/example/static/example/demo.css设定的，支持插件添加静态文件，在v0.1.8及之后版本支持通过register\_yep注册静态文件，当然也可以直接在模板中link
    css，但不建议。

-  更多插件相关，请参阅\ ``插件详解``\ 一节。

启用、禁用插件
--------------

插件不是pypi上发布的包，它应该在应用程序中的本地目录，启用(enabled)、禁用(disabled)一个插件有两种方法。

-  第一种方法是将\ ``__init__.py``\ 中\ ``__state__``\ 值设为\ ``enabled``\ 或\ ``disabled``
-  第二种方法是添加\ ``ENABLED``\ 或\ ``DISABLED``\ 文件（此方法优先级高于第一种，DISABLED文件优先级高于ENABLED文件）

    请注意：启用、禁用的操作需要重启Web应用程序才能生效，需要您自行解决，使用gunicorn作为启动的，可以参考 :class:`~flask_pluginkit.blueprint` 中的路由函数，原理是通过向主进程发送HUP信号重载app。

.. |image0| image:: ./_static/images/flask_pluginkit_demo.png
