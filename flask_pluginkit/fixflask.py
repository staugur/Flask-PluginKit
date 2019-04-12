# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.fixflask
    ~~~~~~~~~~~~~~~~~~~~~~~~

    fixflask: A class inheritance of flask, and added some additional functionality.

    :copyright: (c) 2018 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

import os
import sys
from flask.app import setupmethod
try:
    from flask_multistatic import MultiStaticFlask as _BaseFlask
except ImportError:
    from flask import Flask as _BaseFlask


class Flask(_BaseFlask):

    @setupmethod
    def before_request_top(self, f):
        """Registers a function to run before each request. Priority First.

        The usage is equivalent to the :func:`before_request` decorator, and 
        before_request registers the function at the end of the before_request_funcs, while 
        this decorator registers the function at the top of the before_request_funcs (index 0).

        Because flask-pluginkit has registered all cep into the app at load time, 
        if your web application uses before_request and plugins depend on one of them (like g), the plugin will not run properly, 
        so your web application should use this decorator at this time.

        .. versionadded:: 1.0.1
        """
        self.before_request_funcs.setdefault(None, []).insert(0, f)
        return f

    @setupmethod
    def before_request_second(self, f):
        """Registers a function to run before each request. Priority Second.

        ..versionadded:: 2.4.0
        """
        self.before_request_funcs.setdefault(None, []).insert(1, f)
        return f
