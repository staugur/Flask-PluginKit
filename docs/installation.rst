.. _installation:

Installation
============

Python Version
--------------

Flask-PluginKit only supports Python 3.8+.

Dependencies
------------

These distributions will be installed automatically
when installing Flask-PluginKit.

* `Flask`_ is a Lightweight Web Application Framework Written in Python,
  theoretically support 3.0.0+.

* `semver`_ is a Semantic Version Control Specification.

.. _Flask: https://www.palletsprojects.com/p/flask/
.. _semver: https://semver.org

Virtual environments
--------------------

We recommend using a virtual environment to manage the dependencies for
your project, both in development and in production.

Of course, this requires you to understand it yourself.

Python 3 comes bundled with the :mod:`venv` module to
create virtual environments.

Install Flask-PluginKit
-----------------------

Within the activated virtual environment or global environment,
use the following command to install Flask-PluginKit:

.. code-block:: sh

    $ pip install -U Flask-PluginKit

Flask-PluginKit is now installed. Check out the :doc:`/quickstart` or
go to the :doc:`Documentation Overview </index>`.

Install development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to work with the latest Flask-PluginKit code
before it's released, install or update the code from the master branch:

.. code-block:: sh

    $ pip install -U git+https://github.com/staugur/Flask-PluginKit.git@master

.. _virtualenv: https://virtualenv.pypa.io/
