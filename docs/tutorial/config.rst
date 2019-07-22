.. _config:

Configuration
=============

Description
-----------

The configuration here refers to the configuration information of the plugin.
In general, the plugin needs to obtain the configuration of the
web application. In the first case, the python module of the plugin needs
configuration information, and the second case is that the template code of
the plugin needs to obtain configuration information.

In the first case, the plugin can be imported directly into the configuration
file module, or use ``current_app.config``.

In the second case, the Flask itself already supports the configuration of
**current_app.config** directly in the template using config, but the
old version (before 0.10) may not support it, so Flask-PluginKit adds a
template "global variable", :meth:`~flask_pluginkit.PluginManager.emit_config`,
the configuration passed to :class:`~flask_pluginkit.PluginManager` with
the :attr:`~flask_pluginkit.PluginManager.pluginkit_config` parameter and
the configuration of **current_app.config** can be obtained directly.

.. note::

    The **emit_config** will first look in the **pluginkit_config** parameter.
    If not found, then find **current_app.config**.
    If still can't find, return None.

Example
-------

- User Definition

.. code-block:: python

    from flask_pluginkit import PluginManager
    PluginManager(app, pluginkit_config=dict(HELLO="WORLD"))

- Plugin call

Suppose the following code is a template file under a plugin,
get HELLO and DEBUG configuration:

.. code-block:: html

    <div>
        Hello: {{ emit_config("HELLO") }}
    </div>
    <div>
        App is debug: {{ emit_config("DEBUG") }}
    </div>
