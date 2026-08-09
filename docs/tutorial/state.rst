.. _state:

State Points
============

State points are application-level lifecycle hooks that let a plugin run logic
after the plugin has been accepted as a normal extension plugin.

Unlike extension points such as ``tep``, ``hep`` or ``vep``, a state point is
not used to register new plugin capabilities. Instead, it is used to execute
application-level initialization once the Flask application is ready.

What is a state point?
----------------------

A state point is a special function that the framework detects by name.
Currently, the supported state point is ``on_app_ready(app)``.

It is called after the plugin manager has scanned, loaded and registered the
plugin into the Flask application. The hook receives the current Flask app
instance as its only parameter.

How to define it
----------------

A plugin can define a state point together with ``register()``:

.. code-block:: python

    from flask import Blueprint

    bp = Blueprint("demo", __name__)

    def register():
        return {"bep": {"blueprint": bp, "prefix": "/demo"}}

    def on_app_ready(app):
        with app.app_context():
            app.config.setdefault("DEMO_PLUGIN_ENABLED", True)
            app.extensions["demo_plugin"] = {"ready": True}

How it works
------------

The framework will call ``on_app_ready(app)`` only for plugins that provide a
regular ``register()`` entry point. A plugin that defines only
``on_app_ready`` without ``register()`` is treated as an invalid extension and
will be rejected during loading.

Typical use cases
-----------------

Use a state point when you need to:

- initialize shared services or clients
- inject configuration into the application
- register application-wide globals or template helpers
- attach objects to ``app.extensions`` for later reuse

Example
-------

.. code-block:: python

    def on_app_ready(app):
        with app.app_context():
            app.config.setdefault("PLUGIN_TITLE", "Demo")
            app.extensions["plugin"] = {
                "title": app.config["PLUGIN_TITLE"],
                "ready": True,
            }
            app.jinja_env.globals["plugin_title"] = app.config["PLUGIN_TITLE"]
