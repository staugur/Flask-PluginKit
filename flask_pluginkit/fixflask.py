# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.fixflask
    ~~~~~~~~~~~~~~~~~~~~~~~~

    fixflask: A class inheritance of flask, and added some additional functionality.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import sys
from flask.app import Flask as BaseFlask, setupmethod
from flask.helpers import send_from_directory
from werkzeug.exceptions import NotFound
from .utils import string_types


class Flask(BaseFlask):
    """The current class code from flask-multistatic, support for multiple static folder,
    in addition, also increases the before_req decorator to set the xx the highest priority
    """

    def _get_static_folder(self):
        if self._static_folder is not None:
            return [os.path.join(self.root_path, folder)
                    for folder in self._static_folder]

    def _set_static_folder(self, value):
        folders = value
        if isinstance(folders, string_types):
            folders = [value]
        self._static_folder = folders
    static_folder = property(_get_static_folder, _set_static_folder)
    del _get_static_folder, _set_static_folder

    # Use the last entry in the list of static folder as it should be what
    # contains most of the files
    def _get_static_url_path(self):
        if self._static_url_path is not None:
            return self._static_url_path
        if self.static_folder is not None:
            return '/' + os.path.basename(self.static_folder[-1])

    def _set_static_url_path(self, value):
        self._static_url_path = value
    static_url_path = property(_get_static_url_path, _set_static_url_path)
    del _get_static_url_path, _set_static_url_path

    def send_static_file(self, filename):
        """Function used internally to send static files from the static
        folder to the browser.

        .. versionadded:: 1.0.1
        """
        if not self.has_static_folder:
            raise RuntimeError('No static folder for this object')

        # Ensure get_send_file_max_age is called in all cases.
        # Here, we ensure get_send_file_max_age is called for Blueprints.
        cache_timeout = self.get_send_file_max_age(filename)

        folders = self.static_folder
        if isinstance(self.static_folder, string_types):
            folders = [self.static_folder]

        for directory in folders:
            try:
                return send_from_directory(
                    directory, filename, cache_timeout=cache_timeout)
            except NotFound:
                pass
        raise NotFound()

    @setupmethod
    def before_request_top(self, f):
        """Registers a function to run before each request.

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
