# -*- coding: utf-8 -*-
"""
    Flask-PluginKit
    ~~~~~~~~~~~~~~

    PluginManager: load and run plugins.

    PluginInstaller: install or remove plugin.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import re
import sys
import jinja2
import shutil
import tarfile
import zipfile
import urllib2
import logging
from itertools import chain
from cgi import parse_header
from posixpath import basename
from urlparse import urlsplit, parse_qs
from tempfile import NamedTemporaryFile
from flask import Response, render_template

logger = logging.getLogger(__name__)


class PluginError(Exception):
    pass


class TarError(PluginError):
    pass


class ZipError(PluginError):
    pass


class InstallError(PluginError):
    pass


class CSSNotFoundError(PluginError):
    pass


class TemplateEventResult(list):

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
    静态资源建议上传到第三方存储中.
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

    def __init__(self, app=None, plugins_base=None, plugins_folder="plugins", **kwargs):
        """Initializes the PluginManager. It is also possible to initialize the PluginManager via a factory. For example::
            plugin_manager = PluginManager()
            plugin_manager.init_app(app)
        :param app: The flask application.
        :param plugins_base: The plugin folder where the plugins resides.
        :param plugins_folder: The base folder for the application. It is used to build the plugins package name.
        """
        self.plugins_folder = plugins_folder
        self.plugin_abspath = os.path.join(plugins_base or os.getcwd(), self.plugins_folder)
        if not os.path.isdir(self.plugin_abspath):
            raise PluginError("Not Found Plugin Directory for %s" % self.plugin_abspath)

        #: all locally stored plugins
        #:
        #: .. versionadded:: 0.1.4
        self.__plugins = []

        #: logging Logger instance
        #:
        #: .. versionadded:: 0.1.9
        self.logger = kwargs.get("logger", logger)

        #: initialize app via a factory
        #:
        #: .. versionadded:: 0.1.4
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.static_url_path = app.static_url_path
        self.__scanPlugins()
        # 自定义添加多模板文件夹
        app.jinja_loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.FileSystemLoader([p["plugin_tpl_path"] for p in self.get_enabled_plugins if os.path.isdir(os.path.join(app.root_path, p["plugin_tpl_path"]))]),
        ])
        # 自定义添加多静态文件夹，需要`flask-multistatic`扩展支持
        if isinstance(app.static_folder, list):
            app.static_folder += [p["plugin_ats_path"] for p in self.get_enabled_plugins if os.path.isdir(os.path.join(app.root_path, p["plugin_ats_path"]))]
        # 注册模板变量
        app.jinja_env.globals["emit_tep"] = self.emit_tep
        app.jinja_env.globals["emit_yep"] = self.emit_yep

        # 注册蓝图扩展点
        for bep in self.get_all_bep:
            app.register_blueprint(bep["blueprint"], url_prefix=bep["prefix"])

        # 注册请求上下文扩展点
        @app.before_request
        def _before_request():
            # 上下文扩展点之请求前
            for cep_func in self.get_all_cep["before_request_hook"]:
                cep_func()
            # 上下文扩展点之拦截请求
            for cep_func in self.get_all_cep["before_request_return"]:
                resp = cep_func()
                if isinstance(resp, Response) and hasattr(resp, "is_before_request_return") and resp.is_before_request_return is True:
                    return resp

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

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['pluginkit'] = self
        app.plugin_manager = self
        self.app = app

    def __scanPlugins(self):
        """ 扫描插件目录 """
        self.logger.info("Initialization Plugins Start, loadPlugins path: %s" % self.plugin_abspath)
        if os.path.isdir(self.plugin_abspath):
            for package in os.listdir(self.plugin_abspath):
                _plugin_path = os.path.join(self.plugin_abspath, package)
                if os.path.isdir(_plugin_path) and os.path.isfile(os.path.join(_plugin_path, "__init__.py")):
                    self.logger.info("find plugin package: %s" % package)
                    #: 动态加载模块(plugins.package): 可以查询自定义的信息, 并通过getPluginClass获取插件的类定义
                    plugin = __import__("{0}.{1}".format(self.plugins_folder, package), fromlist=[self.plugins_folder, ])
                    #: 检测插件信息
                    if hasattr(plugin, "__name__") and \
                            hasattr(plugin, "__version__") and \
                            hasattr(plugin, "__description__") and \
                            hasattr(plugin, "__author__") and \
                            hasattr(plugin, "getPluginClass"):
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
                            self.logger.info("The plugin {0} wants to register the following template extension points: {1}".format(package, tep))
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
                                        raise PluginError("Invalid TEP Format")
                                pluginInfo.update(plugin_tep=newTep)
                                self.logger.info("Register TEP Success")
                            else:
                                self.logger.error("Register TEP Failed, not a dict")
                        #: 注册上下文扩展点
                        if hasattr(i, "register_cep"):
                            cep = i.register_cep()
                            self.logger.info("The plugin {0} wants to register the following context extension points: {1}".format(package, cep))
                            if isinstance(cep, dict):
                                pluginInfo.update(plugin_cep=cep)
                                self.logger.info("Register CEP Success")
                            else:
                                self.logger.error("Register CEP Failed, not a dict")
                        #: 注册蓝图扩展点
                        if hasattr(i, "register_bep"):
                            bep = i.register_bep()
                            self.logger.info("The plugin {0} wants to register the following blueprint extension points: {1}".format(package, bep))
                            if isinstance(bep, dict):
                                pluginInfo.update(plugin_bep=bep)
                                self.logger.info("Register BEP Success")
                            else:
                                self.logger.error("Register BEP Failed, not a dict")
                        #: 注册样式扩展点
                        if hasattr(i, "register_yep"):
                            # 注册所有插件的层叠样式表(css)文件
                            yep = i.register_yep()
                            newCSS = []
                            if isinstance(yep, (unicode, str)):
                                if os.path.isfile(os.path.join(self.plugin_abspath, package, "static", yep)) and \
                                        yep.endswith(".css"):
                                    newCSS.append(self.static_url_path + "/" + yep)
                            elif isinstance(yep, (list, tuple)):
                                for css in yep:
                                    if isinstance(css, (unicode, str)) and \
                                            os.path.isfile(os.path.join(self.plugin_abspath, package, "static", css)) and \
                                            css.endswith(".css"):
                                        newCSS.append(self.static_url_path + "/" + css)
                                    else:
                                        raise CSSNotFoundError("YEP CSS File Not Found: %s" % css)
                            else:
                                raise PluginError("Register YEP Failed, not str or list or tuple")
                            pluginInfo.update(plugin_yep=newCSS)
                            self.logger.info("Register YEP Success")
                        #: 注册信号扩展点`sep`
                        #: 加入全局插件中
                        if hasattr(i, "run") or hasattr(i, "register_tep") or hasattr(i, "register_cep") or hasattr(i, "register_bep") or hasattr(i, "register_yep"):
                            self.__plugins.append(pluginInfo)
                        else:
                            self.logger.error("The current package does not have the `run` or `register_tep` or `register_cep` or `register_bep` or `register_yep` method")

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
            "plugin_ats_path": os.path.join(self.plugins_folder, package, "static"),
            "plugin_tep": {},
            "plugin_cep": {},
            "plugin_bep": {},
            "plugin_yep": {}
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
        """上下文扩展点, Context extension point, 分别对应请求前、请求后(返回前，无异常)、请求后(返回前，无论是否有异常)、请求前(直接拦截请求):
        CEP: before_request_hook
        CEP: after_request_hook
        CEP: teardown_request_hook
        CEP: before_request_return
        """
        return dict(
            before_request_hook=[plugin["plugin_cep"]["before_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("before_request_hook")],
            after_request_hook=[plugin["plugin_cep"]["after_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("after_request_hook")],
            teardown_request_hook=[plugin["plugin_cep"]["teardown_request_hook"] for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("teardown_request_hook")],
            before_request_return=[plugin["plugin_cep"]["before_request_return"] for plugin in self.get_enabled_plugins if plugin["plugin_cep"].get("before_request_return")],
        )

    @property
    def get_all_bep(self):
        """蓝图扩展点"""
        return [plugin["plugin_bep"] for plugin in self.get_enabled_plugins if plugin["plugin_bep"]]

    @property
    def get_all_yep(self):
        """层叠样式表(css)扩展点"""
        return list(chain.from_iterable([plugin["plugin_yep"] for plugin in self.get_enabled_plugins if plugin["plugin_yep"]]))

    def emit_tep(self, tep, typ="all"):
        """获取模板扩展点数据，请在模板中使用此函数，扩展点需要自己定义，方法如下：
        假设有一个扩展点名叫`tep`，只需要模板中启用自定义的扩展点:
            ```
            # 渲染某个扩展点的HTML代码和文件
            {{ emit_tep('tep') }}
            ```
        参数：
            @param tep str: 模板扩展点名称，这是唯一的，一个tep解析结果是list，内可以是html代码和文件
            @param typ str: 渲染类型，all-渲染所有-默认，fil-渲染HTML文件，cod=渲染HTML代码
        """
        e = self.get_all_tep.get(tep) or dict(HTMLFile=[], HTMLString=[])
        typ = "all" if not typ in ("fil", "cod") else typ
        mtf = jinja2.Markup("".join(map(render_template, e["HTMLFile"])))
        mtc = jinja2.Markup("".join(e["HTMLString"]))
        if typ == "fil":
            return mtf
        elif typ == "cod":
            return mtc
        else:
            return mtf + mtc

    def emit_yep(self):
        """获取样式扩展点数据，请在模板中<head></head>之间使用此函数，且应用需要支持多静态文件夹功能，即是用flask-multistatic初始化的app
        假设以下模板，需要用emit_yep启用引入css文件：
        ```
            <!DOCTYPE html>
            <html>
            <head>
                <title></title>
                {{ emit_yep() }}
            </head>
            <body>
                Your HTML Code
                {{ emit_tep('tep') }}
            </body>
            </html>
        ```
        """
        tpl = ''
        for css in self.get_all_yep:
            tpl += '<link rel="stylesheet" type="text/css" href="%s" />' % css
        return jinja2.Markup(tpl)


class PluginInstaller(object):
    """插件安装器，用于安装一个压缩格式的本地/远程插件"""

    def __init__(self, plugin_abspath):
        self.plugin_abspath = plugin_abspath
        if not os.path.isdir(self.plugin_abspath):
            raise PluginError("Not Found Plugin Directory")

    def __isValidUrl(self, addr):
        """检测UrlAddr是否为有效格式，例如
        http://ip:port
        https://abc.com
        """
        regex = re.compile(
            r'^(?:http)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if addr and isinstance(addr, (str, unicode)):
            if regex.match(addr):
                return True
        return False

    def __isValidTGZ(self, suffix):
        """判断后缀是否是`.tar.gz`或`.tgz`格式"""
        if suffix and isinstance(suffix, (unicode, str)):
            if suffix.endswith(".tar.gz") or suffix.endswith(".tgz"):
                return True
        return False

    def __isValidZIP(self, suffix):
        """判断后缀是否是`.zip`格式"""
        if suffix and isinstance(suffix, (unicode, str)):
            if suffix.endswith(".zip"):
                return True
        return False

    def __isValidFilename(self, filename):
        """判断filename是否是合法的"""
        if filename and isinstance(filename, (unicode, str)):
            if re.match(r'^[\w\d\_\-\.]+$', filename, re.I):
                if self.__isValidTGZ(filename) or self.__isValidZIP(filename):
                    return True
        return False

    def __getFilename(self, data, scene=1):
        """从不同场景中获取data中filename，场景值参看`remote_download`中1、2、3、4"""
        try:
            filename = None
            if scene == 1:
                plugin_filename = [i for i in parse_qs(urlsplit(data).query).get("plugin_filename") or [] if i]
                if plugin_filename and len(plugin_filename) == 1:
                    filename = plugin_filename[0]
            elif scene == 2:
                filename = basename(urlsplit(data).path)
            elif scene == 3:
                filename = parse_header(data)[-1].get("filename")
            elif scene == 4:
                mt = {'zip': 'zip', 'x-compressed-tar': 'tar.gz', 'x-gzip': 'tar.gz'}
                subtype = mt.get(data)
                if subtype:
                    filename = "." + subtype
        except Exception, e:
            logger.warning(e)
        else:
            if self.__isValidFilename(filename):
                return filename

    def __getFilenameSuffix(self, filename):
        """获取filename后缀"""
        if filename and isinstance(filename, (unicode, str)):
            if self.__isValidTGZ(filename):
                return ".tar.gz"
            elif filename.endswith(".zip"):
                return ".zip"

    def __unpack_tgz(self, filename):
        """解压`tar.gz`,`tgz`格式的压缩文件"""
        if isinstance(filename, (str, unicode)) and self.__isValidTGZ(filename) and tarfile.is_tarfile(filename):
            with tarfile.open(filename, mode='r:gz') as t:
                for name in t.getnames():
                    t.extract(name, self.plugin_abspath)
        else:
            raise TarError("Invalid Plugin Compressed File")

    def __unpack_zip(self, filename):
        """解压`zip`格式的压缩文件"""
        if isinstance(filename, (str, unicode)) and self.__isValidZIP(filename) and zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename) as z:
                for name in z.namelist():
                    z.extract(name, self.plugin_abspath)
        else:
            raise ZipError("Invalid Plugin Compressed File")

    def _remote_download(self, url):
        """下载远程插件包，filename设置依照优先级有四种方法，每一种获取到合格的文件名时停止设置，最终无法获取合格有效的文件名时触发异常
        1. url中添加`plugin_filename`参数
        2. url中解析出文件名
        3. 解析返回头中Content-Disposition
        4. 解析返回头中Content-Type
        """
        # 预先根据前两步尝试设置filename
        if self.__isValidUrl(url):
            filename = self.__getFilename(url, scene=1)
            if not filename:
                filename = self.__getFilename(url, scene=2)
            try:
                f = urllib2.urlopen(url, timeout=10)
                i = f.info()
            except (AttributeError, ValueError, urllib2.URLError):
                raise InstallError("Open URL Error")
            else:
                if not filename:
                    filename = self.__getFilename(i.getheader("Content-Disposition", ""), scene=3)
                    if not filename:
                        filename = self.__getFilename(i.subtype, scene=4)
                if filename and self.__isValidFilename(filename):
                    suffix = self.__getFilenameSuffix(filename)
                    with NamedTemporaryFile(mode='w+b', prefix='fpk-', suffix=suffix, delete=False) as fp:
                        fp.write(f.read())
                        filename = fp.name
                    try:
                        self.__unpack_tgz(filename) if self.__isValidTGZ(suffix) else self.__unpack_zip(filename)
                    finally:
                        os.remove(filename)
                else:
                    raise InstallError("Invalid Filename")
            finally:
                f.close()
        else:
            raise InstallError("Invalid URL")

    def _local_upload(self, filepath, remove=False):
        """本地插件包处理"""
        if os.path.isfile(filepath):
            filename = os.path.basename(os.path.abspath(filepath))
            if filename and self.__isValidFilename(filename):
                suffix = self.__getFilenameSuffix(filename)
                try:
                    self.__unpack_tgz(os.path.abspath(filepath)) if self.__isValidTGZ(suffix) else self.__unpack_zip(os.path.abspath(filepath))
                finally:
                    if remove is True:
                        os.remove(filepath)
            else:
                raise InstallError("Invalid Filename")
        else:
            raise InstallError("Invalid Filepath")

    def addPlugin(self, method="remote", **kwargs):
        """添加一个插件"""
        res = dict(code=1, msg=None)
        try:
            if method == "remote":
                self._remote_download(kwargs["url"])
            elif method == "local":
                self._local_upload(kwargs["filepath"], kwargs.get("remove", False))
            else:
                res.update(msg="Invalid method")
        except Exception, e:
            res.update(msg=str(e))
        else:
            res.update(code=0)
        return res

    def removePlugin(self, package):
        """删除一个插件"""
        res = dict(code=1, msg=None)
        if package and isinstance(package, (str, unicode)):
            path = os.path.join(self.plugin_abspath, package)
            if os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                except Exception, e:
                    res.update(msg=str(e))
                else:
                    res.update(code=0)
            else:
                res.update(msg="No Such Package")
        else:
            res.update(msg="Invalid Package Format")
        return res
