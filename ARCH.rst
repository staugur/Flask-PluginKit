Flask-PluginKit 架构说明
========================

1. 项目定位
-----------

Flask-PluginKit 是一个面向 Flask 应用的插件化扩展框架。它的核心目标是：

- 让应用能够动态发现并加载插件；
- 为插件提供统一的扩展点（模板、路由、蓝图、钩子、过滤器等）；
- 支持本地插件目录、第三方包插件以及通过 Web 管理界面进行安装、启用/禁用、上传/下载。

项目实现主要集中在以下几个模块：

- ``flask_pluginkit/pluginkit.py``：插件管理器核心，负责扫描、解析、注册和运行插件。
- ``flask_pluginkit/_installer.py``：插件安装与卸载逻辑。
- ``flask_pluginkit/_web.py``：Web 管理界面与 API。
- ``flask_pluginkit/utils.py``：工具函数、存储抽象和辅助能力。
- ``examples/``：示例插件，说明插件编写方式。


2. 典型插件模型
----------------

一个插件通常是一个 Python 包目录，包含：

.. code-block:: text

   plugins/
   └── demo_plugin/
       ├── __init__.py
       ├── templates/
       └── static/

插件包中至少要暴露：

- ``__plugin_name__``：插件名字
- ``__version__``：版本号
- ``__author__``：作者
- ``register()``：注册扩展点的入口函数

这也是插件作为“合法扩展”参与框架的前提；``on_app_ready(app)`` 只会在这类插件上生效。

示例插件会返回一个字典，里面包含不同的“扩展点”定义，例如：

.. code-block:: python

   def register():
       return {
           "bep": dict(blueprint=bp, prefix=None),
           "hep": dict(before_request=limit_handler),
       }


3. 核心组件
-----------

3.1 PluginManager
~~~~~~~~~~~~~~~~~

``PluginManager`` 是整个框架的主控制器，负责：

- 接收 Flask app 并初始化；
- 扫描本地插件目录和第三方插件包；
- 解析插件元数据；
- 处理插件扩展点；
- 将插件挂载到 Flask 应用中；
- 提供模板上下文函数（如 ``emit_tep``、``emit_assets``、``emit_config``）。

它是通过 ``PluginManager(app)`` 或 ``PluginManager().init_app(app)`` 初始化的。

3.2 PluginInstaller
~~~~~~~~~~~~~~~~~~~

``PluginInstaller`` 负责“插件包”的安装与移除：

- 支持本地压缩包安装（``.zip``、``.tar.gz``、``.tgz``）；
- 支持远程 URL 下载并解包；
- 支持通过 ``pip`` 安装第三方插件包；
- 支持删除本地已安装插件目录。

3.3 Web 管理器
~~~~~~~~~~~~~~

``blueprint`` 是一个 Flask Blueprint，提供：

- 插件启用/禁用接口；
- 上传/下载插件包接口；
- 安装第三方包接口；
- 插件管理页面。

它通过 ``/api`` 和 ``/msg`` 与前端交互。


4. 插件生命周期
----------------

4.1 初始化阶段
~~~~~~~~~~~~~~~

当 ``PluginManager`` 初始化时，流程如下：

1. 确定插件根目录：

   - 本地插件目录默认位于应用根目录下的 ``plugins/``。

2. 扫描第三方插件包：

   - 读取 ``plugin_packages`` 配置；
   - 通过 ``importlib.import_module()`` 导入插件模块。

3. 扫描本地插件目录：

   - 遍历 ``plugins/<plugin_name>/__init__.py`` 形式的目录插件。

4. 加载插件模块：

   - 检查插件是否具备标准元数据，并确认它是否具备 ``register()`` 入口；这决定了它是否被视为合法扩展插件。

5. 解析扩展点：

   - 将插件的扩展点收集为内部结构，形成插件信息对象。

6. 进行预处理：

   - 处理 ``p3`` 这种跨插件预处理扩展点。

7. 挂载到 Flask：

   - 注册模板加载器、静态资源路由、蓝图、视图、过滤器、错误处理器与上下文处理器。

