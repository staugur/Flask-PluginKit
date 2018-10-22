fixflask.py
-----------

这个文件是继承Flask的类，增加了一些功能，即支持多静态文件夹(来自于 ``flask-multistatic`` )、支持 ``before_request_top`` (此装饰器与before_request作用一致，区别是它将装饰的函数置于钩子首位)。


使用方法::

    from flask_pluginkit import Flask
    app = Flask(__name__)

web.py
------

这是一个蓝图，:class:`~flask_pluginkit.blueprint`, 在您的app中注册此蓝图，它提供一个页面展示插件列表，支持禁用、启用插件、重启app、访问认证。

当然，这个蓝图仅支持flask-pluginkit的 :class:`~flask_pluginkit.PluginManager` 初始化的app，没有此扩展，蓝图不可用。

重启app功能::

    # 支持生产环境重启gunicorn、uwsgi

    # 要求安装模块
    pip install psutil

    # 使用gunicorn启动的应用 - app配置
    app.config.update(ENV="production", PLUGINKIT_GUNICORN_ENABLED=True, PLUGINKIT_GUNICORN_PROCESSNAME="进程名")

    # 使用uwsgi启动的应用 - app配置
    app.config.update(ENV="production", PLUGINKIT_UWSGI_ENABLED=True)

访问认证::

    # 支持字段认证、HTTP Basic Auth

    # app配置
    app.config.update(PLUGINKIT_AUTHMETHOD=值)

    值为BOOL为字段认证，使用 ``g.signin`` 认证，当此值为 ``True`` 时允许访问。

    值为BASIC为HTTP Basic Auth，支持传入 ``PLUGINKIT_AUTHREALM`` 设置提示信息，必须传入 ``PLUGINKIT_AUTHUSERS`` 设置认证的用户名及密码，要求类型是字典，key是用户名，value是密码。

示例::

    from flask_pluginkit import Flask, PluginManager, blueprint

    app = Flask(__name__)

    app.update(ENV="production", PLUGINKIT_GUNICORN_ENABLED=True, PLUGINKIT_GUNICORN_PROCESSNAME="gunicorn: master [xxx]", PLUGINKIT_AUTHREALM="BASIC", PLUGINKIT_AUTHUSERS=dict(admin="admin"))

    plugin = PluginManager(app)

    app.register_blueprint(blueprint, url_prefix="/PluginManager")

installer.py
------------

安装插件类, :class:`~flask_pluginkit.PluginInstaller`, 支持添加http远程插件和本地插件。
