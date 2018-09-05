# -*- coding: utf-8 -*-
"""
    Flask-Plugin-Development-Kit.libs.plugins
    ~~~~~~~~~~~~~~

    Plugins Manager: load and run plugins.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import sys
import jinja2
import logging


class PluginError(Exception):
    pass


class TemplateEventResult(list):
    """A list subclass for results returned by the event listener that
    concatenates the results if converted to string, otherwise it works
    exactly like any other list.
    """

    def __init__(self, items):
        list.__init__(self, items)

    def __unicode__(self):
        return u''.join(map(str, self))

    def __str__(self):
        if sys.version_info[0] == 2:
            return self.__unicode__().encode('utf-8')
        else:
            return self.__unicode__()


class PluginManager(object):
    """Flask Plugin Manager Extension
    定义插件基类, 遵循格式如下:
    插件为目录, 目录名称为插件名称, 插件入口文件是__init__.py, 文件内包含name、description、version、author、license、url、README、state等插件信息.
    静态资源请通过提供的接口上传至又拍云等第三方存储中.
    ```
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
    ```
    """

    def __init__(self, app=None, plugins_folder="plugins"):
        self.plugins_folder = plugins_folder
        self.plugin_abspath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.plugins_folder)
        self.__plugins = []
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.__scanPlugins()
        # 自定义添加多模板文件夹
        app.jinja_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader([p["plugin_tpl_path"] for p in self.get_enabled_plugins if os.path.isdir(os.path.join(app.root_path, p["plugin_tpl_path"]))]),
        ])
        # 自定义添加多静态文件夹 - flask-multistatic扩展支持
        if isinstance(app.static_folder, list):
            app.static_folder += [p["plugin_ats_path"] for p in self.get_enabled_plugins if os.path.isdir(os.path.join(app.root_path, p["plugin_ats_path"]))]
        # 注册模板变量
        app.jinja_env.globals["get_tep"] = self.get_tep
        app.jinja_env.globals["get_tep_string"] = self.get_tep_string

        # 注册蓝图扩展点
        for bep in self.get_all_bep:
            app.register_blueprint(bep["blueprint"], url_prefix=bep["prefix"])

        # 注册请求上下文扩展点
        @app.before_request
        def _before_request():
            # 上下文扩展点之请求前
            for cep_func in self.get_all_cep["before_request_hook"]:
                cep_func()

        @app.after_request
        def _after_request(response):
            # 上下文扩展点之请求后(返回前且无异常)
            for cep_func in self.get_all_cep["after_request_hook"]:
                cep_func(response=response)
            return response

        @app.teardown_request
        def _teardown_request(exception=None):
            # 上下文扩展点之请求后(返回前无论异常)
            for cep_func in self.get_all_cep["teardown_request_hook"]:
                cep_func(exception=exception)
        self.app = app

    def __scanPlugins(self):
        """ 扫描插件目录 """
        #logging.info("Initialization Plugins Start, loadPlugins path: %s" %self.plugin_abspath)
        if os.path.exists(self.plugin_abspath):
            for package in os.listdir(self.plugin_abspath):
                _plugin_path = os.path.join(self.plugin_abspath, package)
                if os.path.isdir(_plugin_path) and os.path.isfile(os.path.join(_plugin_path, "__init__.py")):
                    #logging.info("find plugin package: {0}".format(package))
                    #: 动态加载模块(plugins.package): 可以查询自定义的信息, 并通过getPluginClass获取插件的类定义
                    plugin = __import__("{0}.{1}".format(self.plugins_folder, package), fromlist=[self.plugins_folder, ])
                    #: 检测插件信息
                    if hasattr(plugin, "__name__") and hasattr(plugin, "__version__") and hasattr(plugin, "__description__") and hasattr(plugin, "__author__") and hasattr(plugin, "getPluginClass"):
                        #: 获取插件信息
                        pluginInfo = self.__loadPluginInfo(package, plugin)
                        try:
                            #: 获取插件主类并实例化
                            p = plugin.getPluginClass()
                            i = p()
                        except Exception, e:
                            raise PluginError("Load Plugin Error")
                        #: 未启用时不执行后续方法
                        if pluginInfo["plugin_state"] != "enabled":
                            self.__plugins.append(pluginInfo)
                            return
                        #: 更新插件信息
                        pluginInfo.update(plugin_instance=i)
                        #
                        #: 运行插件主类的run方法
                        if hasattr(i, "run"):
                            i.run()
                        #: 注册模板扩展点
                        if hasattr(i, "register_tep"):
                            """ 模板扩展点要求：
                            返回格式：
                                return {tep_1: HTMLFile, tep_2: HTMLString}
                            解释说明：
                                1. 必须返回dict，key即tep是扩展点标识名，每个扩展点只能包含一种模板类型，要么html，要么string，都是要求str类型，其他类型触发异常
                                2. html模板类型后缀为`html、htm`认定为模板文件，将采用include方式引入
                            收录格式：
                                plugin_tep = {tep:dict(HTMLFile=str, HTMLString=str), tep...}
                            """
                            tep = i.register_tep()
                            #logging.info("The plugin {0} wants to register the following template extension points: {1}".format(package, tep))
                            if isinstance(tep, dict):
                                newTep = dict()
                                for event, tpl in tep.iteritems():
                                    if isinstance(tpl, (unicode, str)):
                                        if os.path.splitext(tpl)[-1] in (".html", ".htm"):
                                            if os.path.isfile(os.path.join(self.plugin_abspath, package, "templates", tpl)):
                                                newTep[event] = dict(HTMLFile=tpl)
                                            else:
                                                raise jinja2.TemplateNotFound("TEP Template File Not Found: %s" % tpl)
                                        else:
                                            newTep[event] = dict(HTMLString=jinja2.Markup(TemplateEventResult(tpl)))
                                    else:
                                        raise PluginError("Invaild TEP Format")
                                pluginInfo.update(plugin_tep=newTep)
                                logging.info("Register TEP Success")
                            else:
                                logging.error("Register TEP Failed, not a dict")
                        #: 注册上下文扩展点
                        if hasattr(i, "register_cep"):
                            cep = i.register_cep()
                            #logging.info("The plugin {0} wants to register the following context extension points: {1}".format(package, cep))
                            if isinstance(cep, dict):
                                pluginInfo.update(plugin_cep=cep)
                                logging.info("Register CEP Success")
                            else:
                                logging.error("Register CEP Failed, not a dict")
                        #: 注册蓝图扩展点
                        if hasattr(i, "register_bep"):
                            bep = i.register_bep()
                            #logging.info("The plugin {0} wants to register the following blueprint extension points: {1}".format(package, bep))
                            if isinstance(bep, dict):
                                pluginInfo.update(plugin_bep=bep)
                                logging.info("Register BEP Success")
                            else:
                                logging.error("Register BEP Failed, not a dict")
                        #: 注册信号扩展点`sep`
                        #: 加入全局插件中
                        if hasattr(i, "run") or hasattr(i, "register_tep") or hasattr(i, "register_cep") or hasattr(i, "register_bep"):
                            self.__plugins.append(pluginInfo)
                        else:
                            logging.error("The current class {0} does not have the `run` or `register_tep` or `register_cep` or `register_bep` method".format(i))
                    else:
                        del plugin

    def __loadPluginInfo(self, package, plugin):
        """ 组织插件信息
        @param package: 插件包名(位于plugins下的目录)，比如PluginDemo
        @param plugin: 动态加载的插件模块
        """
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
        # 插件状态首先读取`__state`状态值，优先级低于状态文件，ENABLED文件优先级低于DISABLED文件
        if os.path.isfile(os.path.join(self.plugin_abspath, package, "ENABLED")):
            plugin_state = "enabled"
        if os.path.isfile(os.path.join(self.plugin_abspath, package, "DISABLED")):
            plugin_state = "disabled"

        return {
            "plugin_name": plugin.__name__,
            "plugin_package_name": package,
            "plugin_description": plugin.__description__,
            "plugin_version": plugin.__version__,
            "plugin_author": plugin.__author__,
            "plugin_url": url,
            "plugin_license": license,
            "plugin_license_file": license_file,
            "plugin_readme_file": readme_file,
            "plugin_state": plugin_state,
            "plugin_tpl_path": os.path.join(self.plugins_folder, package, "templates"),
            "plugin_ats_path": os.path.join(self.plugins_folder, package, "assets"),
            "plugin_tep": {},
            "plugin_cep": {},
            "plugin_bep": {}
        }

    def __touch_file(self, filename):
        """创建空文件"""
        with open(filename, "w") as fd:
            fd.write("")

    def get_plugin_info(self, plugin_name):
        """获取插件信息"""
        if plugin_name:
            return next(i for i in self.get_all_plugins if i["plugin_name"] == plugin_name)

    def disable_plugin(self, plugin_name):
        """禁用插件"""
        plugin = self.get_plugin_info(plugin_name)
        ENABLED = os.path.join(self.plugin_abspath, plugin["plugin_package_name"], "ENABLED")
        if os.path.isfile(ENABLED):
            os.remove(ENABLED)
        self.__touch_file(os.path.join(self.plugin_abspath, plugin["plugin_package_name"], "DISABLED"))

    def enable_plugin(self, plugin_name):
        """启用插件"""
        plugin = self.get_plugin_info(plugin_name)
        DISABLED = os.path.join(self.plugin_abspath, plugin["plugin_package_name"], "DISABLED")
        if os.path.isfile(DISABLED):
            os.remove(DISABLED)
        self.__touch_file(os.path.join(self.plugin_abspath, plugin["plugin_package_name"], "ENABLED"))

    @property
    def get_all_plugins(self):
        """ 获取所有插件 """
        return self.__plugins

    @property
    def get_enabled_plugins(self):
        """ 获取所有启用的插件 """
        return [p for p in self.get_all_plugins if p["plugin_state"] == "enabled"]

    @property
    def get_all_tep(self):
        """模板扩展点, Template extension point
        # 返回dict，格式如下：
            {tep: dict(HTMLFile=[], HTMLString=[]), tep...}
        """
        teps = {}
        for p in self.get_enabled_plugins:
            # p是插件信息、e是扩展点名称、v是扩展点模板、f是模板类型、s是模板内容
            for e, v in p["plugin_tep"].iteritems():
                tep = teps.get(e, dict())
                tepHF = tep.get("HTMLFile", [])
                tepHS = tep.get("HTMLString", [])
                tepHF += [s for f, s in v.iteritems() if f == "HTMLFile"]
                tepHS += [s for f, s in v.iteritems() if f == "HTMLString"]
                teps[e] = dict(HTMLFile=tepHF, HTMLString=tepHS)
        return teps

    @property
    def get_all_cep(self):
        """上下文扩展点, Context extension point, 分别对应请求前、请求后(返回前):
        CEP: before_request_hook
        CEP: after_request_hook
        CEP: teardown_request_hook
        """
        return dict(
            before_request_hook=[plugin["plugin_cep"]["before_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("before_request_hook")],
            after_request_hook=[plugin["plugin_cep"]["after_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("after_request_hook")],
            teardown_request_hook=[plugin["plugin_cep"]["teardown_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("teardown_request_hook")],
        )

    @property
    def get_all_bep(self):
        """蓝图扩展点"""
        return [plugin["plugin_bep"] for plugin in self.get_enabled_plugins if plugin["plugin_bep"]]

    def get_tep(self, tep):
        """获取模板扩展点数据，请在模板中使用此函数，扩展点需要自己定义，方法如下：
        假设有一个扩展点名叫`tep`，只需要模板中启用自定义的扩展点:
        ```
        # 仅引入HTML文件
            {% for hf in get_tep('tep').HTMLFile %}{% include hf %}{% endfor %}
        # 仅渲染HTML元素
            {{ get_tep_string('tep') }}
        # 上面语句等价于下面
            {% for hs in get_tep('tep').HTMLString %}{{ hs }}{% endfor %}
        ```
        """
        return self.get_all_tep.get(tep) or dict(HTMLFile=[], HTMLString=[])

    def get_tep_string(self, tep):
        """获取模板扩展点HTMLString合并数据"""
        return jinja2.Markup("".join(self.get_tep(tep)["HTMLString"]))
