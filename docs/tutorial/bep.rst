.. _bep:

Blueprint Extension Point
=========================

Description
-----------

The extension point abbreviation is bep.

This extension point is very simple, just add a blueprint to the web
application, no different from the normal blueprint.

The plugin needs to return the bep field via register. The bep data type
returned is a dictionary with the format
{blueprint: Blueprint Instance, prefix: /your_blueprint_url_prefix, parent: Name}.
Only one blueprint is currently supported.

.. versionchanged:: 3.6.2

    Support Flask2.0 nested blueprint with the `parent` param(beta).
    But only blueprints of other plugins can be nested.

The Flask-PluginKit loads bep via
:meth:`~flask_pluginkit.PluginManager._bep_handler`, this method will
detect bep rules and specific content.

The blueprint can be mounted under None or under other prefixes.
Flask-PluginKit does not detect blueprint routing,
as long as the prefix is legal.

The user only needs to ensure that the plugin is harmless and does not
pollute your original application. Others are plugin developers.

If you just want to add the view to the existing blueprint,
you can refer to :ref:`vep-on-blueprint`

Example
-------

- Plugin registration for bep

.. code-block:: python

    from os.path import dirname, abspath
    from flask import Blueprint

    bp = Blueprint('test', 'test', root_path=dirname(abspath(__file__)))

    @bp.route('/')
    def your_route():
        pass

    def register():
        return dict(
            bep=dict(
                blueprint=bp,
                prefix='/test'
            )
        )