4.2 运行阶段
~~~~~~~~~~~~~

插件在应用运行期不会被“动态执行”脚本，而是以“挂载后的扩展能力”参与 Flask 请求处理：

- ``hep`` 会挂载到 Flask 请求钩子中；
- ``bep`` 会注册蓝图；
- ``vep`` 会注册路由；
- ``filter`` 会注入 Jinja 过滤器；
- ``errhandler`` 会注册错误处理器；
- ``tcp`` 会参与模板上下文构造；
- ``tep`` 会在模板渲染时被 ``emit_tep()`` 取出并渲染。


5. 扩展点设计
--------------

除了通过 ``register()`` 注册的扩展点之外，框架还引入了“状态点”机制：

- ``on_app_ready(app)``：当所有插件都被扫描、注册并挂载到 Flask 应用后执行；适合做应用级别的就绪初始化。

它不是通过 ``register()`` 声明，而是直接以函数名为识别点；但只有在插件已经作为“合法扩展插件”参与正常注册流程时，才会在应用初始化完成后自动执行，并将当前 Flask 应用实例作为唯一参数传入。也就是说，单独只有 ``on_app_ready`` 而没有 ``register()`` 的插件会被视为非法扩展而拒绝加载。

插件系统提供了以下扩展点：

- ``tep``：模板扩展点，用于向页面注入片段或模板内容。
- ``hep``：Hook 扩展点，用于拦截请求生命周期，如 before_request。
- ``bep``：Blueprint 扩展点，用于注册子蓝图。
- ``vep``：View 扩展点，用于注册额外路由。
- ``cvep``：Class-based view 扩展点，用于注册类视图。
- ``filter``：模板过滤器，用于注入 Jinja 过滤器。
- ``errhandler``：错误处理，用于定制 404/403/500 等行为。
- ``tcp``：模板上下文处理器，用于注入模板变量。
- ``p3``：预处理扩展点，用于在插件加载后统一修改或增强其他扩展点。

其中，``tep`` 与 ``emit_tep()`` 是最典型的“插件内容注入”机制。

5.1 应用上下文场景：插件如何作用到整个 Flask 应用
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

除了请求上下文，插件也可以在“应用上下文”层面工作。这里的关键点是：插件不需要依赖某一次具体请求，就能在应用启动完成后为整个应用注入状态、配置或共享资源。

最典型的做法是利用 ``on_app_ready(app)`` 这一状态点，在应用初始化收尾阶段执行一次性逻辑。例如，插件可以：

- 把自己的对象挂到 ``app.extensions`` 中，供后续模块复用；
- 向 ``app.config`` 写入默认配置；
- 在应用上下文中初始化一个共享客户端、缓存对象或连接池；
- 注册应用级别的全局变量或模板全局函数；
- 绑定应用级别的生命周期行为（如 teardown、日志、监控等）。

示例：

.. code-block:: python

   from flask import current_app


   def on_app_ready(app):
       with app.app_context():
           # 1. 配置项：让整个应用都能看到插件能力
           app.config.setdefault("DEMO_PLUGIN_ENABLED", True)
           app.config.setdefault("DEMO_PLUGIN_TITLE", "Demo Plugin")

           # 2. 共享服务：挂到 app.extensions，供后续模块复用
           app.extensions["demo_plugin"] = {
               "ready": True,
               "title": app.config["DEMO_PLUGIN_TITLE"],
           }

           # 3. 模板全局变量：让模板也能直接使用
           app.jinja_env.globals["demo_plugin_name"] = "demo"

           # 4. 记录应用级初始化日志
           current_app.logger.info("demo plugin initialized")

如果应用在启动后需要读取这些配置，可以直接在任意地方使用：

.. code-block:: python

   from flask import current_app

   with current_app.app_context():
       enabled = current_app.config.get("DEMO_PLUGIN_ENABLED")
       title = current_app.config.get("DEMO_PLUGIN_TITLE")

这类场景的特点是：

