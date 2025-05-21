# -*- coding: utf-8 -*-
"""
    flask_pluginkit.pluginkit
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Load and run plugins.

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

import logging
from os import getcwd, listdir, remove
from os.path import join, dirname, abspath, isdir, isfile, splitext
from itertools import chain
from jinja2 import ChoiceLoader, FileSystemLoader
from flask import (
    Blueprint,
    render_template,
    render_template_string,
    send_from_directory,
    abort,
    url_for,
    current_app,
)
from markupsafe import Markup
from .utils import isValidPrefix, isValidSemver, Attribution, DcpManager
from ._compat import string_types, iteritems, text_type
from .exceptions import PluginError, VersionError, PEPError, TemplateNotFound

from typing import Optional, Dict, Union, Any, Sequence, List, Callable
from flask import Flask
from logging import Logger

META = Attribution[Dict[str, Union[None, str, list, dict]]]


class PluginManager(object):
    """Flask Plugin Manager Extension, collects all plugins and
    maps the metadata to the plugin.

    The plugin is a directory or a locally importable module,
    and the plugin entry file is __init__.py,
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

    :param Flask app: flask application.

    :param str plugins_base: plugin folder where the plugins resides.

    :param str plugins_folder: base folder for the application.
                               It is used to build the plugins package name.

    :param Logger logger: logging instance, for debug.

    :param str stpl: turn on template sorting when the value is True, ASC, DESC.
                     Sorting rules can be used, DESC or ASC(default).

    :param str plugin_packages: list of third-party plugin packages.

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

    .. versionchanged:: 3.3.1
        Add try_compatible, if True, it will try to load old version

    .. versionchanged:: 3.4.0
        Add hep named before_first_request.

    .. versionchanged:: 3.4.0
        The param ``stpl`` allows to be set to `asc` or `desc`, respectively,
        ascending, descending, which will also open the template sorting.
        So, the param ``stpl_reverse`` will be deprecated.

    .. versionchanged:: 3.5.0
        Add ``cvep`` feature for beta.

    .. deprecated:: 3.7.0
        Ready to remove ``stpl_reverse`` and ``try_compatible``
        in the next minor version, if it is still used,
        a warning will be issued.

    .. versionchanged:: 3.7.0
        Add ``p3`` feature for beta.

    .. deprecated:: 3.7.2
        Remove `before_first_request` hep

    .. deprecated:: 3.8.0
        Remove `stpl_reverse` and `try_compatible` param.
    """

    def __init__(
        self,
        app: Optional[Flask] = None,
        plugins_base: Optional[str] = None,
        plugins_folder: Optional[str] = "plugins",
        **options: Dict[str, Any],
    ):
        """Receive initialization parameters and
        pass options to :meth:`init_app` method.
        """
        #: logging Logger instance
        self.logger: Logger = options.get("logger", logging.getLogger(__name__))

        #: Template sorting
        self.stpl: Union[str, bool] = options.get("stpl", False)

        #: Template sort order, True descending, False ascending (default).
        if self.stpl in ("asc", "desc", "ASC", "DESC"):
            self.stpl = True
            self.stpl_reverse: bool = False if self.stpl in ("asc", "ASC") else True

        #: Third-party plugin package
        self.plugin_packages = options.get("plugin_packages") or []
        if not isinstance(self.plugin_packages, (tuple, list)):
            raise PluginError("Invalid plugin_packages")

        #: Static endpoint
        self.static_endpoint: str = options.get("static_endpoint") or "assets"

        #: Static url prefix
        self.static_url_path: str = (
            options.get("static_url_path") or f"/{self.static_endpoint}"
        )
        if not isValidPrefix(self.static_url_path):
            raise PluginError("Invalid static_url_path")

        #: Configuration Dictionary of Flask-PLuginKit in Project
        self.pluginkit_config: Dict[str, Any] = options.get("pluginkit_config") or {}
        if not isinstance(self.pluginkit_config, dict):
            raise PluginError("Invalid pluginkit_config")

        #: Plugins Extended Processor
        self.__pet_handlers: Dict[str, Callable] = {
            "tep": self._tep_handler,
            "hep": self._hep_handler,
            "bep": self._bep_handler,
            "vep": self._vep_handler,
            "cvep": self._cvep_handler,
            "errhandler": self._error_handler,
            "filter": self._filter_handler,
            "tcp": self._context_processor_handler,
            "p3": self._p3_handler,
        }

        #: Hook extension type handlers
        self.__het_allow_hooks: Dict[str, Callable] = {
            "before_request": self.__before_request_hook_handler,
            "after_request": self.__after_request_hook_handler,
            "teardown_request": self.__teardown_request_hook_handler,
        }

        #: Dynamic Connection Point
        #:
        #: .. versionadded:: 3.2.0
        self._dcp_manager = DcpManager()

        #: All locally stored plugins
        self.__plugins: List = []

        #: Initialize app via a factory
        if app is not None:
            self.init_app(app, plugins_base, plugins_folder)

    def init_app(
        self,
        app: Flask,
        plugins_base: Optional[str] = None,
        plugins_folder: Optional[str] = "plugins",
    ):
        self.plugins_folder: str = plugins_folder
        self.plugins_abspath: str = join(
            plugins_base or getattr(app, "root_path", getcwd()),
            self.plugins_folder,
        )

        #: Scan and load plugins for :attr:`plugins_folder` and third-plugins
        self.logger.debug(
            "Start plugins initialization, local plugins path: %s, third party"
            "-plugins: %s" % (self.plugins_abspath, self.plugin_packages)
        )
        self.__scan_third_plugins()
        self.__scan_affiliated_plugins()

        #: Try to update `self.__plugins`
        #:
        #: ..versionadded:: 3.7.0
        self.__preprocess_all_plugins()

        #: Analysis and run plugins. First, register template variable
        app.jinja_env.globals.update(
            emit_tep=self.emit_tep,
            emit_assets=self.emit_assets,
            emit_config=self.emit_config,
            emit_dcp=self._dcp_manager.emit,
        )

        #: Custom add multiple template folders.
        #: Maybe you can use :class:`~jinja2.PackageLoader`.
        app.jinja_loader = ChoiceLoader(
            [
                app.jinja_loader,
                FileSystemLoader(self.__get_valid_tpl),
            ]
        )

        #: Add a static rule for plugins
        app.add_url_rule(
            self.static_url_path + "/<string:plugin_name>/<path:filename>",
            endpoint=self.static_endpoint,
            view_func=self._send_plugin_static_file,
        )

        #: Register the hook extension point processor
        for hep, handler in iteritems(self.__het_allow_hooks):
            _deco_func = getattr(app, hep)
            _deco_func(handler)

        #: Register the blueprint extension point
        #:
        #: .. versionchanged:: 3.6.2
        #:     flask 2.0 nested blueprints,
        #:     but only blueprints of other plugins can be nested
        _plugin_bps = {}  # {name:{blueprint}, }
        _nested_bps = {}  # {parent:[{blueprint}, ], }
        for bep in self.get_enabled_beps:
            bp = bep["blueprint"]
            parent = bep.get("parent")
            if parent:
                _nested_bps.setdefault(parent, []).append(bep)
            else:
                _plugin_bps[bp.name] = bep
        for parent, beps in iteritems(_nested_bps):
            if parent not in _plugin_bps:
                raise PEPError("No parent blueprint found named %s" % parent)
            pbp = _plugin_bps[parent]["blueprint"]
            for bep in beps:
                bp = bep["blueprint"]
                prefix = bep["prefix"]
                pbp.register_blueprint(bp, url_prefix=prefix)
        for bep in _plugin_bps.values():
            bp = bep["blueprint"]
            prefix = bep["prefix"]
            app.register_blueprint(bp, url_prefix=prefix)

        #: Register the viewfunc extension point
        #:
        #: .. versionadded:: 3.1.0
        #:
        #: .. versionchanged:: 3.6.0
        #:     allow blueprint name
        for vep in self.get_enabled_veps:
            rule, viewfunc, endpoint, options, _bp = vep
            if _bp:
                if _bp in app.blueprints:
                    s = app.blueprints[_bp].make_setup_state(app, {})
                    s.add_url_rule(rule, endpoint, viewfunc, **options)
                else:
                    raise PEPError(
                        "The required blueprint({}) was not found when "
                        "registering vep with {}".format(_bp, rule)
                    )
            else:
                app.add_url_rule(rule, endpoint, viewfunc, **options)

        #: Register the class-based view extension point
        #:
        #: .. versionadded:: 3.5.0
        for cvep in self.get_enabled_cveps:
            viewclass, options = cvep
            viewclass.register(app, **options)

        #: Register the template filters
        #:
        #: .. versionadded:: 3.2.0
        for tf in self.get_enabled_filters:
            if tf and tf[0] not in app.jinja_env.filters:
                app.add_template_filter(tf[-1], tf[0])

        #: Register the error handlers
        #:
        #: .. versionadded:: 3.2.0
        for err_code_exc, errview in self.get_enabled_errhandlers:
            app.register_error_handler(err_code_exc, errview)

        #: Register the template context processors
        #:
        #: .. versionadded:: 3.2.0
        app.template_context_processors[None].append(
            lambda: {k: v for tcp in self.get_enabled_tcps for k, v in iteritems(tcp)}
        )

        #: register extension with app
        app.extensions = getattr(app, "extensions", None) or {}
        app.extensions["pluginkit"] = self

    def __scan_third_plugins(self):
        if self.plugin_packages and isinstance(self.plugin_packages, (list, tuple)):
            for package_name in self.plugin_packages:
                self.logger.debug("find third plugin package: %s" % package_name)
                try:
                    plugin = __import__(package_name)
                except ImportError as e:
                    raise PluginError(e)
                else:
                    plugin_abspath = dirname(abspath(plugin.__file__))
                    self.__load_plugin(plugin, plugin_abspath, package_name)

    def __scan_affiliated_plugins(self):
        if isdir(self.plugins_abspath) and isfile(
            join(self.plugins_abspath, "__init__.py")
        ):
            for package_name in listdir(self.plugins_abspath):
                package_abspath = join(self.plugins_abspath, package_name)
                if isdir(package_abspath) and isfile(
                    join(package_abspath, "__init__.py")
                ):
                    self.logger.debug("find local plugin package: %s" % package_name)
                    #: Dynamic load module (plugins.package):
                    #: you can query custom information and get the plugin's
                    #: class definition through `register` function.
                    plugin = __import__(
                        "%s.%s" % (self.plugins_folder, package_name),
                        fromlist=[
                            self.plugins_folder,
                        ],
                    )
                    self.__load_plugin(plugin, package_abspath, package_name)

    def __load_plugin(self, p_obj, package_abspath, package_name):
        """Try to load the plugin.

        :param p_obj: dynamically loaded plugin modules

        :param package_abspath: absolute path to the module directory

        :param package_name: the plugin package name

        :raises PEPError: Load plugin error

        :raises PluginError: Compatibility loading error

        .. versionchanged:: 3.0.1
            Do not check whether it is empty or not.

        .. versionchanged:: 3.3.1
            Read and convert the method of getPluginClass in the old version.
        """
        #: Detection plugin information
        if (
            hasattr(p_obj, "__plugin_name__")
            and hasattr(p_obj, "__version__")
            and hasattr(p_obj, "__author__")
            and hasattr(p_obj, "register")
        ):
            #: Plugin extension point.
            #: It should return a dictionary type,
            #: and each element is an extension point, like this:
            #: {"tep":{}, "hep":{}, "bep":{}, "vep":[]}
            pets = p_obj.register()
            if isinstance(pets, dict):
                #: Get plugin information
                plugin_info: META = self._get_plugin_meta(
                    p_obj, package_abspath, package_name
                )
                if plugin_info.plugin_state == "enabled":
                    for pet, value in iteritems(pets):
                        try:
                            self.__pet_handlers[pet](plugin_info, value)
                        except KeyError:
                            raise PEPError(
                                "The plugin %s found an invalid "
                                "extension point called %s"
                                % (plugin_info.plugin_name, pet)
                            )
                self.__plugins.append(plugin_info)
            else:
                raise PEPError(
                    "When loading %s, the register returns the wrong type, "
                    "it should be a dict."
                    % getattr(p_obj, "__plugin_name__", package_name)
                )
        else:
            raise PEPError(
                "The plugin %s metadata error"
                % getattr(p_obj, "__plugin_name__", package_name)
            )

    def _get_plugin_meta(self, p_obj, package_abspath, package_name) -> META:
        """Organize plugin information.

        :returns: dict: plugin info

        .. versionchanged:: 3.4.0
            plugin_errhandler format change: {} -> []

        .. versionchanged:: 3.5.0
            add plugin_cvep

        .. versionchanged:: 3.7.0
            add plugin_p3

        .. versionchanged:: 3.9.0
            add proxy
        """
        if not isValidSemver(p_obj.__version__):
            raise VersionError(
                "The version number of %s is not compliant, "
                "please refer to https://semver.org" % package_name
            )

        try:
            plugin_state = p_obj.__state__
        except AttributeError:
            plugin_state = "enabled"

        #: The plugin state first reads the `__state__` value,
        #: the priority is lower than the state file,
        #: and the ENABLED file has a lower priority than the DISABLED file.
        if isfile(join(package_abspath, "ENABLED")):
            plugin_state = "enabled"
        if isfile(join(package_abspath, "DISABLED")):
            plugin_state = "disabled"

        return Attribution(
            {
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
                "plugin_tpl_path": join(package_abspath, "templates"),
                "plugin_ats_path": join(package_abspath, "static"),
                "plugin_tep": {},
                "plugin_hep": {},
                "plugin_bep": {},
                "plugin_vep": [],
                "plugin_cvep": [],
                "plugin_filter": [],
                "plugin_errhandler": [],
                "plugin_tcp": {},
                "plugin_p3": {},
                "__proxy__": p_obj,
            }
        )

    def _tep_handler(self, plugin_info: META, tep_rule: Dict[str, str]):
        """Template extension point handler.

        :param META plugin_info: if tep is valid, will update it.

        :param dict tep_rule: look like {tep_name: your_html_file_or_code}

                        1. This must be dict, where key means that tep is
                        the extension point identifier, and each extension
                        point can contain only one template type, either HTML
                        or string, which requires string,
                        and other types trigger exceptions.

                        2. HTML template type suffix for `html` or `htm`
                        as template file (the other as pure HTML code), to be
                        real, will adopt a `render_template` way rendering,
                        using template type can be specified when rendering
                        and introduced to additional data.

        :raises TemplateNotFound: if no template file is found.

        :raises PEPError: if tep rule or content is invalid.
        """
        if isinstance(tep_rule, dict):
            plugin_tep = {}
            for event, tpl in iteritems(tep_rule):
                if isinstance(tpl, string_types):
                    if splitext(tpl)[-1] in (".html", ".htm", ".xhtml"):
                        if isfile(
                            join(
                                plugin_info.plugin_tpl_path,
                                (
                                    tpl.split("@")[-1]
                                    if "@" in tpl and self.stpl is True
                                    else tpl
                                ),
                            )
                        ):
                            plugin_tep[event] = dict(fil=tpl)
                        else:
                            raise TemplateNotFound(
                                "TEP Template File Not Found: %s" % tpl
                            )
                    else:
                        #: Keep Unicode encoding
                        if not isinstance(tpl, text_type):
                            tpl = tpl.decode("utf-8")
                        plugin_tep[event] = dict(cod=tpl)
                else:
                    raise PEPError(
                        "The tep content is invalid for %s" % plugin_info.plugin_name
                    )
            #: result look like {tep_name:dict(HTMLFile=str, HTMLString=str)}
            plugin_info["plugin_tep"] = plugin_tep
            self.logger.debug("Register TEP Success")
        else:
            raise PEPError(
                "The tep rule is invalid for %s, "
                "it should be a dict." % plugin_info.plugin_name
            )

    def _hep_handler(self, plugin_info: META, hep_rule: Dict[str, Callable]):
        """Hook extension point handler.

        :param hep_rule: look like {hook: func}, the supporting hooks:

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
                        raise PEPError(
                            "The hep content cannot be called back "
                            "for %s" % plugin_info.plugin_name
                        )
                else:
                    raise PEPError(
                        "The hep type is invalid for %s" % plugin_info.plugin_name
                    )
            #: plugin_hep, look like {hep_name:callable, and so on}
            plugin_info["plugin_hep"] = plugin_hep
            self.logger.debug("Register HEP Success")
        else:
            raise PEPError(
                "The hep rule is invalid for %s, "
                "it should be a dict." % plugin_info.plugin_name
            )

    def _bep_handler(self, plugin_info: META, bep_rule: Dict[str, str]):
        """Blueprint extension point handler.

        :param bep_rule: look like {blueprint=, prefix=, parent=}

        :raises PEPError: if bep rule or content is invalid.
        """
        if (
            isinstance(bep_rule, dict)
            and "blueprint" in bep_rule
            and "prefix" in bep_rule
        ):
            try:
                bp = bep_rule["blueprint"]
                prefix = bep_rule["prefix"]
            except KeyError:
                raise PEPError(
                    "The bep rule is invalid for %s" % plugin_info.plugin_name
                )
            if not isinstance(bp, Blueprint):
                raise PEPError(
                    "The bep blueprint is invalid for %s" % plugin_info.plugin_name
                )
            if not isValidPrefix(prefix, allow_none=True):
                raise PEPError(
                    "The bep prefix is invalid for %s" % plugin_info.plugin_name
                )
            #: result look like {blueprint:Blueprint instance, prefix='/xxx'}
            plugin_info["plugin_bep"] = bep_rule
            self.logger.debug("Register BEP Success")
        else:
            raise PEPError(
                "The bep rule is invalid for %s, "
                "it should be a dict." % plugin_info.plugin_name
            )

    def _vep_handler(
        self,
        plugin_info: META,
        vep_rule: Union[
            Dict[str, Union[str, Callable]], Sequence[Dict[str, Union[str, Callable]]]
        ],
    ):
        """Viewfunc extension point handler.

        :param vep_rule: look like [{rule=, view_func=, _blurprint=, opts}, ]

        :raises PEPError: if vep rule or content is invalid.

        .. versionadded:: 3.1.0

        .. versionchanged:: 3.6.0
            Allow adding vep on blueprint
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
                    raise PEPError(
                        "The vep rule is invalid for %s" % plugin_info.plugin_name
                    )
                else:
                    endpoint = options.pop("endpoint", None)
                    #: If it is not None,
                    #: it means that vep is bound to the blueprint
                    #:
                    #: .. versionadded:: 3.6.0
                    _bp = options.pop("_blueprint", None)

                    plugin_vep.append((rule, view_func, endpoint, options, _bp))
            #: look like [(rule, view_func, endpoint, opts, bp), (), (), etc.]
            plugin_info["plugin_vep"] = plugin_vep
            self.logger.debug("Register VEP Success")
        else:
            raise PEPError(
                "The vep rule is invalid for %s, it should be "
                "a list or tuple." % plugin_info.plugin_name
            )

    def _cvep_handler(self, plugin_info: META, cvep_rule: Sequence[Dict[str, Any]]):
        """Class-based views extension point handler.

        :param cvep_rule: look like [{view_class=, other options}, etc.]

        :raises PEPError: if cvep rule or content is invalid.

        .. versionadded:: 3.5.0
        """
        if isinstance(cvep_rule, dict):
            cvep_rule = (cvep_rule,)
        if isinstance(cvep_rule, (list, tuple)):
            plugin_cvep = []
            for options in cvep_rule:
                try:
                    view_class = options.pop("view_class")
                except KeyError:
                    raise PEPError(
                        "The cvep rule is invalid for %s" % plugin_info.plugin_name
                    )
                else:
                    plugin_cvep.append((view_class, options))
            #: look like [(view_class, other options), (), (), etc.]
            plugin_info["plugin_cvep"] = plugin_cvep
            self.logger.debug("Register CVEP Success")
        else:
            raise PEPError(
                "The cvep rule is invalid for %s, it should be "
                "a list or tuple." % plugin_info.plugin_name
            )

    def _filter_handler(
        self,
        plugin_info: META,
        filter_rule: Union[Dict[str, Callable], Sequence[Union[Callable, Sequence]]],
    ):
        """Template filter handler.

        :param filter_rule: e.g. {filter_name=func,} or [func, (name,func)]

        :raises PEPError: if filter rule or content is invalid.

        .. versionadded:: 3.2.0

        .. versionchanged:: 3.4.0
            If filter_rule is list or tuple, allow nested tuple to set name
        """
        if isinstance(filter_rule, (list, tuple)):
            _filter_rule = {}
            for f in filter_rule:
                name, func = f if isinstance(f, (tuple, list)) else (None, f)
                if not callable(func):
                    raise PEPError(
                        "The filter found a func, that cannot be called for %s"
                        % plugin_info.plugin_name
                    )
                if not name:
                    name = func.__name__
                _filter_rule[name] = func
            filter_rule = _filter_rule
        if isinstance(filter_rule, dict):
            plugin_filter = []
            for name, func in iteritems(filter_rule):
                if callable(func):
                    plugin_filter.append((name, func))
                else:
                    raise PEPError(
                        "The filter cannot be called for %s." % plugin_info.plugin_name
                    )
            plugin_info["plugin_filter"] = plugin_filter
        else:
            raise PEPError(
                "The filter rule is invalid for %s, "
                "it should be a dict." % plugin_info.plugin_name
            )

    def _error_handler(self, plugin_info, errhandler_rule):
        """Error code handler.

        :param errhandler_rule: eg: {err_code=func} or [{error=exception_class,
                                handler=func}, {error=err_code, handler=func}]

        :raises PEPError: if error handler rule or content is invalid.

        .. versionadded:: 3.2.0

        .. versionchanged:: 3.4.0
            Allow registration of class-based exception handlers
        """
        if isinstance(errhandler_rule, dict):
            _errhandler_rule = []
            for code, func in iteritems(errhandler_rule):
                if not isinstance(code, int):
                    raise PEPError(
                        "The errhandler code is not interger for %s"
                        % plugin_info.plugin_name
                    )
                _errhandler_rule.append(dict(error=code, handler=func))
            errhandler_rule = _errhandler_rule
        if isinstance(errhandler_rule, (tuple, list)):
            plugin_errhandler_rules = []
            for eh in errhandler_rule:
                #: eh is dict, look like {error: code_or_class, handler: func}
                if not isinstance(eh, dict) or "error" not in eh or "handler" not in eh:
                    raise PEPError(
                        "The errhandler format error for %s" % plugin_info.plugin_name
                    )
                code_or_exc = eh["error"]
                func = eh["handler"]
                if not isinstance(code_or_exc, int):
                    try:
                        _is_ok_exc = issubclass(code_or_exc, Exception)
                    except TypeError:
                        raise PEPError(
                            "The errhandler custom error class requires"
                            " inheritance of Exception for %s" % plugin_info.plugin_name
                        )
                    else:
                        if not _is_ok_exc:
                            raise PEPError(
                                "The errhandler exc is not a subclass of"
                                " Exception for %s" % plugin_info.plugin_name
                            )
                if not callable(func):
                    raise PEPError(
                        "The errhandler func is not called for %s"
                        % plugin_info.plugin_name
                    )
                plugin_errhandler_rules.append((code_or_exc, func))
            plugin_info["plugin_errhandler"] = plugin_errhandler_rules
        else:
            raise PEPError(
                "The error handler rule is invalid for %s, "
                "it should be a list or tuple." % plugin_info.plugin_name
            )

    def _context_processor_handler(self, plugin_info, processor_rule):
        """Template context processor(tcp) handler.

        :param processor_rule: look like {var_name=var, func_name=func,}

        :raises PEPError: if tcp rule or content is invalid.

        .. versionadded:: 3.2.0
        """
        if isinstance(processor_rule, dict):
            plugin_info["plugin_tcp"] = processor_rule
        else:
            raise PEPError(
                "The context processor rule is invalid for %s, "
                "it should be a dict." % plugin_info.plugin_name
            )

    def _p3_handler(self, plugin_info, p3_rule):
        """Plugin preprocessor handler.

        :param p3_rule: look like {plugin_name:{pet:func}}

        :raises PEPError: if the rule or content is invalid.

        .. versionadded:: 3.7.0
        """
        if isinstance(p3_rule, dict):
            petns = list(self.__pet_handlers.keys())
            petns.remove("p3")
            for pname, handlers in iteritems(p3_rule):
                for pet, func in iteritems(handlers):
                    if pet not in petns:
                        raise PEPError(
                            "The p3 name(%s) is not found for %s"
                            % (pname, plugin_info.plugin_name)
                        )
                    if not callable(func):
                        raise PEPError(
                            "The p3 func(%s) is not called for %s"
                            % (pname, plugin_info.plugin_name)
                        )
            plugin_info["plugin_p3"] = p3_rule
        else:
            raise PEPError(
                "The p3 handler rule is invalid for %s, "
                "it should be a dict." % plugin_info.plugin_name
            )

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

    def __preprocess_all_plugins(self):
        """After the local plug-in and third-party plug-in are loaded,
        the `p3` parameters of the all plug-in are parsed,
        and the plug-in data is pre-processed.

        If the plugin is not enabled, skip it.

        .. versionadded:: 3.7.0
        """
        # all plugins data
        oplugins = []
        # like {plugin_name:[(from_pname,{pet:func, pet:func}), (other,{})],}
        p3s = {}
        for p in self.__plugins:
            oplugins.append(p)
            if p.plugin_state == "enabled":
                for pname, handler in iteritems(p.plugin_p3):
                    p3s.setdefault(pname, []).append((p.plugin_name, handler))
        nplugins = []
        petns = list(self.__pet_handlers.keys())
        petns.remove("p3")
        for p in oplugins:
            if p.plugin_state == "enabled" and p.plugin_name in p3s:
                for handler in p3s[p.plugin_name]:
                    from_pname = handler[0]
                    pets_funcs = handler[1]
                    for pet, func in iteritems(pets_funcs):
                        if pet in petns:
                            obj = "plugin_" + pet
                            try:
                                ov = p[obj]
                                nv = func(ov)
                                if type(ov) != type(nv):
                                    raise PluginError(
                                        "Illegal extension point" " data type(%s)" % pet
                                    )
                            except Exception as e:
                                self.logger.debug(e)
                                raise PEPError(from_pname, str(e))
                            else:
                                p[obj] = nv
            nplugins.append(p)
        self.__plugins = nplugins

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
            if isdir(p.plugin_tpl_path)
        ]

    @property
    def get_enabled_teps(self):
        """Get all tep of the enabled plugins.

        :returns: dict, look like {tep_1: dict(fil=[], cod=[]), tep_n...}
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

        :returns: dictionary with nested tuples, look like {hook:[]}
        """
        heps = {}
        for hep in self.__het_allow_hooks.keys():
            heps[hep] = [
                p.plugin_hep[hep]
                for p in self.get_enabled_plugins
                if hep in p.plugin_hep.keys()
            ]
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
    def get_enabled_cveps(self):
        """Get all cvep for the enabled plugins.

        :returns: List of nested tuples, like [(view_class, other options),]

        .. versionadded:: 3.5.0
        """
        return [
            rule
            for p in self.get_enabled_plugins
            for rule in p.plugin_cvep
            if p.plugin_cvep
        ]

    @property
    def get_enabled_filters(self):
        """Get all template filters for the enabled plugins.

        :returns: List of nested tuples, like [(filter_name, filter_func),]

        .. versionadded:: 3.2.0
        """
        return list(
            chain.from_iterable(
                [p.plugin_filter for p in self.get_enabled_plugins if p.plugin_filter]
            )
        )

    @property
    def get_enabled_errhandlers(self):
        """Get all error handlers for the enabled plugins.

        :returns: list, like [(err_code_class, func_handler), ...]

        .. versionadded:: 3.2.0

        .. versionchanged:: 3.4.0
            Return type changed from dict to list
        """
        return list(
            chain.from_iterable(
                [
                    p.plugin_errhandler
                    for p in self.get_enabled_plugins
                    if p.plugin_errhandler
                ]
            )
        )

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
                (p for p in self.get_all_plugins if p.plugin_name == plugin_name)
            )
        except StopIteration:
            raise PluginError("No plugin named %s was found" % plugin_name)

    def disable_plugin(self, plugin_name):
        """Disable a plugin (that is, create a DISABLED empty file)
        and restart the application to take effect.
        """
        p = self.get_plugin_info(plugin_name)
        ENABLED = join(p.plugin_package_abspath, "ENABLED")
        DISABLED = join(p.plugin_package_abspath, "DISABLED")
        if isfile(ENABLED):
            remove(ENABLED)
        self.__touch_file(DISABLED)

    def enable_plugin(self, plugin_name):
        """Enable a plugin (that is, create a ENABLED empty file)
        and restart the application to take effect.
        """
        p = self.get_plugin_info(plugin_name)
        ENABLED = join(p.plugin_package_abspath, "ENABLED")
        DISABLED = join(p.plugin_package_abspath, "DISABLED")
        if isfile(DISABLED):
            remove(DISABLED)
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
                func = sorted(
                    tep_result[tep_typ],
                    key=lambda x: x.split("@")[0],
                    reverse=self.stpl_reverse,
                )
                return map(lambda tpl: tpl.split("@")[-1], func)

            tep_result["fil"] = _sort_refresh("fil")
            tep_result["cod"] = _sort_refresh("cod")

        mtf = Markup(
            "".join([render_template(i, **context) for i in tep_result["fil"]])
        )
        mtc = Markup(
            "".join([render_template_string(i, **context) for i in tep_result["cod"]])
        )

        typ = "all" if typ not in ("fil", "cod") else typ
        if typ == "fil":
            return mtf
        elif typ == "cod":
            return mtc
        else:
            return mtf + mtc

    def emit_assets(self, plugin_name, filename, _raw=False, _external=False):
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

            <script src="/assets/plugin/js/demo.js"></script>

        Other types of files, only return file url path segment, like this::

            /assets/plugin/img/logo.png
            /assets/plugin/attachment/test.zip

        However, the ``_raw`` parameter has been added in v3.4.0, and if it is
        True, only path is generated.

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
                <div class="showJsPath">
                    <scan>
                        {{ emit_assets('demo', 'js/demo.js', _raw=True) }}
                    </scan>
                </div>
            </body>
            </html>

        :param plugin_name: name of the plugin, which is `__plugin_name__`

        :param filename: filename in the static directory of the plugin package

        :param _raw: if True, not to parse automatically, only generate uri.
                     Default False.

        :param _external: _external parameter passed to url_for

        :returns: html code with :class:`~flask.Markup`.

        .. versionchanged:: 3.4.0
            Add _raw, only generate uri without parse

        .. versionchanged:: 3.6.0
            Add _external, pass to :func:`flask.url_for`
        """
        uri = url_for(
            self.static_endpoint,
            plugin_name=plugin_name,
            filename=filename,
            _external=_external,
        )
        if _raw is not True:
            if filename.endswith(".css"):
                uri = '<link rel="stylesheet" href="%s">' % uri
            elif filename.endswith(".js"):
                uri = '<script src="%s"></script>' % uri
        return Markup(uri)

    def emit_config(self, conf_name):
        """Get configuration information in the template context."""
        try:
            return self.pluginkit_config[conf_name]
        except KeyError:
            return current_app.config.get(conf_name)


def push_dcp(event, callback, position="right"):
    """Push a callable for with :meth:`~flask_pluginkit.utils.DcpManager.push`.

    Example usage::

        push_dcp('demo', lambda:'Hello dcp')

    .. versionadded:: 3.2.0
    """
    current_app.extensions.get("pluginkit")._dcp_manager.push(event, callback, position)
