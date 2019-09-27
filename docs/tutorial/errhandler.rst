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

However, there is now a new format: [{error=exception_class, handler=func},
{error=err_code, handler=func}], this form allows you to use http-code to
handle error codes while allowing a custom exception class to be passed in.
And the associated processor (capturing the handler for this exception class),
please refer to the Flask documentation for this class-based form of code.

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

    class ApiError(Exception):

        def __init__(self, code, message, status_code=200):
            super(ApiError, self).__init__()
            self.code = code
            self.message = message
            self.status_code = status_code

        def to_dict(self):
            return dict(code=self.code, msg=self.message)

    def handle_api_error(e):
        #: e is an instance of an exception class
        response = jsonify(e.to_dict())
        response.status_code = e.status_code
        return response

    def raise_api_error_view():
        #: Actively triggering ApiError in the view will be intercepted by
        #: handle_api_error and return json response.
        raise ApiError(10000, "err_message")

    def register():
        return {
            'vep': dict(rule='/api_error', view_func=raise_api_error_view),
            'errhandler': [
                dict(error=403, handler=permission_deny),
                dict(error=ApiError, handler=handle_api_error)
            ]
        }