- 它们发生在应用已经“准备好”的阶段，而不是某次请求执行时；
- 插件逻辑可以影响整个应用，而不是只影响单次请求；
- 适合做应用级初始化、共享服务绑定和全局配置注入。

如果插件要在请求之外访问当前应用状态，最常见的方式就是：

.. code-block:: python

   from flask import current_app

   with app.app_context():
       value = current_app.config.get("DEMO_PLUGIN_ENABLED")

这类写法说明，插件已经进入了“应用上下文”，可以安全地访问整个应用的配置和状态。


6. 请求执行流程
----------------

下面是一个简化请求处理流：

.. code-block:: text

   Client Request
     -> Flask app
     -> before_request hooks (from hep)
     -> route/view matching
     -> plugin registered blueprint/view/error handlers
     -> template rendering
     -> emit_tep / emit_assets / context processors
     -> Response

6.1 钩子执行
~~~~~~~~~~~~

``hep`` 以 ``before_request``、``after_request``、``teardown_request`` 三类钩子形式工作：

- ``before_request`` 可以直接拦截请求；
- ``after_request`` 可以修改 response；
- ``teardown_request`` 用于清理或收尾工作。

6.2 模板注入
~~~~~~~~~~~~

插件通过 ``tep`` 声明模板扩展点，应用在模板中调用：

.. code-block:: jinja2

   {{ emit_tep("hello") }}

``emit_tep()`` 会收集所有启用插件的对应模板内容并渲染输出。

6.3 静态资源
~~~~~~~~~~~~

插件静态文件通过 ``emit_assets()`` 生成资源 URL，最终由统一静态路由提供服务：

.. code-block:: jinja2

   {{ emit_assets('demo', 'css/demo.css') }}


7. 插件启用/禁用机制
--------------------

插件的启用状态并不是只存在于内存中，而是通过目录文件标记：

- ``ENABLED``：表示启用
- ``DISABLED``：表示禁用

``enable_plugin()`` 和 ``disable_plugin()`` 会在插件目录中创建/删除空文件，从而影响下次加载时的状态。这样设计的好处是：

- 状态可以在应用重启后保留；
- 便于通过文件系统进行人工管理；
- 与 Web 管理界面天然兼容。


8. Web 管理流程
----------------

Web 管理入口由 Blueprint 提供，流程如下：

1. 用户访问插件管理页面；
2. Web API 接受动作：

   - ``enablePlugin``
   - ``disablePlugin``
   - ``reloadApp``
   - ``uploadPlugin``
   - ``downloadPlugin``
   - ``installPackage``

3. 对应动作调用 ``PluginManager`` 或 ``PluginInstaller``；
4. 结果以 JSON 返回给前端。

其中：

- ``uploadPlugin``：上传本地插件包并解压；
- ``downloadPlugin``：从远程 URL 下载插件包；
- ``installPackage``：通过 ``pip`` 安装第三方包插件。


9. 设计特点
------------

9.1 以“扩展点 + 注册”驱动
~~~~~~~~~~~~~~~~~~~~~~~~~~~

插件不是直接修改核心逻辑，而是通过注册扩展点把自身能力挂接到应用中。

9.2 兼容本地与第三方插件
~~~~~~~~~~~~~~~~~~~~~~~~~

框架同时支持：

- 本地目录插件；
- 作为 Python 包发布的第三方插件。

9.3 以 Flask 原生机制为基础
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

它没有重新发明一套完整的 Web 框架，而是借助 Flask 的：

- 蓝图注册；
- 请求钩子；
- 模板渲染；
- 错误处理；
- 静态文件服务。

9.4 适合“轻量插件化”场景
~~~~~~~~~~~~~~~~~~~~~~~~~~

它适合需要快速扩展页面、路由和拦截逻辑的场景，但并不是一个提供复杂插件隔离、沙箱和热更新的完整插件平台。


10. 一句话总结
---------------

Flask-PluginKit 的核心流程可以概括为：

“插件被发现 -> 解析扩展点 -> 绑定到 Flask 生命周期 -> 在请求和模板渲染阶段被调用”。

这也是它最核心的架构骨架。
