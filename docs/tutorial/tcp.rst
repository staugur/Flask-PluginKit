.. _tcp:

Template Context Processors Extension Point
===========================================

Description
-----------

The extension point abbreviation is tcp.

Its role is to automatically introduce variables or functions you define into
the template environment for use in templates (like g, request, url_for).

The plugin needs to return the tcp field via register. The data type required
for this field is dict, and the format is {var_name=var, func_name=func}.

The Flask-PluginKit loads tcp via
:meth:`~flask_pluginkit.PluginManager._context_processor_handler`,
this method will detect tcp rules and specific content.

Example
-------

- Plugin registration for tcp

.. code-block:: python

    whoami = 'tcp'

    def register():
        return dict(
            tcp=dict(whoami=whoami, get_whoami=lambda :whoami)
        )

- Call in template

.. code-block:: html

    <div>
        Who are you?
        - {{ whoami }}
        - {{ get_whoami() }}
    </div>
