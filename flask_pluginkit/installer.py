# -*- coding: utf-8 -*-
"""
    Flask-PluginKit
    ~~~~~~~~~~~~~~

    PluginInstaller: install or remove plugin.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import re
import shutil
import tarfile
import zipfile
import urllib2
import logging
from cgi import parse_header
from posixpath import basename
from urlparse import urlsplit, parse_qs
from tempfile import NamedTemporaryFile
from .exceptions import PluginError, TarError, ZipError, InstallError

logger = logging.getLogger(__name__)


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
