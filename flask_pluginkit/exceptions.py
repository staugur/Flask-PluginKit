# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Exception Classes

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""


class PluginError(Exception):
    pass


class TarError(PluginError):
    pass


class ZipError(PluginError):
    pass


class InstallError(PluginError):
    pass


class CSSLoadError(PluginError):
    pass


class DCPError(PluginError):
    pass


class VersionError(PluginError):
    pass
