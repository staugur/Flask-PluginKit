.. _quickstart:

Quickstart
==========

Suppose you have installed the Flask-PluginKit. If you do not,
head over to the :ref:`installation` section.

The first one is to initalize it directly::

    from flask_pluginkit import PluginManager, Flask
    app = Flask(__name__)
    pm = PluginManager(app)

where as the second one is to use the factory pattern::

    from flask_pluginkit import PluginManager, Flask
    app = Flask(__name__)
    pm = PluginManager()
    pm.init_app(app)

Plugin Structure
----------------

After the first step is done, you can start developing your first plugin.

The plugin is a legal python package that needs to define some metadata and use
register to return the extension point, more see :ref:`core-plugin-structure`

For example, the structure of small plugin can look like this:

.. sourcecode:: text

    my_plugin
    |-- __init__.py

the structure of a more complex plugin can also look like this:

.. sourcecode:: text

    my_plugin
    ├── __init__.py
    ├── static
    │   └── example
    │       └── demo.css
    └── templates
        └── example
            └── demo.html

Hello World
-----------

For a better understanding you can also have a look at the `example`_,
it contains a local plugin and a third party plugin.

Now, let's start with a simple plugin example. The plugin name is helloworld.

This simple helloworld example can be found `here`_.

First, the developer wrote a simple plugin web application with only
one app.py, an index view function, and the content is:

.. code-block:: python

    # -*- coding: utf-8 -*-

    from flask import Flask
    from flask_pluginkit import PluginManager

    app = Flask(__name__)
    pm = PluginManager(app)

    @app.route('/')
    def index():
        return 'hello world'

Now, we want to limit when accessing the index view (ie /),
if ip is 127.0.0.1, then redirect to ``/limit``, proceed as follows:

1. Create helloworld directory

.. code-block:: bash

    $ mkdir -p plugins/helloworld
    $ touch plugins/__init__.py plugins/helloworld/__init__.py

2. Write ``__init__.py`` for the helloworld plugin, content is:

.. code-block:: python

    # -*- coding: utf-8 -*-

    from flask import Blueprint, jsonify, request, redirect, url_for, make_response

    __plugin_name__ = "helloworld"
    __version__ = "0.1.0"
    __author__ = "staugur"

    bp = Blueprint("helloworld", "helloworld")

    @bp.route("/limit")
    def limit():
        return jsonify(dict(status=0, message="Access Denial"))

    def limit_handler():
        """I am running in before_request"""
        ip = request.headers.get('X-Real-Ip', request.remote_addr)
        if request.endpoint == "index" and ip == "127.0.0.1":
            resp = make_response(redirect(url_for("helloworld.limit")))
            resp.is_return = True
            return resp

    def register():
        return {
            "bep": dict(blueprint=bp, prefix=None),
            "hep": dict(before_request=limit_handler)
        }

3. Run

The current web application structure is as follows:

.. code-block:: text

    demo
    ├── app.py
    └── plugins
        ├── helloworld
        │   └── __init__.py # Plugin core code file
        └── __init__.py     # Only an empty file

Run app:

.. code-block:: bash

    $ FLASK_ENV=development FLASK_APP=app.py flask run --no-reload

4. Testing

    .. image:: ./_static/images/helloworld.png

For details, see :ref:`tutorial`

.. _example: https://github.com/staugur/Flask-PluginKit/tree/master/examples/fulldemo

.. _here: https://github.com/staugur/Flask-PluginKit/tree/master/examples/helloworld

