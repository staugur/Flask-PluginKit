.. _static:

Static Resource
===============

Description
-----------

Generally speaking, when accessing static files during development, you can
use Flask, but in the production environment, it is definitely a combination
of WSGI servers and web servers such as nginx and apache.
Static resources can be processed through nginx.

However, for the plugin of Flask-PluginKit, the static resources are located
in the static directory of the plugin. If there are many plugins in a web
application, then there are several static directories, so it is inconvenient
to configure through nginx.

So Flask-PluginKit customizes a view with an endpoint to access the static
directory under the plugin, and also provides a method
:meth:`~flask_pluginkit.PluginManager.emit_assets` to easily get the static
files under the plugin in the template. Of course, this method uses
:func:`~flask.url_for` internally,
so you can also use url_for to build the url.

The assets view above can customize its endpoints, pass
:attr:`~flask_pluginkit.PluginManager.static_endpoint` when initializing
:class:`~flask_pluginkit.PluginManager`, and pass
:attr:`~flask_pluginkit.PluginManager.static_url_path` to define view route
prefix. When using **emit_assets**, it will call the view function, try to
find the plugin static directory, and return 404 error if it is not found.

In addition, it is worth mentioning that the static file suffix is
currently processed.

- The suffix is **.css**

Will generate the html code for `link css`, for example:

.. code-block:: html

    <link rel="stylesheet" href="/assets/plugin/css/demo.css">

- The suffix is **.js**

Will generate the html code of `script`, for example:

.. code-block:: html

    <script src="/assets/plugin/js/demo.js"></script>

- Other suffixes

Only the url path portion of the static file will be generated.

.. note::

    In emit_assets, you can add ``_raw=True`` to let Flask-PluginKit not add
    code based on the suffix, but instead return the resource path directly.

Example
-------

- Static files

Suppose a plugin called plugin_demo has a static directory.
The file structure looks like this:

.. code-block:: text

    plugin_demo/
    ├── __init__.py
    └── static
        ├── css
        │   └── style.css
        ├── hello.png
        └── js
            └── demo.js

- Access static files

In the template, the url of the static file can be built by **emit_assets**.

.. code-block:: html

    <!DOCTYPE html>
    <html>
    <head>
        {{ emit_assets('plugin_demo','css/style.css') }}
    </head>
    <body>
        <div class="image">
            <img src="{{ emit_assets('plugin_demo', 'hello.png') }}">
        </div>

        <div class="showJsPath">
            <b>{{ emit_assets('plugin_demo', 'js/demo.js', _raw=True) }}</b>
        </div>

        {{ emit_assets("plugin_demo", filename="js/demo.js") }}
    </body>
    </html>

The actual source code for this page is this:

.. code-block:: html

    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="/assets/plugin_demo/css/style.css">
    </head>
    <body>
        <div class="image">
            <img src="/assets/plugin_demo/hello.png">
        </div>

        <div class="showJsPath">
            <b>/assets/plugin_demo/js/demo.js</b>
        </div>

        <script src="/assets/plugin_demo/js/demo.js"></script>
    </body>
    </html>
