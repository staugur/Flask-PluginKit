Plugin Core
===========

.. _core-minimal-plugin:

Minimal Plugin
--------------

.. code-block:: python

    # -*- coding: utf-8 -*-

    __plugin_name__ = "Demo"
    __author__ = "Mr.tao <staugur@saintic.com>"
    __version__ = "0.1.1"

    def register():
        return {}

However, this plugin doesn't make any sense, it just means
a valid plugin content, whether it's a local plugin or a third-party plugin,
the core part is the same.

The mini plugin above, which starts and ends with ``__``, is called metadata,
which is the most important information for getting plugins.

The ``register`` function is used to return the extension point.
Let's explain it one by one.

.. _core-plugin-structure:

Plugin Structure
----------------

The most minimal plugin needs to have at least it's own directory.
The directory must contain the ``__init__.py`` file, otherwise
it is not considered a plugin!

The core code of the plugin can be written in other modules of the package,
then returned in **__init__.py** using the ``register`` function, and
this file contains the metadata required to register the plugin.

In `__init__.py`, you can write your plugin code all in. Of course,
the recommended way is to create a module with another name under
the plugin package. Write your functions, class, variable, and so on,
then import the module in `__init__.py` and
use register to return the extension point.

The project structure of a complete plugin web application is
probably like this:

.. code-block:: text

    your_project/
    ├── app.py
    ├── config.py
    ├── libs
    │   └── __init__.py
    ├── LICENSE
    ├── plugins
    │   ├── __init__.py
    │   └── local_plugin_demo    # A local plugin
    │       ├── _core.py
    │       ├── __init__.py
    │       ├── license.txt
    │       ├── readme.txt
    │       ├── static
    │       │   └── demo.css
    │       ├── template
    │       │   └── demo
    │       │       └── demo.html
    │       └── _util.py
    ├── README.md
    ├── requirements.txt
    ├── utils
    │   └── __init__.py
    └── views
        └── __init__.py

.. _core-metadata:

metadata
---------

Below are all supported metadata configuration items, please note that
the first three are required:

- ``__plugin_name__``

    Your plugin name is not strictly required to be consistent
    with the plugin directory name.

- ``__author__``

    Plugin Author

- ``__version__``

    Plugin Version, compliance with `Semantic Version 2.0`_ Rules.

- ``__description__``

    What is the use of plugin description information.

- ``__url__``

    Plugin Homepage

- ``__license__``

    Plugin LICENSE

- ``__license_file__``

    The plugin LICENSE detail file. Your plugin directory should have
    a LICENSE file.

- ``__readme_file__``

    The plugin profile should have a README description file
    in your plugin directory.

- ``__state__``

    The plugin Status, enabled (default) or disabled.

.. _Semantic Version 2.0: https://semver.org

.. _core-register:

register
--------

This function is also required, it should be defined or imported
in `__init__.py`. Flask-PluginKit will call this function when loading,
return data is dict, contains various types of extension points,
such as:

.. code-block:: python

    def register():
        return dict(
            bep=dict(),
            hep=dict(),
            tep=dict(),
            errhandler=dict(),
            filter=dict(),
            tcp=dict(),
        )

For the extension points returned, please see the following sections.

.. _core-enabling-and-disabling-plugins:

Enabling and Disabling Plugins
------------------------------

This extension, uses a different approach for handling plugins.

Anyway, local plugins (a subdirectory located in the application,
such as plugins, is a package) or third-party plugins (which can be pypi
or from git, svn, etc.), should be installed in the local environment.

Plugins are enabled by default, and there are two ways to
enable or disable a plugin.

The first method is to set the metadata ``__state__`` value to  **enabled**
or **disabled**.

The second method is to add the ``ENABLED`` or ``DISABLED`` file in the
plugin's root directory, without changing the source code.
This can either be done by hand or with the method provided
by :meth:`~flask_pluginkit.PluginManager.disable_plugin` or
:meth:`~flask_pluginkit.PluginManager.enable_plugin`.

.. note::

    The second method has a higher priority than the first one, and
    the DISABLED file has a higher priority than the ENABLED file.

The directory structure of a disabled plugin is shown below.

.. sourcecode:: text

    my_plugin
    |-- DISABLED    # Just add a empty file named "DISABLED"
    |-- __init__.py

.. warning::

    The server needs to be restarted or reloaded to disable the plugin.
    This is a limitation of Flask. However, it is possible, to restart
    the application by sending a HUP signal to the application server.

    The following code snippets, are showing how this can be done with
    the WSGI server gunicorn. Gunicorn has be to started in
    daemon (``--daemon``) mode in order for this to work.

    You can use the command to manually reload:

    .. sourcecode:: bash

        $ kill -HUP Your_APP_Gunicorn_master_pid

    or direct restart (kill, then start).

    In web applications, according to previous tests, it should
    use :func:`os.getppid` instead of :func:`os.getpid`
    to get the master pid of gunicorn, and send SIGHUP signal to master pid.

    For security, the process name should be verified!

    .. sourcecode:: python

        @app.route('/reload')
        def reload():
            os.kill(os.getppid(), signal.SIGHUP)

    This feature is implemented in v3.3.0, reference document :doc:`/webmanager`
