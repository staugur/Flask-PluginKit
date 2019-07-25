# -*- coding: utf-8 -*-
"""
    flask_pluginkit.pluginkit
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Load and run plugins.

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

import os
import logging
from itertools import chain
from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Blueprint, render_template, render_template_string, \
    send_from_directory, abort, url_for, Markup, current_app
from .utils import isValidPrefix, isValidSemver, Attribution, DcpManager
from ._compat import string_types, iteritems, text_type, integer_types
from .exceptions import PluginError, VersionError, PEPError, TemplateNotFound
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class PluginManager(object):
    """Flask Plugin Manager Extension, collects all plugins and
    maps the metadata to the plugin.

    The plugin is a directory or a locally importable module,
    and the plugin entry file is **__init__.py**,
    including __plugin_name__, __version__, __author__ and other metadata.

    A meaningful plugin structure should look like this::

        plugins/
        ├── plugin1
        │   ├── __init__.py
        │   ├── LICENCE
        │   ├── README
        │   ├── static
        │   │   └── plugin1.css
        │   └── templates
        │       └── plugin1
        │           └── plugin1.html
        └── plugin2
            ├── __init__.py
            ├── LICENCE
            ├── README
            ├── static
            │   └── plugin2.css
            └── templates
                └── plugin2
                    └── plugin2.html

    Initializes the PluginManager. It is also possible to initialize
    the PluginManager via a factory::

        from flask_pluginkit import Flask, PluginManager
        app = Flask(__name__)
        pm = PluginManager()
        pm.init_app(app)

    :param app: flask application.

    :param plugins_base: plugin folder where the plugins resides.

    :param plugins_folder: base folder for the application.
                           It is used to build the plugins package name.

    :param logger: logging instance, for debug.

    :param stpl: turn on template sorting when the value is True.

    :param stpl_reverse: Collation, True descending, False ascending (Default).

    :param plugin_packages: list of third-party plugin packages.

    :param static_url_path: can be used to specify a different path for the
                            static files on the plugins. Defaults to the name
                            of the `static_endpoint` folder.

    :param static_endpoint: the endpoint name of plugins static files
                            that should be served at `static_url_path`.
                            Defaults to the ``'assets'``

    :param pluginkit_config: additional configuration can be used
                             in the template via :meth:`emit_config`.

    .. versionchanged:: 3.1.0
        Add a vep handler

    .. versionchanged:: 3.2.0
        Add filter handler, error handler, template context processor
    """

    def __init__(
        self,
        app=None,
        plugins_base=None,
        plugins_folder="plugins",
        **options
    ):
        """Receive initialization parameters and
        pass options to :meth:`init_app` method.
        """
        #: logging Logger instance
        self.logger = options.get("logger", logging.getLogger(__name__))

        #: Template sorting
        self.stpl = options.get("stpl", False)

        #: Template sort order, True descending, False ascending (default).
        self.stpl_reverse = options.get("stpl_reverse", False)

        #: Third-party plugin package
        self.plugin_packages = options.get("plugin_packages") or []
        if not isinstance(self.plugin_packages, (tuple, list)):
            raise PluginError("Invalid plugin_packages")

        #: Static endpoint
        self.static_endpoint = options.get("static_endpoint") or "assets"

        #: Static url prefix
        self.static_url_path = options.get("static_url_path") or \
            "/%s" % self.static_endpoint
        if not isValidPrefix(self.static_url_path):
            raise PluginError("Invalid static_url_path")

        #: Configuration Dictionary of Flask-PLuginKit in Project
        self.pluginkit_config = options.get("pluginkit_config") or {}
        if not isinstance(self.pluginkit_config, dict):
            raise PluginError("Invalid pluginkit_config")

        #: Plugins Extended Preprocessor
        self.__pet_handlers = {
            "tep": self._tep_handler,
            "hep": self._hep_handler,
            "bep": self._bep_handler,
            "vep": self._vep_handler,
            "errhandler": self._error_handler,
            "filter": self._filter_handler,
            "tcp": self._context_processor_handler,
        }

        #: Hook extension type handlers
        self.__het_allow_hooks = {
            "before_request": self.__before_request_hook_handler,
            "after_request": self.__after_request_hook_handler,
            "teardown_request": self.__teardown_request_hook_handler,
        }

        #: Dynamic Connection Point
        #:
        #: .. versionadded:: 3.2.0
        self._dcp_manager = DcpManager()

        #: All locally stored plugins
        self.__plugins = []

        #: Initialize app via a factory
        if app is not None:
            self.init_app(app, plugins_base, plugins_folder)

    def init_app(self, app, plugins_base=None, plugins_folder="plugins"):
        self.plugins_folder = plugins_folder
        self.plugins_abspath = os.path.join(
            plugins_base or getattr(app, 'root_path', os.getcwd()),
            self.plugins_folder
        )

        #: Scan and load plugins for :attr:`plugins_folder` and third-plugins
        self.logger.debug("Start plugins initialization, "
                          "local plugins path: %s, "
                          "third party plugins: %s" %
                          (self.plugins_abspath, self.plugin_packages))

        self.__scan_third_plugins()
        self.__scan_affiliated_plugins()
        # TODO Import single module plugin

        #: Analysis and run plugins. First, register template variable
        app.jinja_env.globals.update(
            emit_tep=self.emit_tep,
            emit_assets=self.emit_assets,
            emit_config=self.emit_config,
            emit_dcp=self._dcp_manager.emit
        )

        #: Custom add multiple template folders.
        #: Maybe you can use :class:`~jinja2.PackageLoader`.
        app.jinja_loader = ChoiceLoader([
            app.jinja_loader,
            FileSystemLoader(self.__get_valid_tpl),
        ])

        #: Add a static rule for plugins
        app.add_url_rule(self.static_url_path +
                         '/<string:plugin_name>/<path:filename>',
                         endpoint=self.static_endpoint,
                         view_func=self._send_plugin_static_file)

        #: Register the hook extension point processor
        for hep, handler in iteritems(self.__het_allow_hooks):
            _deco_func = getattr(app, hep)
            _deco_func(handler)

        #: Register the blueprint extension point
        for bep in self.get_enabled_beps:
            app.register_blueprint(bep["blueprint"], url_prefix=bep["prefix"])

        #: Register the viewfunc extension point
        #:
        #: .. versionadded:: 3.1.0
        for vep in self.get_enabled_veps:
            rule, viewfunc, endpoint, options = vep
            app.add_url_rule(rule, endpoint, viewfunc, **options)

        #: Register the template filters
        #:
        #: .. versionadded:: 3.2.0
        for tf in self.get_enabled_filters:
            if tf and tf[0] not in app.jinja_env.filters:
                app.add_template_filter(tf[-1], tf[0])

        #: Register the error handlers
        #:
        #: .. versionadded:: 3.2.0
        for errcode, errview in iteritems(self.get_enabled_errhandlers):
            app.register_error_handler(errcode, errview)

        #: Register the template context processors
        #:
        #: .. versionadded:: 3.2.0
        app.template_context_processors[None].append(
            lambda: {
                k: v
                for tcp in self.get_enabled_tcps
                for k, v in iteritems(tcp)
            }
        )

        #: register extension with app
        app.extensions = getattr(app, 'extensions', None) or {}
        app.extensions['pluginkit'] = self

    def __scan_third_plugins(self):
        if self.plugin_packages and isinstance(self.plugin_packages, (list, tuple)):
            for package_name in self.plugin_packages:
                self.logger.debug("find third plugin package: %s" %
                                  package_name)
                try:
                    plugin = __import__(package_name)
                except ImportError as e:
                    raise PluginError(e)
                else:
                    plugin_abspath = os.path.dirname(
                        os.path.abspath(plugin.__file__)
                    )
                    self.__load_plugin(plugin, plugin_abspath, package_name)

    def __scan_affiliated_plugins(self):
        if os.path.isdir(self.plugins_abspath) and \
                os.path.isfile(os.path.join(self.plugins_abspath, "__init__.py")):
            for package_name in os.listdir(self.plugins_abspath):
                package_abspath = os.path.join(
                    self.plugins_abspath, package_name)
                if os.path.isdir(package_abspath) and \
                        os.path.isfile(os.path.join(package_abspath, "__init__.py")):
                    self.logger.debug("find local plugin package: %s" %
                                      package_name)
                    #: Dynamic load module (plugins.package):
                    #: you can query custom information and get the plugin's
                    #: class definition through `register` function.
                    plugin = __import__("%s.%s" % (self.plugins_folder, package_name),
                                        fromlist=[self.plugins_folder, ])
                    self.__load_plugin(plugin, package_abspath, package_name)

    def __load_plugin(self, p_obj, package_abspath, package_name):
        """Try to load the plugin.

        :param p_obj: dynamically loaded plugin modules

        :param package_abspath: absolute path to the module directory

        :param package_name: the plugin package name

        :raises PEPError: Load plugin error

        .. versionchanged:: 3.0.1
            Do not check whether it is empty or not.
        """
        #: Detection plugin information
        if hasattr(p_obj, "__plugin_name__") and \
                hasattr(p_obj, "__version__") and \
                hasattr(p_obj, "__author__") and \
                hasattr(p_obj, "register"):
            #: Plugin extension point.
            #: It should return a dictionary type,
            #: and each element is an extension point, like this:
            #: {"tep":{}, "hep":{}, "bep":{}, "vep":[]}
            pets = p_obj.register()
            if isinstance(pets, dict):
                #: Get plugin information
                plugin_info = self._get_plugin_meta(
                    p_obj, package_abspath, package_name
                )
                if plugin_info.plugin_state == "enabled":
                    for pet, value in iteritems(pets):
                        try:
                            self.__pet_handlers[pet](plugin_info, value)
                        except KeyError:
                            raise PEPError("The plugin %s found an invalid "
                                           "extension point called %s" %
                                           (plugin_info.plugin_name, pet))
                self.__plugins.append(plugin_info)
            else:
                raise PEPError("The register returns the wrong type, "
                               "it should be a dict.")
        else:
            raise PEPError("The plugin metadata error")

    def _get_plugin_meta(self, p_obj, package_abspath, package_name):
        """ Organize plugin information.

        :returns: dict: plugin info
        """
        if not isValidSemver(p_obj.__version__):
            raise VersionError("The version number of %s is not compliant, "
                               "please refer to https://semver.org" %
                               package_name)

        try:
            plugin_state = p_obj.__state__
        except AttributeError:
            plugin_state = "enabled"

        #: The plugin state first reads the `__state__` value,
        #: the priority is lower than the state file,
        #: and the ENABLED file has a lower priority than the DISABLED file.
        if os.path.isfile(os.path.join(package_abspath, "ENABLED")):
            plugin_state = "enabled"
        if os.path.isfile(os.path.join(package_abspath, "DISABLED")):
            plugin_state = "disabled"

        return Attribution({
            "plugin_name": p_obj.__plugin_name__,
            "plugin_package_name": package_name,
            "plugin_package_abspath": package_abspath,
            "plugin_description": getattr(p_obj, "__description__", None),
            "plugin_version": p_obj.__version__,
            "plugin_author": p_obj.__author__,
            "plugin_url": getattr(p_obj, "__url__", None),
            "plugin_license": getattr(p_obj, "__license__", None),
            "plugin_license_file": getattr(p_obj, "__license_file__", None),
            "plugin_readme_file": getattr(p_obj, "__readme_file__", None),
            "plugin_state": plugin_state,
            "plugin_tpl_path": os.path.join(package_abspath, "templates"),
            "plugin_ats_path": os.path.join(package_abspath, "static"),
            "plugin_tep": {},
            "plugin_hep": {},
            "plugin_bep": {},
            "plugin_vep": [],
            "plugin_filter": [],
            "plugin_errhandler": {},
            "plugin_tcp": {},
        })

    def _tep_handler(self, plugin_info, tep_rule):
        """Template extension point handler.

        :param plugin_info: if tep is valid, will update it.

        :param tep_rule: the tep rule, like {tep_name: your_html_file_or_code}

                        1. This must be dict, where key means that tep is
                        the extension point identifier, and each extension point
                        can contain only one template type, either HTML or
                        string, which requires string,
                        and other types trigger exceptions.

                        2. HTML template type suffix for `html` or `htm`
                        as template file (the other as pure HTML code),
                        to be real, will adopt a `render_template` way rendering,
                        using template type can be specified when rendering
                        and introduced to additional data.

        :raises TemplateNotFound: if no template file is found.

        :raises PEPError: if tep rule or content is invalid.
        """
        if isinstance(tep_rule, dict):
            plugin_tep = {}
            for event, tpl in iteritems(tep_rule):
                if isinstance(tpl, string_types):
                    if os.path.splitext(tpl)[-1] in (".html", ".htm", ".xhtml"):
                        if os.path.isfile(os.path.join(
                            plugin_info.plugin_tpl_path,
                            tpl.split("@")[-1] if "@" in tpl and self.stpl is True else tpl)
                        ):
                            plugin_tep[event] = dict(fil=tpl)
                        else:
                            raise TemplateNotFound("TEP Template File "
                                                   "Not Found: %s" % tpl)
                    else:
                        #: Keep Unicode encoding
                        if not isinstance(tpl, text_type):
                            tpl = tpl.decode('utf-8')
                        plugin_tep[event] = dict(cod=tpl)
                else:
                    raise PEPError("The tep content is invalid for %s" %
                                   plugin_info.plugin_name)
            #: plugin_tep, like {tep_name:dict(HTMLFile=str, HTMLString=str)}
            plugin_info['plugin_tep'] = plugin_tep
            self.logger.debug("Register TEP Success")
        else:
            raise PEPError("The tep rule is invalid for %s, "
                           "it should be a dict." % plugin_info.plugin_name)

    def _hep_handler(self, plugin_info, hep_rule):
        """Hook extension point handler.

        :param hep_rule: like {hook: func}, the supporting hooks are as follows:

                        1. before_request, Before request
                        (intercept requests are allowed)

                        2. after_request, After request
                        (no exception before return)

                        3. teardown_request, After request
                        (before return, with or without exception)

        :raises PEPError: if hep rule or content is invalid.
        """
        if isinstance(hep_rule, dict):
            plugin_hep = {}
            for event, func in iteritems(hep_rule):
                if event in self.__het_allow_hooks.keys():
                    if callable(func):
                        plugin_hep[event] = func
                    else:
                        raise PEPError("The hep content cannot be called back "
                                       "for %s" % plugin_info.plugin_name)
                else:
                    raise PEPError("The hep type is invalid for %s" %
                                   plugin_info.plugin_name)
            #: plugin_hep, like {hep_name:callable, and so on}
            plugin_info['plugin_hep'] = plugin_hep
            self.logger.debug("Register HEP Success")
        else:
            raise PEPError("The hep rule is invalid for %s, "
                           "it should be a dict." % plugin_info.plugin_name)

    def _bep_handler(self, plugin_info, bep_rule):
        """Blueprint extension point handler.

        :param bep_rule: like {blueprint=, prefix=}

        :raises PEPError: if bep rule or content is invalid.
        """
        if isinstance(bep_rule, dict) and \
                "blueprint" in bep_rule and \
                "prefix" in bep_rule:
            try:
                bp = bep_rule["blueprint"]
                prefix = bep_rule["prefix"]
            except KeyError:
                raise PEPError("The bep rule is invalid for %s" %
                               plugin_info.plugin_name)
            if not isinstance(bp, Blueprint):
                raise PEPError("The bep blueprint is invalid for %s" %
                               plugin_info.plugin_name)
            if not isValidPrefix(prefix, allow_none=True):
                raise PEPError("The bep prefix is invalid for %s" %
                               plugin_info.plugin_name)
            #: TODO check and fix bp.root_path
            #: plugin_bep, like {blueprint:Blueprint instance, prefix='/xxx'}
            plugin_info['plugin_bep'] = bep_rule
            self.logger.debug("Register BEP Success")
        else:
            raise PEPError("The bep rule is invalid for %s, "
                           "it should be a dict." % plugin_info.plugin_name)

    def _vep_handler(self, plugin_info, vep_rule):
        """Viewfunc extension point handler.

        :param vep_rule: like [{rule=, view_func=, other options}, etc.]

        :raises PEPError: if bep rule or content is invalid.

        .. versionadded:: 3.1.0
        """
        if isinstance(vep_rule, dict):
            vep_rule = (vep_rule,)
        if isinstance(vep_rule, (list, tuple)):
            plugin_vep = []
            for options in vep_rule:
                try:
                    rule = options.pop("rule")
                    view_func = options.pop("view_func")
                except KeyError:
                    raise PEPError("The vep rule is invalid for %s" %
                                   plugin_info.plugin_name)
                else:
                    endpoint = options.pop("endpoint", None)
                    plugin_vep.append((rule, view_func, endpoint, options))
            #: like [(rule, view_func, endpoint), (), (), etc.]
            plugin_info['plugin_vep'] = plugin_vep
            self.logger.debug("Register VEP Success")
        else:
            raise PEPError("The vep rule is invalid for %s, it should be "
                           "a list or tuple." % plugin_info.plugin_name)

    def _filter_handler(self, plugin_info, filter_rule):
        """Template filter handler.

        :param filter_rule: like {filter_name=func,} or [func,]

        :raises PEPError: if filter rule or content is invalid.

        .. versionadded:: 3.2.0
        """
        if isinstance(filter_rule, (list, tuple)):
            _filter_rule = {}
            for f in filter_rule:
                if not callable(f):
                    raise PEPError("The filter named %s cannot be called." %
                                   plugin_info.plugin_name)
                else:
                    _filter_rule[f.__name__] = f
            filter_rule = _filter_rule
        if isinstance(filter_rule, dict):
            plugin_filter = []
            for name, func in iteritems(filter_rule):
                if callable(func):
                    plugin_filter.append((name, func))
                else:
                    raise PEPError("The filter named %s cannot be called." %
                                   plugin_info.plugin_name)
            plugin_info['plugin_filter'] = plugin_filter
        else:
            raise PEPError("The filter rule is invalid for %s, "
                           "it should be a dict." % plugin_info.plugin_name)

    def _error_handler(self, plugin_info, errhandler_rule):
        """Error code handler.

        :param errhandler_rule: like {err_code=func, }

        :raises PEPError: if error handler rule or content is invalid.

        .. versionadded:: 3.2.0
        """
        if isinstance(errhandler_rule, dict):
            for code, func in iteritems(errhandler_rule):
                if not isinstance(code, integer_types):
                    raise PEPError("The errhandler code is not interger for %s"
                                   % plugin_info.plugin_name)
                if not callable(func):
                    raise PEPError("The errhandler func is not called for %s"
                                   % plugin_info.plugin_name)
            plugin_info["plugin_errhandler"] = errhandler_rule
        else:
            raise PEPError("The error handler rule is invalid for %s, "
                           "it should be a dict." % plugin_info.plugin_name)

    def _context_processor_handler(self, plugin_info, processor_rule):
        """Template context processor(tcp) handler.

        :param processor_rule: like {var_name=var, func_name=func,}

        :raises PEPError: if tcp rule or content is invalid.

        .. versionadded:: 3.2.0
        """
        if isinstance(processor_rule, dict):
            plugin_info["plugin_tcp"] = processor_rule
        else:
            raise PEPError("The context processor rule is invalid for %s, "
                           "it should be a dict." % plugin_info.plugin_name)

    def __before_request_hook_handler(self):
        for func in self.get_enabled_heps["before_request"]:
            resp = func()
            if resp is not None:
                return resp

    def __after_request_hook_handler(self, response):
        for func in self.get_enabled_heps["after_request"]:
            func(response)
            #: TODO response = func(response)
        return response

    def __teardown_request_hook_handler(self, exception=None):
        for func in self.get_enabled_heps["teardown_request"]:
            func(exception)

    @property
    def get_all_plugins(self):
        """Get all plugins, enabled and disabled"""
        return self.__plugins

    @property
    def get_enabled_plugins(self):
        """Get all enabled plugins"""
        return [p for p in self.get_all_plugins if p.plugin_state == "enabled"]

    @property
    def __get_valid_tpl(self):
        return [
            p.plugin_tpl_path
            for p in self.get_enabled_plugins
            if os.path.isdir(p.plugin_tpl_path)
        ]

    @property
    def get_enabled_teps(self):
        """Get all tep of the enabled plugins.

        :returns: dict like {tep_1: dict(fil=[], cod=[]), tep_n...}
        """
        teps = {}
        for p in self.get_enabled_plugins:
            for e, v in iteritems(p.plugin_tep):
                tep = teps.get(e, dict())
                tepHF = tep.get("fil", [])
                tepHS = tep.get("cod", [])
                tepHF += [s for f, s in v.items() if f == "fil"]
                tepHS += [s for f, s in v.items() if f == "cod"]
                teps[e] = dict(fil=tepHF, cod=tepHS)
        return teps

    @property
    def get_enabled_heps(self):
        """Get all hep of the enabled plugins.

        :returns: dictionary with nested tuples, like {hook:[]}
        """
        heps = {}
        for hep in self.__het_allow_hooks.keys():
            heps[hep] = [p.plugin_hep[hep] for p in self.get_enabled_plugins
                         if hep in p.plugin_hep.keys()]
        return heps

    @property
    def get_enabled_beps(self):
        """Get all bep of the enabled plugins.

        :returns: List of nested dictionaries, like [{blueprint=,prefix=},]
        """
        return [p.plugin_bep for p in self.get_enabled_plugins if p.plugin_bep]

    @property
    def get_enabled_veps(self):
        """Get all vep for the enabled plugins.

        :returns: List of nested tuples, like [(path, view_func),]

        .. versionadded:: 3.1.0
        """
        return [
            rule
            for p in self.get_enabled_plugins
            for rule in p.plugin_vep
            if p.plugin_vep
        ]

    @property
    def get_enabled_filters(self):
        """Get all template filters for the enabled plugins.

        :returns: List of nested tuples, like [(filter_name, filter_func),]

        .. versionadded:: 3.2.0
        """
        return list(chain.from_iterable([
            p.plugin_filter
            for p in self.get_enabled_plugins
            if p.plugin_filter
        ]))

    @property
    def get_enabled_errhandlers(self):
        """Get all error handlers for the enabled plugins.

        :returns: dict, like {code: view_func,}

        .. versionadded:: 3.2.0
        """
        return {
            k: v
            for p in self.get_enabled_plugins
            for k, v in iteritems(p.plugin_errhandler)
            if p.plugin_errhandler
        }

    @property
    def get_enabled_tcps(self):
        """Get all template context processors for the enabled plugins.

        :returns: List of Nested Dictionaries, like [{name:var_or_func},]

        .. versionadded:: 3.2.0
        """
        return [
            {k: v}
            for p in self.get_enabled_plugins
            for k, v in iteritems(p.plugin_tcp)
            if p.plugin_tcp
        ]

    def get_plugin_info(self, plugin_name):
        """Get plugin information from all plugins"""
        try:
            return next(
                (p for p in self.get_all_plugins
                 if p.plugin_name == plugin_name)
            )
        except StopIteration:
            raise PluginError("No plugin named %s was found" % plugin_name)

    def disable_plugin(self, plugin_name):
        """Disable a plugin (that is, create a DISABLED empty file)
        and restart the application to take effect.
        """
        p = self.get_plugin_info(plugin_name)
        ENABLED = os.path.join(p.plugin_package_abspath, "ENABLED")
        DISABLED = os.path.join(p.plugin_package_abspath, "DISABLED")
        if os.path.isfile(ENABLED):
            os.remove(ENABLED)
        self.__touch_file(DISABLED)

    def enable_plugin(self, plugin_name):
        """Enable a plugin (that is, create a ENABLED empty file)
        and restart the application to take effect.
        """
        p = self.get_plugin_info(plugin_name)
        ENABLED = os.path.join(p.plugin_package_abspath, "ENABLED")
        DISABLED = os.path.join(p.plugin_package_abspath, "DISABLED")
        if os.path.isfile(DISABLED):
            os.remove(DISABLED)
        self.__touch_file(ENABLED)

    def __touch_file(self, filename):
        """Create an empty file"""
        with open(filename, "w") as fd:
            fd.write("")

    def _send_plugin_static_file(self, plugin_name, filename):
        try:
            p = self.get_plugin_info(plugin_name)
        except PluginError:
            return abort(404)
        else:
            return send_from_directory(p.plugin_ats_path, filename)

    def emit_tep(self, tep, typ="all", **context):
        """Emit a tep and get the tep data(html code) with
        :func:`flask.render_template` or :func:`flask.render_template_string`

        Please use this function in the template file or code.
        The emit_tep needs to be defined by yourself.
        It can render HTML code and files for a tep, or even
        pass in extra data at render time.

        Suppose you have a tep named `hello`, only need to enable
        custom extension points in the template context, eg::

            {{ emit_tep("hello", context="world") }}

        :param tep: Template extension point name, it is the only one.
                    A tep parsing result is list, within which can be
                    HTML code and files, or one of them.

        :param typ: Render type, default is all.

                    all - render HTML file and code;

                    fil - render HTML file only;

                    cod - render HTML code only.

        :param context: Keyword params, additional data passed to the template

        :returns: html code with :class:`~flask.Markup`.
        """
        tep_result = self.get_enabled_teps.get(tep) or dict(cod=[], fil=[])
        #: Disposable template sequence
        if self.stpl is True:
            def _sort_refresh(tep_typ):
                func = sorted(tep_result[tep_typ],
                              key=lambda x: x.split('@')[0],
                              reverse=self.stpl_reverse)
                return map(lambda tpl: tpl.split('@')[-1], func)
            tep_result["fil"] = _sort_refresh("fil")
            tep_result["cod"] = _sort_refresh("cod")

        mtf = Markup("".join(
            [render_template(i, **context) for i in tep_result["fil"]]
        ))
        mtc = Markup("".join(
            [render_template_string(i, **context) for i in tep_result["cod"]]
        ))

        typ = "all" if not typ in ("fil", "cod") else typ
        if typ == "fil":
            return mtf
        elif typ == "cod":
            return mtc
        else:
            return mtf + mtc

    def emit_assets(self, plugin_name, filename):
        """Get the static file in template context.
        This global function, which can be used directly in the template,
        is used to quickly reference the static resources of the plugin.

        In addition, static resources can still pass through the blueprint,
        but `emit_assets` can be used if there is no blueprint.

        Of course, you can also use :func:`flask.url_for` instead.

        If filename ends with `.css`, then this function will
        return the `link` code, like this::

            <link rel="stylesheet" href="/assets/plugin/css/demo.css">

        If filename ends with `.js`, then this function will
        return the `script` code, like this::

            <script type="text/javascript" src="/assets/plugin/js/demo.js"></script>

        Other types of files, only return file url path segment, like this::

            /assets/plugin/img/logo.png
            /assets/plugin/attachment/test.zip

        The following is a mini example::

            <!DOCTYPE html>
            <html>
            <head>
                <title>Hello World</title>
                {{ emit_assets('demo','css/demo.css') }}
            </head>
            <body>
                <div class="logo">
                    <img src="{{ emit_assets('demo', 'img/logo.png') }}">
                </div>
            </body>
            </html>

        :param plugin_name: name of the plugin, which is `__plugin_name__`

        :param filename: file name in the static directory of the plugin package

        :returns: html code with :class:`~flask.Markup`.
        """
        uri = url_for(
            self.static_endpoint,
            plugin_name=plugin_name,
            filename=filename
        )
        if filename.endswith(".css"):
            uri = '<link rel="stylesheet" href="%s">' % uri
        elif filename.endswith(".js"):
            uri = '<script type="text/javascript" src="%s"></script>' % uri
        return Markup(uri)

    def emit_config(self, conf_name):
        """Get configuration information in the template context, like config."""
        try:
            return self.pluginkit_config[conf_name]
        except KeyError:
            return current_app.config.get(conf_name)


def push_dcp(event, callback, position='right'):
    """Push a callable for with :meth:`~flask_pluginkit.utils.DcpManager.push`.

    Example usage::

        push_dcp('demo', lambda:'Hello dcp')

    .. versionadded:: 3.2.0
    """
    ctx = stack.top
    ctx.app.extensions.get('pluginkit')._dcp_manager.push(
        event,
        callback,
        position
    )
