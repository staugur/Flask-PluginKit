# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.installer
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    installer: install or remove plugin.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import re
import shutil
import tarfile
import zipfile
import logging
from cgi import parse_header
from posixpath import basename
from tempfile import NamedTemporaryFile
from .exceptions import PluginError, TarError, ZipError, InstallError
from .utils import PY2, string_types
if PY2:
    import urllib2
    from urlparse import urlsplit, parse_qs
else:
    import urllib.request as urllib2
    from urllib.parse import urlsplit, parse_qs

logger = logging.getLogger(__name__)


class PluginInstaller(object):
    """plugin installer for installing a compressed local/remote plugin"""

    def __init__(self, plugin_abspath, **kwargs):
        """
        :param plugin_abspath: The absolute path to the plugin directory.
        """
        self.plugin_abspath = plugin_abspath
        if not os.path.isdir(self.plugin_abspath):
            raise PluginError("Not Found Plugin Directory")

        #: logging Logger instance
        #:
        #: .. versionadded:: 1.0.1
        self.logger = kwargs.get("logger", logger)

    def __isValidUrl(self, addr):
        """Check if the UrlAddr is in a valid format, for example::

            http://ip:port
            https://abc.com
        """
        regex = re.compile(
            r'^(?:http)s?://'  #: http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  #: domain...
            r'localhost|'  #: localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  #: ...or ip
            r'(?::\d+)?'  #: optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if addr and isinstance(addr, string_types):
            if regex.match(addr):
                return True
        return False

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
            if re.match(r'^[\w\d\_\-\.]+$', filename, re.I):
                if self.__isValidTGZ(filename) or self.__isValidZIP(filename):
                    return True
        return False

    def __getFilename(self, data, scene=1):
        """To get the data from different scenarios in the filename, scene value see `remote_download` in 1, 2, 3, 4"""
        try:
            filename = None
            if scene == 1:
                plugin_filename = [i for i in parse_qs(urlsplit(data).query).get("plugin_filename") or [] if i]
                if plugin_filename and len(plugin_filename) == 1:
                    filename = plugin_filename[0]
            elif scene == 2:
                filename = basename(urlsplit(data).path)
            elif scene == 3:
                if PY2:
                    cd = data.headers.getheader("Content-Disposition", "")
                else:
                    cd = data.getheader("Content-Disposition", "")
                filename = parse_header(cd)[-1].get("filename")
            elif scene == 4:
                if PY2:
                    cd = data.info().subtype
                else:
                    cd = data.info().get_content_subtype()
                mt = {'zip': 'zip', 'x-compressed-tar': 'tar.gz', 'x-gzip': 'tar.gz'}
                subtype = mt.get(cd)
                if subtype:
                    filename = "." + subtype
        except Exception as e:
            self.logger.warning(e)
        else:
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
        if isinstance(filename, string_types) and self.__isValidTGZ(filename) and tarfile.is_tarfile(filename):
            with tarfile.open(filename, mode='r:gz') as t:
                for name in t.getnames():
                    t.extract(name, self.plugin_abspath)
        else:
            raise TarError("Invalid Plugin Compressed File")

    def __unpack_zip(self, filename):
        """Unpack the `zip` compressed file format"""
        if isinstance(filename, string_types) and self.__isValidZIP(filename) and zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename) as z:
                for name in z.namelist():
                    z.extract(name, self.plugin_abspath)
        else:
            raise ZipError("Invalid Plugin Compressed File")

    def _remote_download(self, url):
        """To download the remote plugin package,
        there are four methods of setting filename according to priority,
        each of which stops setting when a qualified filename is obtained,
        and an exception is triggered when a qualified valid filename is ultimately unavailable.

        1. Add url `plugin_filename` query parameters
        2. The file name is resolved in the url, eg: http://xx.xx.com/plugin-v0.0.1.tar.gz
        3. Parse the Content-Disposition in the return header
        4. Parse the Content-Type in the return header
        """
        #: Try to set filename in advance based on the previous two steps
        if self.__isValidUrl(url):
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
                if f is not None:
                    f.close()
        else:
            raise InstallError("Invalid URL")

    def _local_upload(self, filepath, remove=False):
        """Local plugin package processing"""
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
        """Add a plugin, support only for `.tar.gz` or `.zip` compression packages.

        :param method:
            `remote`, download and unpack a remote plugin package;
            `local`, unzip a local plugin package.

        :param url: str: for method is remote, plugin can be downloaded from the address.

        :param filepath: str: for method is local, plugin local absolute path

        :param remove: Boolean: for method is local, remove the plugin source code package, default is False.

        :returns: dict: add the result of the plugin, like dict(msg=str, code=int), code=0 is successful.
        """
        res = dict(code=1, msg=None)
        try:
            if method == "remote":
                self._remote_download(kwargs["url"])
            elif method == "local":
                self._local_upload(kwargs["filepath"], kwargs.get("remove", False))
            else:
                res.update(msg="Invalid method")
        except Exception as e:
            res.update(msg=str(e))
        else:
            res.update(code=0)
        return res

    def removePlugin(self, package):
        """Remove a plugin

        :param package: The plugin package name.
        """
        res = dict(code=1, msg=None)
        if package and isinstance(package, string_types):
            path = os.path.join(self.plugin_abspath, package)
            if os.path.isdir(path):
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
