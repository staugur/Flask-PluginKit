# -*- coding: utf-8 -*-
"""
    flask_pluginkit
    ~~~~~~~~~~~~~~~

    Load and run plugins for your Flask application

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

from .pluginkit import PluginManager, push_dcp
from .utils import (
    LocalStorage,
    RedisStorage,
    JsonResponse,
    ExpiredLocalStorage,
)
from ._installer import PluginInstaller
from ._web import blueprint

__author__ = "Hiroshi.tao <me@tcw.im>"

__version__ = "3.10.0"

__all__ = [
    "PluginManager",
    "LocalStorage",
    "RedisStorage",
    "JsonResponse",
    "PluginInstaller",
    "push_dcp",
    "blueprint",
    "ExpiredLocalStorage",
]
