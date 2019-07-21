# -*- coding: utf-8 -*-
"""
    flask_pluginkit
    ~~~~~~~~~~~~~~~

    Load and run plugins for your Flask application

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

from .pluginkit import PluginManager
from .utils import Flask, LocalStorage, RedisStorage

__author__ = "staugur <staugur@saintic.com>"

__version__ = "3.0.1"

__all__ = [
    "Flask",
    "PluginManager",
    "LocalStorage",
    "RedisStorage",
]
