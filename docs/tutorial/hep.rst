.. _hep:

Hook Extension Point
====================

Description
-----------

The extension point abbreviation is hep.

This extension point works in the flask hook function and currently supports
three hooks with the following names:

- before_request

    Before request (intercept requests are allowed)

- after_request

    After request (no exception before return)

- teardown_request

    After request (before return, with or without exception)

Other hooks will be supported later, and a exception
:class:`~flask_pluginkit.exceptions.PEPError` will be triggered if a hook name
that is not supported by the current version is used.

The plugin needs to return the hep field via register. The hep data type
returned is a dictionary with the format {hook_name: callable},
which can have multiple hep_names.

The Flask-PluginKit loads hep via
:meth:`~flask_pluginkit.PluginManager._hep_handler`, this method will
detect hep rules and specific content.

Similar to tep, each hook_name has many values for the entire web application.

When in use, the user does not care how to call, because Flask-PluginKit has
registered the hook handler at initialization time, but it should be noted
that there are different requirements for different hook type handlers:

- before_request

    This is simple, any callback function, class method, and so on can be used,
    there is no parameter, but the hook function here has a special place.
    As we all know, for Flask, if the before_request return value is not None,
    the request will be terminated. So Flask-PluginKit will try to detect the
    return value of the hook function, if it is not None, it will return,
    and the request is terminated at this moment.

- after_request

    Will pass a **response** parameter, this is the web application response
    data, is an instance of :class:`~flask.Response`, the function
    corresponding to this hook can get response, you can not return response.

- teardown_request

    Similar to after_request, this hook is triggered by the flask when
    the web exception occurs. Flask-PluginKit will pass the **exception**
    parameter to the corresponding hook function without returning.

Example
-------

- Plugin registration for hep

.. code-block:: python

    from flask import request, g, current_app

    def set_login_state():
        g.login_in = request.args.get("username") == "admin" and \
                     request.args.get("password") == "admin

    def record_access_log(response):
        log = {
            "status_code": response.status_code,
            "method": request.method,
            "ip": request.headers.get('X-Real-Ip', request.remote_addr),
            "url": request.url,
            "referer": request.headers.get('Referer'),
            "agent": request.headers.get("User-Agent"),
            "login_in": g.login_in
        }
        current_app.logger.info(log)

    def register():
        return dict(
            hep=dict(
                before_request=set_login_state,
                after_request=record_access_log
            )
        )

As above, after your program is running, the `set_login_state` function will
be executed before each request, and the `record_access_log` function will
be executed before the request returns.

