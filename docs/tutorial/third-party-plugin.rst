Third party plugin
==================

Description
-----------

Third-party plugins are non-program subdirectories, local modules from
installations such as ``pip`` or ``easy_install``.

The third-party plugin is easy to use, the program can not put the plugin
code into the subdirectory, just use `pip install` to install to the local
machine, and then pass the
:attr:`~flask_pluginkit.PluginManager.plugin_packages` parameter when the
:class:`~flask_pluginkit.PluginManager` is initialized.

This means that anyone can write a package and publish it to pypi, and
the user writes **requirements.txt** and installs the dependent plugin,
which is called in the initialization, and almost no need to worry about
subsequent third-party plugin upgrades.

Local Plugin
------------

It's a package under the web application, which is part of the web application,
and the plugin developer is the user, more see :ref:`core-plugin-structure`.

How to develop plugins?
-----------------------

The local plugin only needs the first step, and the third party plugin needs
to write ``setup.py``, which requires the next few steps.

1. First create a package, the metadata and register functions should be
   written in ``__init__.py``, the core code can also be written in this
   file, of course, the recommended approach is to separate the module.

2. The first step is actually the process of writing local plugins.
   In this step, you need to write `setup.py`, so that local plugins
   can be (published in pypi, optionally) used by others through pip:

.. code-block:: python

    from setuptools import setup
    setup(
        name='flask_pluginkit_demo',
        packages=['flask_pluginkit_demo',],
        include_package_data=True,
        ..
    )

3. If your plugin contains template directory or static directory, you need
   to write an additional manifest file ``MANIFEST.in``:

.. code-block:: text

    recursive-include flask_pluginkit_demo/templates *
    recursive-include flask_pluginkit_demo/static *

4. Testing, Release

The modules required by the following commands can be installed like this:

.. code-block:: bash

    $ pip install -U pip twine wheel setuptools

4.1 Use ``pip install .`` to install to the local environment and
test the plugin functionality.

4.2 If the plugin is as expected, it can be packaged and the command is:
``python setup.py sdist bdist_wheel``, more parameters to adjust themselves.

4.3 Before the official release, you can post to test.pypi.org, which is
the official pypi test site. The package inside will not be used easily.
The command is:
``twine upload --repository-url https://test.pypi.org/legacy/ dist/*``

4.4 The test station can look at the interface description and so on
whether it meets the requirements of the heart, and publish it to the
official station without problems, pypi.org, the command is:
``twine upload dist/*``

5. `Third-party example <https://github.com/saintic/flask-pluginkit-demo>`_

