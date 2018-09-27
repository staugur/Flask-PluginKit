# -*- coding: utf-8 -*-

version = "0.1.10"

author = "staugur"

email = "staugur@saintic.com"

from .exceptions import PluginError, TarError, ZipError, InstallError, CSSLoadError
from .flask_pluginkit import PluginManager
from .installer import PluginInstaller
from .web import blueprint
