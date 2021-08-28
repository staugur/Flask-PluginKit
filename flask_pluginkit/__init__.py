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
    Flask,
    LocalStorage,
    RedisStorage,
    MongoStorage,
    JsonResponse,
)
from ._installer import PluginInstaller
from ._web import blueprint

__author__ = "staugur <me@tcw.im>"

__version__ = "3.7.0"

__all__ = [
    "Flask",
    "PluginManager",
    "LocalStorage",
    "RedisStorage",
    "MongoStorage",
    "JsonResponse",
    "PluginInstaller",
    "push_dcp",
    "blueprint",
]
