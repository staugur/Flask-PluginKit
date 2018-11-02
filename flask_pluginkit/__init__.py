# -*- coding: utf-8 -*-

version = "2.1.0"

author = "staugur"

email = "staugur@saintic.com"

from .exceptions import PluginError, TarError, ZipError, InstallError, CSSLoadError, DCPError
from .flask_pluginkit import PluginManager, push_dcp
from .installer import PluginInstaller
from .web import blueprint
from .fixflask import Flask
from .utils import BaseStorage, LocalStorage, RedisStorage, PY2, string_types

__all__ = ["Flask", "PluginManager", "PluginInstaller", "blueprint", "push_dcp",
           "PluginError", "TarError", "ZipError", "InstallError", "CSSLoadError", "DCPError",
           "BaseStorage", "LocalStorage", "RedisStorage", "PY2", "string_types"]
