# -*- coding: utf-8 -*-
"""
    Flask-Plugin-Development-Kit.libs.plugins
    ~~~~~~~~~~~~~~

    Plugins Manager: load and run plugins.

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os, logging


class PluginManager(object):
    """
    定义插件基类, 遵循格式如下:
    插件为目录, 目录名称为插件名称, 插件入口文件是__init__.py, 文件内包含name、description、version、author、license、url、README、state等插件信息.
    静态资源请通过提供的接口上传至又拍云等第三方存储中.
    plugins/
    ├── plugin1
    │   ├── __init__.py
    │   ├── LICENSE
    │   ├── README
    │   └── templates
    │       └── plugin1
    └── plugin2
        ├── __init__.py
        ├── LICENSE
        ├── README
        └── templates
            └── plugin2
    """

    def __init__(self):
        self.plugins     = []
        self.plugin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
        self.__scanPlugins()
        logging.debug(self.plugins)

    def __getPluginInfo(self, package, plugin):
        """ 组织插件信息 """
        try:
            url = plugin.__url__
        except AttributeError:
            url = None

        try:
            license = plugin.__license__
        except AttributeError:
            license = None

        try:
            license_file = plugin.__license_file__
        except AttributeError:
            license_file = None

        try:
            readme_file = plugin.__readme_file__
        except AttributeError:
            readme_file = None

        try:
            plugin_state = plugin.__state__
        except AttributeError:
            plugin_state = "enabled"

        return {
            "plugin_name": plugin.__name__,
            "plugin_description": plugin.__description__,
            "plugin_version": plugin.__version__,
            "plugin_author": plugin.__author__,
            "plugin_url": url,
            "plugin_license": license,
            "plugin_license_file": license_file,
            "plugin_readme_file": readme_file,
            "plugin_state": plugin_state,
            "plugin_tpl_path": os.path.join("plugins", package, "templates"),
            "plugin_tep": {},
            "plugin_cep": {},
            "plugin_bep": {}
        }

    def __scanPlugins(self):
        """ 扫描插件目录 """
        logging.info("Initialization Plugins Start, loadPlugins path: {0}".format(self.plugin_path))
        if os.path.exists(self.plugin_path):
            for package in os.listdir(self.plugin_path):
                _plugin_path = os.path.join(self.plugin_path, package)
                if os.path.isdir(_plugin_path):
                    if os.path.isfile(os.path.join(_plugin_path, "__init__.py")):
                        logging.info("find plugin package: {0}".format(package))
                        self.__runPlugins(package)
        else:
            logging.warning("Plugins directory not in here!")

    def __runPlugins(self, package):
        """ 动态加载插件模块,遵循插件格式的才能被启用并运行,否则删除加载 """

        #: 动态加载模块(plugins.package): 可以查询自定义的信息, 并通过getPluginClass获取插件的类定义
        plugin = __import__("{0}.{1}".format("plugins", package), fromlist=["plugins",])
        #: 检测插件信息
        if plugin.__name__ and plugin.__version__ and plugin.__description__ and plugin.__author__ and plugin.__state__ == "enabled":
            #: 获取插件信息
            pluginInfo = self.__getPluginInfo(package, plugin)
            #: 获取插件主类并实例化
            p = plugin.getPluginClass()
            i = p()
            logging.info("runPlugin: package is {0}.{1}, class instance is {2}".format("plugins", package, i))
            #: 更新插件信息
            pluginInfo.update(plugin_instance=i)
            #: 运行插件主类的run方法
            if hasattr(i, "run"):
                i.run()
            #: 注册模板扩展点
            if hasattr(i, "register_tep"):
                tep = i.register_tep()
                logging.info("The plugin {0} wants to register the following template extension points: {1}".format(package, tep))
                if isinstance(tep, dict):
                    pluginInfo.update(plugin_tep=tep)
                    logging.info("Register TEP Success")
                else:
                    logging.error("Register TEP Failed, not a dict")
            #: 注册上下文扩展点
            if hasattr(i, "register_cep"):
                cep = i.register_cep()
                logging.info("The plugin {0} wants to register the following context extension points: {1}".format(package, cep))
                if isinstance(cep, dict):
                    pluginInfo.update(plugin_cep=cep)
                    logging.info("Register CEP Success")
                else:
                     logging.error("Register CEP Failed, not a dict")
            #: 注册蓝图扩展点
            if hasattr(i, "register_bep"):
                bep = i.register_bep()
                logging.info("The plugin {0} wants to register the following blueprint extension points: {1}".format(package, bep))
                if isinstance(bep, dict):
                    pluginInfo.update(plugin_bep=bep)
                    logging.info("Register BEP Success")
                else:
                    logging.error("Register BEP Failed, not a dict")
            #: 加入全局插件中
            if hasattr(i, "run") or hasattr(i, "register_tep") or hasattr(i, "register_cep") or hasattr(i, "register_bep"):
                self.plugins.append(pluginInfo)
            else:
                logging.error("The current class {0} does not have the `run` or `register_tep` or `register_cep` or `register_bep` method".format(i))
        else:
            del plugin
            logging.warning("This plugin `{0}` not conform to the standard plugin format, or has been disabled".format(package))

    @property
    def get_all_plugins(self):
        """ 获取所有插件 """
        return self.plugins

    @property
    def get_enabled_plugins(self):
        """ 获取所有启用的插件 """
        return [ p for p in self.get_all_plugins if p["plugin_state"] == "enabled" ]

    @property
    def get_all_tep(self):
        """模板扩展点, Template extension point, 更多扩展点自己定义.
        #No1. 自定义在模板中的扩展点:
        TEP: base_front_header_include
        TEP: base_front_header_string
        #No2. 模板中启用自定义的扩展点:
        {% if base_front_header_include %}
            {% for hi in base_front_header_include() %}
                {% include hi %}
            {% endfor %}
        {% endif %}
        {% if base_front_header_string %}
            {% for hs in base_front_header_string() %}
                {{ hs|safe }}
            {% endfor %}
        {% endif %}
        """
        return dict(
            base_front_header_include     = lambda: [ plugin["plugin_tep"].get("base_front_header_include") for plugin in self.get_enabled_plugins if plugin["plugin_tep"].get("base_front_header_include") ],
            base_front_header_string      = lambda: [ plugin["plugin_tep"].get("base_front_header_string") for plugin in self.get_enabled_plugins if plugin["plugin_tep"].get("base_front_header_string") ],
        )

    @property
    def get_all_cep(self):
        """上下文扩展点, Context extension point, 分别对应请求前、请求后(返回前):
        CEP: before_request_hook
        CEP: after_request_hook
        """
        return dict(
            before_request_hook     = lambda: [ plugin["plugin_cep"].get("before_request_hook") for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("before_request_hook") ],
            after_request_hook      = lambda: [ plugin["plugin_cep"].get("after_request_hook") for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("after_request_hook") ],
        )

    @property
    def get_all_bep(self):
        """蓝图扩展点"""
        return [ plugin["plugin_bep"] for plugin in self.get_enabled_plugins if plugin["plugin_bep"] ]
        