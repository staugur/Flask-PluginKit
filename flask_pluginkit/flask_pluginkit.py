# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.flask_pluginkit
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pluginkit: load and run plugins.

    :copyright: (c) 2018 by staugur.
    :license: BSD, see LICENSE for more details.
"""

import os
import re
import jinja2
import logging
from collections import deque
from flask import Response, render_template
from .exceptions import PluginError, CSSLoadError, DCPError, VersionError, DFPError, NotCallableError
from .utils import PY2, string_types, isValidSemver
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

logger = logging.getLogger(__name__)


class TemplateEventResult(list):

    def __init__(self, items):
        list.__init__(self, items)

    def __unicode__(self):
        return u''.join(map(str, self))

    def __str__(self):
        if PY2:
            return self.__unicode__().encode('utf-8')
        else:
            return self.__unicode__()


class PluginManager(object):
    """Flask Plugin Manager Extension, collects all plugins and maps the metadata to the plugin.

    The plugin is a directory, the directory name is the plugin name, and the plugin entry file is **__init__.py**,
    including __plugin_name__, __description__, __version__, __author__, __state__ and other plugin metadata.

    A meaningful plugin structure should look like this::

        plugins/
        ├── plugin1
        │   ├── __init__.py
        │   ├── LICENCE
        │   ├── README
        │   ├── static
        │   │   └── plugin1
        │   │       └── plugin1.css
        │   └── templates
        │       └── plugin1
        │           └── plugin1.html
        └── plugin2
            ├── __init__.py
            ├── LICENCE
            ├── README
            ├── static
            │   └── plugin2
            │       └── plugin2.css
            └── templates
                └── plugin2
                    └── plugin2.html

    """

    def __init__(self, app=None, plugins_base=None, plugins_folder="plugins", **kwargs):
        """Initializes the PluginManager. It is also possible to initialize the PluginManager via a factory.
        For example::

            from flask_pluginkit import Flask, PluginManager

            app = Flask(__name__)

            plugin_manager = PluginManager()
            plugin_manager.init_app(app)

        :param app: The flask application.

        :param plugins_base: str: The plugin folder where the plugins resides.

        :param plugins_folder: str: The base folder for the application. It is used to build the plugins package name.

        :param logger:

        :param stpl: Bool: Template sorting options

        :param stpl_reverse: Bool: Template sort reverse. Default False

        :param s3: str: Simple storage service, local or redis or empty

        :param s3_redis: str: If s3 is redis, thie key is redis url, such as redis://@localhost:6379/0

        :param plugin_packages: list,tuple: List of third-party plug-in package names
        """
        self.plugins_folder = plugins_folder
        self.plugins_abspath = os.path.join(plugins_base or os.getcwd(), self.plugins_folder)

        #: all locally stored plugins
        #:
        #: .. versionadded:: 0.1.4
        self.__plugins = []

        #: logging Logger instance
        #:
        #: .. versionadded:: 0.1.9
        self.logger = kwargs.get("logger", logger)

        #: Template sorting
        #:
        #: .. versionadded:: 1.2.0
        self.stpl = kwargs.get("stpl", False)
        self.stpl_reverse = kwargs.get("stpl_reverse", False)

        #: Simple storage service(s3), currently optional: local or redis.
        #: May increase in the future: memcache.
        #: You can also inherit :class:`~flask_pluginkit.BaseStorage`, custom storage interface.
        #:
        #: .. versionadded:: 1.3.0
        self.s3 = kwargs.get("s3")
        self.s3_redis = kwargs.get("s3_redis")

        #: Dynamic join point initialization, format::
        #: dict(event=deque())
        #:
        #: .. versionadded:: 2.1.0
        self._dcp_funcs = {}

        #: Third-party plugin package from pypi, format::
        #: [plugin1, plugin2, plugin...]
        #:
        #: .. versionadded:: 2.2.0
        self.plugin_packages = kwargs.get("plugin_packages", tuple())

        #: Dynamic function point initialization, format::
        #: dict(event=deque())
        #:
        #: .. versionadded:: 2.3.0
        self._dfp_funcs = {}

        #: initialize app via a factory
        #:
        #: .. versionadded:: 0.1.4
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.static_url_path = app.static_url_path
        self.__scanPlugins()

        #: Custom add multiple template folders
        app.jinja_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader([p["plugin_tpl_path"] for p in self.get_enabled_plugins if os.path.isdir(p["plugin_tpl_path"])]),
        ])

        #: Custom add more static folder, the requirement is the app initialized by :class:`~flask_pluginkit.Flask`.
        if isinstance(app.static_folder, list):
            app.static_folder += [p["plugin_ats_path"] for p in self.get_enabled_plugins if os.path.isdir(p["plugin_ats_path"])]

        #: Register template variable
        app.jinja_env.globals["emit_tep"] = self.emit_tep
        app.jinja_env.globals["emit_yep"] = self.emit_yep
        app.jinja_env.globals["emit_dcp"] = self.emit_dcp

        #: Register the blueprint extension point
        for bep in self.get_all_bep:
            app.register_blueprint(bep["blueprint"], url_prefix=bep["prefix"])

        #: Register request context extension points
        @app.before_request
        def _before_request():
            #: Before the request of the context extension point
            for cep_func in self.get_all_hep["before_request_hook"]:
                resp = cep_func()
                #: If the request is terminated, define the :class:`~flask.Response` using the likes of Response, and set is_before_request_return=True
                #:
                #: ..versionadded:: 1.0.1
                if isinstance(resp, Response) and hasattr(resp, "is_before_request_return") and resp.is_before_request_return is True:
                    return resp

        @app.after_request
        def _after_request(response):
            #: After the request of the context extension point (before return and no exception)
            for cep_func in self.get_all_hep["after_request_hook"]:
                cep_func(response=response)
            return response

        @app.teardown_request
        def _teardown_request(exception=None):
            #: After the request of the context extension point (no exception before return)
            for cep_func in self.get_all_hep["teardown_request_hook"]:
                cep_func(exception=exception)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['pluginkit'] = self
        app.plugin_manager = self
        self.app = app

    def __scanPlugins(self):
        """Scanning local plugin directories and third-party plugin packages.

        :returns: No return, but self.__plugins will be updated

        :raises: PluginError: raises an exception, maybe CSSLoadError, VersionError, based PluginError
        """
        self.logger.info("Initialization Plugins Start, local plugins path: %s, third party plugins: %s" % (self.plugins_abspath, self.plugin_packages))

        #: Load third-party plugins
        if self.plugin_packages and isinstance(self.plugin_packages, (list, tuple)):
            for package_name in self.plugin_packages:
                try:
                    plugin = __import__(package_name)
                except ImportError:
                    raise PluginError("ImportError for %s" % package_name)
                else:
                    plugin_abspath = os.path.dirname(os.path.abspath(plugin.__file__))
                    self.__loadPlugin(plugin, plugin_abspath, package_name)

        #: Load local plug-in directory
        if os.path.isdir(self.plugins_abspath) and os.path.isfile(os.path.join(self.plugins_abspath, "__init__.py")):
            for package_name in os.listdir(self.plugins_abspath):
                package_abspath = os.path.join(self.plugins_abspath, package_name)
                if os.path.isdir(package_abspath) and os.path.isfile(os.path.join(package_abspath, "__init__.py")):
                    self.logger.info("find plugin package: %s" % package_name)
                    #: Dynamic load module (plugins.package): you can query custom information and get the plugin's class definition through getPluginClass
                    plugin = __import__("{0}.{1}".format(self.plugins_folder, package_name), fromlist=[self.plugins_folder, ])
                    self.__loadPlugin(plugin, package_abspath, package_name)

    def __loadPlugin(self, plugin, package_abspath, package_name=None):
        """Load plugin, plugin is a python package with `__import__`.

        :param plugin: Dynamically loaded plugin modules

        :param package_abspath: The package absolute directory

        :param package_name: Plugin package names (directories under plugins), such as PluginDemo
        """
        #: Detection plugin information
        if hasattr(plugin, "__plugin_name__") and \
                hasattr(plugin, "__version__") and \
                hasattr(plugin, "__description__") and \
                hasattr(plugin, "__author__") and \
                hasattr(plugin, "getPluginClass"):
            try:
                #: Get plugin information
                pluginInfo = self.__getPluginInfo(plugin, package_abspath, package_name)
                #: Get the plugin main class and instantiate it
                p = plugin.getPluginClass()
                i = p()
            except Exception as e:
                raise e
            #: Subsequent methods are not executed when not enabled
            if pluginInfo["plugin_state"] != "enabled":
                self.__plugins.append(pluginInfo)
                return
            #: Update plugin information
            pluginInfo.update(plugin_instance=i)
            #: Run the *run* method of the plugin main class
            if hasattr(i, "run"):
                #: Run once only when loading
                i.run()
            #: Register the template extension point
            if hasattr(i, "register_tep"):
                """ Template extension point requirements:
                format:
                    plugin_tep = {tep:dict(HTMLFile=str, HTMLString=str), tep...}

                returns:
                    return {tep_1: HTMLFile(str), tep_2: HTMLString(str)}

                explanation:
                    1. This must be dict, where key means that tep is the extension point identifier,
                        and each extension point can contain only one template type,
                        either HTML or string, which requires STR type, and other types trigger exceptions
                    2. HTML template type suffix for `html` or `htm` as template file (the other as pure HTML code),
                        to be real, will adopt a `render_template` way rendering,
                        using template type can be specified when rendering and introduced to additional data
                """
                tep = i.register_tep()
                if isinstance(tep, dict):
                    newTep = dict()
                    for event, tpl in tep.items():
                        if isinstance(tpl, string_types):
                            if os.path.splitext(tpl)[-1] in (".html", ".htm"):
                                if os.path.isfile(os.path.join(pluginInfo["plugin_tpl_path"], tpl.split("@")[-1] if "@" in tpl and self.stpl is True else tpl)):
                                    newTep[event] = dict(HTMLFile=tpl)
                                else:
                                    raise jinja2.TemplateNotFound("TEP Template File Not Found: %s" % tpl)
                            else:
                                newTep[event] = dict(HTMLString=jinja2.Markup(tpl))
                        else:
                            raise PluginError("Invalid TEP Format")
                    pluginInfo.update(plugin_tep=newTep)
                    self.logger.info("Register TEP Success")
                else:
                    raise PluginError("Register TEP Failed, not a dict")
            #: Register context extension points
            if hasattr(i, "register_hep"):
                cep = i.register_hep()
                if isinstance(cep, dict):
                    pluginInfo.update(plugin_hep=cep)
                    self.logger.info("Register HEP Success")
                else:
                    raise PluginError("Register HEP Failed, not a dict")
            #: Register the blueprint extension point
            if hasattr(i, "register_bep"):
                bep = i.register_bep()
                if isinstance(bep, dict):
                    pluginInfo.update(plugin_bep=bep)
                    self.logger.info("Register BEP Success")
                else:
                    raise PluginError("Register BEP Failed, not a dict")
            #: Register the css extension point
            if hasattr(i, "register_yep"):
                """Register the plugin's cascading style sheet (CSS) file, requirements:
                format:
                    plugin_yep = {yep: css, yep: [css, ...]}

                returns:
                    return {yep: [css, ...], yep: [css, ...], ...}

                explanation:
                    1. This must be dict, and a key or an extension is the name of the page that CSS suggests to be introduced,
                        and each extension can be a single CSS or a set of CSS
                    2. CSS suffix must be `.css`, and real
                """
                yep = i.register_yep()
                if isinstance(yep, dict):
                    newYep = dict()
                    for event, css in yep.items():
                        if isinstance(css, string_types):
                            if os.path.isfile(os.path.join(pluginInfo["plugin_ats_path"], css)) and css.endswith(".css"):
                                newYep[event] = [self.static_url_path + "/" + css]
                            else:
                                raise CSSLoadError("YEP CSS File Is Invalid: %s" % css)
                        elif isinstance(css, (list, tuple)):
                            newCss = []
                            for ac in css:
                                if isinstance(ac, string_types) and os.path.isfile(os.path.join(pluginInfo["plugin_ats_path"], ac)) and ac.endswith(".css"):
                                    newCss.append(self.static_url_path + "/" + ac)
                                else:
                                    raise CSSLoadError("YEP CSS File Is Invalid: %s" % ac)
                            newYep[event] = newCss
                        else:
                            raise PluginError("Invalid YEP Format")
                    pluginInfo.update(plugin_yep=newYep)
                    self.logger.info("Register YEP Success")
                else:
                    raise PluginError("Register YEP Failed, not a dict")
            #: Register signal extension points`sep`
            #: Add to the global plugin
            if hasattr(i, "run") or hasattr(i, "register_tep") or hasattr(i, "register_hep") or hasattr(i, "register_bep") or hasattr(i, "register_yep"):
                self.__plugins.append(pluginInfo)
            else:
                self.logger.error("The current package does not have the `run` or `register_tep` or `register_hep` or `register_bep` or `register_yep` method")

    def __getPluginInfo(self, plugin, package_abspath, package_name):
        """ Organize plugin information.

        :returns: dict: plugin info
        """
        if not isValidSemver(plugin.__version__):
            raise VersionError("The plugin version does not conform to the standard named %s" % package_name)

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
        if os.path.isfile(os.path.join(package_abspath, "ENABLED")):
            plugin_state = "enabled"
        if os.path.isfile(os.path.join(package_abspath, "DISABLED")):
            plugin_state = "disabled"

        return {
            "plugin_name": plugin.__plugin_name__,
            "plugin_package_name": package_name,
            "plugin_package_abspath": package_abspath,
            "plugin_description": plugin.__description__,
            "plugin_version": plugin.__version__,
            "plugin_author": plugin.__author__,
            "plugin_url": url,
            "plugin_license": license,
            "plugin_license_file": license_file,
            "plugin_readme_file": readme_file,
            "plugin_state": plugin_state,
            "plugin_tpl_path": os.path.join(package_abspath, "templates"),
            "plugin_ats_path": os.path.join(package_abspath, "static"),
            "plugin_tep": {},
            "plugin_hep": {},
            "plugin_bep": {},
            "plugin_yep": {}
        }

    def __touch_file(self, filename):
        """Create an empty file"""
        with open(filename, "w") as fd:
            fd.write("")

    def get_plugin_info(self, plugin_name):
        """Get plugin information"""
        if plugin_name:
            for i in self.get_all_plugins:
                if i["plugin_name"] == plugin_name:
                    return i

    def disable_plugin(self, plugin_name):
        """Disable a plugin (that is, create a DISABLED empty file) and restart the application to take effect"""
        plugin = self.get_plugin_info(plugin_name)
        ENABLED = os.path.join(plugin["plugin_package_abspath"], "ENABLED")
        DISABLED = os.path.join(plugin["plugin_package_abspath"], "DISABLED")
        if os.path.isfile(ENABLED):
            os.remove(ENABLED)
        self.__touch_file(DISABLED)

    def enable_plugin(self, plugin_name):
        """Enable a plugin (that is, create a ENABLED empty file) and restart the application to take effect"""
        plugin = self.get_plugin_info(plugin_name)
        ENABLED = os.path.join(plugin["plugin_package_abspath"], "ENABLED")
        DISABLED = os.path.join(plugin["plugin_package_abspath"], "DISABLED")
        if os.path.isfile(DISABLED):
            os.remove(DISABLED)
        self.__touch_file(ENABLED)

    @property
    def get_all_plugins(self):
        """Get all plugins"""
        return self.__plugins

    @property
    def get_enabled_plugins(self):
        """Get all enabled plugins"""
        return [p for p in self.get_all_plugins if p["plugin_state"] == "enabled"]

    @property
    def get_all_tep(self):
        """Template extension point

        :returns: dict: {tep: dict(HTMLFile=[], HTMLString=[]), tep...}
        """
        teps = {}
        for p in self.get_enabled_plugins:
            for e, v in p["plugin_tep"].items():
                tep = teps.get(e, dict())
                tepHF = tep.get("HTMLFile", [])
                tepHS = tep.get("HTMLString", [])
                tepHF += [s for f, s in v.items() if f == "HTMLFile"]
                tepHS += [s for f, s in v.items() if f == "HTMLString"]
                teps[e] = dict(HTMLFile=tepHF, HTMLString=tepHS)
        return teps

    @property
    def get_all_hep(self):
        """Hook extension point.

        * before_request_hook, Before request (intercept requests are allowed)

        * after_request_hook, After request (no exception before return)

        * teardown_request_hook, After request (before return, with or without exception)
        """
        return dict(
            before_request_hook=[plugin["plugin_hep"]["before_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_hep"].get("before_request_hook")],
            after_request_hook=[plugin["plugin_hep"]["after_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_hep"].get("after_request_hook")],
            teardown_request_hook=[plugin["plugin_hep"]["teardown_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_hep"].get("teardown_request_hook")],
        )

    @property
    def get_all_bep(self):
        """Blueprint extension point"""
        return [plugin["plugin_bep"] for plugin in self.get_enabled_plugins if plugin["plugin_bep"]]

    @property
    def get_all_yep(self):
        """Cascading style sheet (CSS) extension points.

        :returns: dict: {yep: [css...], ...}
        """
        yeps = {}
        for p in self.get_enabled_plugins:
            for e, v in p["plugin_yep"].items():
                yep = yeps.get(e, []) + v
                yeps[e] = yep
        return yeps

    def emit_tep(self, tep, typ="all", **context):
        """Emit a event(with tep) and gets the template extension point data(html code).

        Please use this function in the template. The extension point needs to be defined by itself.

        Suppose you have an extension point named `tep`, only need to enable custom extension points in the template, for examples::

            #: It can render HTML code and files for an template extension point,
            #: or even pass in extra data at render time
            {{ emit_tep('tep', data=data) }}


        :param tep: str: Template extension point name, which is unique, a tep parsing result is list, within which can be HTML code and files

        :param typ: str: Render type, default value = "all"
                        all - render all, is default;
                        fil - render HTML file;
                        cod - render HTML code

        :param context: dict: Keyword parameter, additional data passed to the template

        :returns: html code with :class:`~jinja2.Markup`.
        """
        e = self.get_all_tep.get(tep) or dict(HTMLFile=[], HTMLString=[])
        #: Disposable template sequence
        if self.stpl is True:
            e["HTMLFile"] = map(lambda tpl: tpl.split('@')[-1], sorted(e['HTMLFile'], key=lambda x: x.split('@')[0], reverse=self.stpl_reverse))
            e["HTMLString"] = map(lambda tpl: tpl.split('@')[-1], sorted(e['HTMLString'], key=lambda x: x.split('@')[0], reverse=self.stpl_reverse))
        typ = "all" if not typ in ("fil", "cod") else typ
        mtf = jinja2.Markup("".join([render_template(i, **context) for i in e["HTMLFile"]]))
        mtc = jinja2.Markup("".join(e["HTMLString"]))
        if typ == "fil":
            return mtf
        elif typ == "cod":
            return mtc
        else:
            return mtf + mtc

    def emit_yep(self, yep):
        """Gets the css extension point data(html code).

        Please use this function between in the template, and the application needs to support multiple static folder functions,
        that is, the app initialized with :class:`~flask_pluginkit.Flask`.

        Assuming that the following templates need to be enabled for introducing CSS files using emit_metal, for examples::

            <!DOCTYPE html>
            <html>
            <head>
                <title></title>
                {{ emit_yep('yep') }}
            </head>
            <body>
                Your HTML Code
                {{ emit_tep('tep') }}
            </body>
            </html>

        :param yep: str: Name of css extension point, the only, a analytical results for the list or yep, can be used directly `link CSS` code

        :returns: html code with :class:`~jinja2.Markup`.
        """
        e = self.get_all_yep.get(yep) or []
        tpl = ''
        for css in e:
            tpl += '<link rel="stylesheet" type="text/css" href="%s" />' % css
        return jinja2.Markup(tpl)

    def storage(self, sf=None, args=None):
        """Common storage interface with :class:`~flask_pluginkit.LocalStorage` or :class:`~flask_pluginkit.RedisStorage`,
        sf is a custom storage interface classes, args is its parameters, highest priority.

        :param sf: class based :class:`~flask_pluginkit.BaseStorage`

        :param args: class init args

        :returns: class instance
        """
        from .utils import BaseStorage, LocalStorage, RedisStorage
        if sf and isinstance(sf, BaseStorage):
            return sf(args) if args else sf()
        if self.s3 == "local":
            return LocalStorage()
        elif self.s3 == "redis":
            return RedisStorage(self.s3_redis)

    def push_dcp(self, event, callback, position="right"):
        """Connect a dcp, push a function.

        :param event: str,unicode: A unique identifier name for dcp.

        :param callback: callable: Corresponding to the event to perform a function.

        :param position: The position of the insertion function, right(default) and left.

        :raises: DCPError,NotCallableError: raises an exception

        .. versionadded:: 2.1.0
        """
        if event and isinstance(event, string_types) and callable(callback) and position in ("left", "right"):
            if event in self._dcp_funcs:
                if position == "right":
                    self._dcp_funcs[event].append(callback)
                else:
                    self._dcp_funcs[event].appendleft(callback)
            else:
                self._dcp_funcs[event] = deque([callback])
        else:
            if not callable(callback):
                raise NotCallableError("The event %s cannot be called back" % event)
            raise DCPError("Invalid parameter")

    def emit_dcp(self, event, **context):
        """Emit a event(with dcp) and gets the dynamic join point data(html code).

        :param event: str,unicode: A unique identifier name for dcp.

        :param context: dict: Keyword parameter, additional data passed to the template

        :returns: html code with :class:`~jinja2.Markup`.

        .. versionadded:: 2.1.0
        """
        if event and isinstance(event, string_types) and event in self._dcp_funcs:
            results = []
            for f in self._dcp_funcs[event]:
                rv = f(**context)
                if rv is not None:
                    results.append(rv)
            del self._dcp_funcs[event]
            return jinja2.Markup(TemplateEventResult(results))
        else:
            return jinja2.Markup()

    def push_func(self, cuin, callback):
        """Push a function.

        :param cuin: str,unicode: Callback Unique Identifier Name.

        :param callback: callable: Corresponding to the cuin to perform a function.

        :raises: DFPError,NotCallableError: raises an exception

        .. versionadded:: 2.3.0
        """
        if cuin and isinstance(cuin, string_types) and callable(callback):
            if cuin in self._dfp_funcs:
                raise DFPError("The cuin already exists")
            else:
                self._dfp_funcs[cuin] = callback
        else:
            if not callable(callback):
                raise NotCallableError("The cuin %s cannot be called back" % cuin)
            raise DFPError("Invalid parameter")

    def emit_func(self, cuin, *args, **kwargs):
        """Emit a event(with dcp) and gets the dynamic join point data(html code).

        :param cuin: str,unicode: Callback Unique Identifier Name.

        :param args: list: Variable length parameter for cuin.

        :param kwargs: dict: Keyword parameter for cuin.

        :returns: The result of calling the function.

        .. versionadded:: 2.3.0
        """
        if cuin and isinstance(cuin, string_types):
            if cuin in self._dfp_funcs:
                f = self._dfp_funcs[cuin]
                return f(*args, **kwargs)
            else:
                raise DFPError("The cuin does not exist")
        else:
            raise DFPError("Invalid parameter")


def push_dcp(event, callback, position='right'):
    """Push a callable for :class:`~flask_pluginkit.PluginManager`, :func:`push_dcp`.

    Example usage::

        push_dcp('demo', lambda:'Hello dcp')

    .. versionadded:: 2.1.0
    """
    ctx = stack.top
    ctx.app.extensions.get('pluginkit').push_dcp(event, callback, position)
