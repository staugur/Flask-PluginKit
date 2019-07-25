.. _errhandler:

Error Handler Extension Point
=============================

Description
-----------

The extension point abbreviation is errhandler.

Error handler, this extension point is also very simple, return the
errhandler field through register, this field requires the format is
{http-code: error-view-func, other-code: other-error-view-func}, and
the key is a standard HTTP code (such as 404, 403, 500), the value is an
error handler view function, and supports multiple error code handling.

The Flask-PluginKit loads errhandler via
:meth:`~flask_pluginkit.PluginManager._error_handler`, this method will
detect errhandler rules and specific content.

It should be noted that if multiple duplicate error handling functions
are eventually overwritten, only one is valid. The error handling function
can be written in the official documentation is `flask-error-handlers`_.

.. _flask-error-handlers:
    https://flask.palletsprojects.com/errorhandling/#error-handlers

Example
-------

- Plugin registration for errhandler

.. code-block:: python

    from flask import jsonify

    def permission_deny(error):
        return jsonify(dict(status=403, msg="permission deny")),403

    def register():
        return {
            'errhandler': {403: permission_deny},
        }
