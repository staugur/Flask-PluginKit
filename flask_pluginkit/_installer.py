# -*- coding: utf-8 -*-
"""
    flask_pluginkit._installer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    installer: install or remove plugin.

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

import re
import shutil
import tarfile
import zipfile
from os import remove
from os.path import join, abspath, isdir, isfile, basename
from sys import executable
from subprocess import call
from cgi import parse_header
from posixpath import basename as posixbasename
from tempfile import NamedTemporaryFile
from .exceptions import PluginError, TarError, ZipError, InstallError
from ._compat import string_types, urllib2, urlsplit, parse_qs
from .utils import check_url


class PluginInstaller(object):
    """plugin installer for installing a compressed local/remote plugin"""

    def __init__(self, plugin_abspath, **kwargs):
        """
        :param plugin_abspath: the absolute path to the plugin directory.
        """
        self.plugin_abspath = plugin_abspath
        if not isdir(self.plugin_abspath):
            raise PluginError("Not Found Plugin Directory")

    def __isValidTGZ(self, suffix):
        """To determine whether the suffix `.tar.gz` or `.tgz` format"""
        if suffix and isinstance(suffix, string_types):
            if suffix.endswith(".tar.gz") or suffix.endswith(".tgz"):
                return True
        return False

    def __isValidZIP(self, suffix):
        """Determine if the suffix is `.zip` format"""
        if suffix and isinstance(suffix, string_types):
            if suffix.endswith(".zip"):
                return True
        return False

    def __isValidFilename(self, filename):
        """Determine whether filename is valid"""
        if filename and isinstance(filename, string_types):
            if re.match(r"^[\w\d\_\-\.]+$", filename.split("/")[-1], re.I):
                if self.__isValidTGZ(filename) or self.__isValidZIP(filename):
                    return True
        return False

    def __getFilename(self, data, scene=1):
        """To get the data from different scenarios in the filename,
        scene value see `remote_download` in 1, 2, 3, 4
        """
        filename = None
        try:
            if scene == 1:
                plugin_filename = [
                    i
                    for i in parse_qs(urlsplit(data).query).get("plugin_filename") or []
                    if i
                ]
                if plugin_filename and len(plugin_filename) == 1:
                    filename = plugin_filename[0]
            elif scene == 2:
                filename = posixbasename(urlsplit(data).path)
            elif scene == 3:
                cd = data.getheader("Content-Disposition", "")
                filename = parse_header(cd)[-1].get("filename")
            elif scene == 4:
                cd = data.info().get_content_subtype()
                mt = {
                    "zip": "zip",
                    "x-compressed-tar": "tar.gz",
                    "x-gzip": "tar.gz",
                }
                subtype = mt.get(cd)
                if subtype:
                    filename = "." + subtype
        finally:
            if self.__isValidFilename(filename):
                return filename

    def __getFilenameSuffix(self, filename):
        """Gets the filename suffix"""
        if filename and isinstance(filename, string_types):
            if self.__isValidTGZ(filename):
                return ".tar.gz"
            elif filename.endswith(".zip"):
                return ".zip"

    def __unpack_tgz(self, filename):
        """Unpack the `tar.gz`, `tgz` compressed file format"""
        if (
            isinstance(filename, string_types)
            and self.__isValidTGZ(filename)
            and tarfile.is_tarfile(filename)
        ):
            with tarfile.open(filename, mode="r:gz") as t:
                for name in t.getnames():
                    t.extract(name, self.plugin_abspath)
        else:
            raise TarError("Invalid Plugin Compressed File")

    def __unpack_zip(self, filename):
        """Unpack the `zip` compressed file format"""
        if (
            isinstance(filename, string_types)
            and self.__isValidZIP(filename)
            and zipfile.is_zipfile(filename)
        ):
            with zipfile.ZipFile(filename) as z:
                for name in z.namelist():
                    z.extract(name, self.plugin_abspath)
        else:
            raise ZipError("Invalid Plugin Compressed File")

    def _remote_download(self, url):
        """To download the remote plugin package,
        there are four methods of setting filename according to priority,
        each of which stops setting when a qualified filename is obtained,
        and an exception is triggered when a qualified valid filename is
        ultimately unavailable.

        1. Add url `plugin_filename` query parameters
        2. The file name is resolved in the url, eg: http://x.com/p-v0.0.1.tgz
        3. Parse the Content-Disposition in the return header
        4. Parse the Content-Type in the return header
        """
        #: Try to set filename in advance based on the previous two steps
        if check_url(url):
            filename = self.__getFilename(url, scene=1)
            if not filename:
                filename = self.__getFilename(url, scene=2)
            #: fix UnboundLocalError
            f = None
            try:
                f = urllib2.urlopen(url, timeout=10)
            except (AttributeError, ValueError, urllib2.URLError):
                raise InstallError("Open URL Error")
            else:
                if not filename:
                    filename = self.__getFilename(f, scene=3)
                    if not filename:
                        filename = self.__getFilename(f, scene=4)
                if filename and self.__isValidFilename(filename):
                    suffix = self.__getFilenameSuffix(filename)
                    with NamedTemporaryFile(
                        mode="w+b", prefix="fpk-", suffix=suffix, delete=False
                    ) as fp:
                        fp.write(f.read())
                        filename = fp.name
                    try:
                        if self.__isValidTGZ(suffix):
                            self.__unpack_tgz(filename)
                        else:
                            self.__unpack_zip(filename)
                    finally:
                        remove(filename)
                else:
                    raise InstallError("Invalid Filename")
            finally:
                if f is not None:
                    f.close()
        else:
            raise InstallError("Invalid URL")

    def _local_upload(self, filepath, remove=False):
        """Local plugin package processing"""
        if isfile(filepath):
            filename = basename(abspath(filepath))
            if filename and self.__isValidFilename(filename):
                suffix = self.__getFilenameSuffix(filename)
                try:
                    if self.__isValidTGZ(suffix):
                        self.__unpack_tgz(abspath(filepath))
                    else:
                        self.__unpack_zip(abspath(filepath))
                finally:
                    if remove is True:
                        remove(filepath)
            else:
                raise InstallError("Invalid Filename")
        else:
            raise InstallError("Invalid Filepath")

    def _pip_install(self, package_or_url):
        """Use the pip command to install third-party modules.

        .. versionadded:: 3.3.0
        """
        res = dict(code=1, msg=None)
        if (
            package_or_url
            and isinstance(package_or_url, string_types)
            and package_or_url not in (".", "-")
        ):
            code = call([executable, "-m", "pip", "install", package_or_url])
            res.update(code=code)
            if code != 0:
                res.update(msg="Installation failed with pip command")
        else:
            res.update(msg="Invalid parameter package_or_url", code=1)
        return res

    def addPlugin(self, method="remote", **kwargs):
        """Add plugin,
        support only for `.tar.gz` or `.zip` compression packages.

        :param method: supported method:

                       ``remote``, download and unpack a remote plugin package;

                       ``local``, unzip a local plugin package.

                       ``pip``, install package with pip command.

        :param url: for method is remote,
                    plugin can be downloaded from the address.

        :param filepath: for method is local, plugin local absolute path

        :param remove: for method is local, remove the plugin source code
                       package, default is False.

        :param package_or_url: for method is pip, pypi's package or VCS url.

        :returns: the result of adding the plugin, like {msg:str, code:int},
                  code=0 is successful.

        .. versionchanged:: 3.3.0
            Add pip method, with package_or_url param.
        """
        res = dict(code=1, msg=None)
        try:
            if method == "remote":
                self._remote_download(kwargs["url"])
            elif method == "local":
                self._local_upload(kwargs["filepath"], kwargs.get("remove", False))
            elif method == "pip":  # pragma: nocover
                res = self._pip_install(kwargs["package_or_url"])
            else:
                res.update(msg="Invalid method")
        except Exception as e:
            res.update(msg=str(e))
        else:
            if method != "pip":
                res.update(code=0)
        return res

    def removePlugin(self, package):
        """Remove a local plugin

        :param package: The plugin package name, not __plugin_name.
        """
        res = dict(code=1, msg=None)
        if package and isinstance(package, string_types):
            path = join(self.plugin_abspath, package)
            if isdir(path):
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    res.update(msg=str(e))
                else:
                    res.update(code=0)
            else:
                res.update(msg="No Such Package")
        else:
            res.update(msg="Invalid Package Format")
        return res
