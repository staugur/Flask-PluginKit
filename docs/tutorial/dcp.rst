.. _dcp:

Dynamic Connection Point
========================

Description
-----------

The connection point abbreviation is dcp.

It doesn't need to be returned with **register**, even you may rarely use it.

Dynamic connection points, dynamic registration and execution functions
return the results to the template, which is inspired by `flask-plugins`_.
However, it has been simplified to support pushing multiple functions
in the application context, and in the template to get the execution results
of all functions under the event (safe HTML code returned by
:class:`~flask.Markup`).

.. _flask-plugins: https://flask-plugins.readthedocs.io/#events

The public push method is :func:`~flask_pluginkit.push_dcp`, in addition,
it can be managed using :attr:`~flask_pluginkit.PluginManager._dcp_manager`,
it is an instance of :class:`~flask_pluginkit.utils.DcpManager`.
Flask-PluginKit will update the template with a global method **emit_dcp** when
it loads, the method called is :meth:`~flask_pluginkit.utils.DcpManager.emit`.

Example
-------

- Push dcp

.. code-block:: python

    from flask_pluginkit import push_dcp

    def test(*args, **kwargs):
        return 'hello <b>dcp</b>'

    with app.app_context():
        push_dcp('test', test)

- Call in template

.. code-block:: html

    <div>
        {{ emit_dcp('test', 1, 2, 3, a='a', b='b', c='c') }}
    </div>

