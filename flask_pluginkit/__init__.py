# -*- coding: utf-8 -*-

from .exceptions import PluginError, TarError, ZipError, InstallError, CSSLoadError, DCPError, VersionError
from .flask_pluginkit import PluginManager, push_dcp
from .installer import PluginInstaller
from .web import blueprint
from .fixflask import Flask
from .utils import BaseStorage, LocalStorage, RedisStorage, PY2, string_types, isValidSemver, sortedSemver

__author__ = "staugur <staugur@saintic.com>"

__version__ = "2.1.1"

__all__ = ["Flask", "PluginManager", "PluginInstaller", "blueprint", "push_dcp",
           "PluginError", "TarError", "ZipError", "InstallError", "CSSLoadError", "DCPError", "VersionError",
           "BaseStorage", "LocalStorage", "RedisStorage", "PY2", "string_types", "isValidSemver", "sortedSemver"]
