# -*- coding: utf-8 -*-
"""
flask_pluginkit.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

Exception Classes

:copyright: (c) 2019 by staugur.
:license: BSD 3-Clause, see LICENSE for more details.
"""


class PluginError(Exception):
    pass


class ParamError(PluginError):
    pass


class RunError(PluginError):
    pass


class VersionError(PluginError):
    pass


class PEPError(PluginError):
    pass


class TemplateNotFound(PluginError):
    pass


class TarError(PluginError):
    pass


class ZipError(PluginError):
    pass


class InstallError(PluginError):
    pass


class NotCallableError(PluginError):
    pass
