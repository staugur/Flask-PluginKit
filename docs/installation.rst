.. _installation:

Installation
============

Python Version
--------------

We recommend using the latest version of Python 3.
Flask-PluginKit supports Python 3.6 and newer, Python 2.7, and PyPy.

Dependencies
------------

These distributions will be installed automatically
when installing Flask-PluginKit.

* `Flask`_ is a Lightweight Web Application Framework Written in Python,
  theoretically support 0.9 and later versions.

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

If you are using Python 2, the venv module is not available.
Instead, install `virtualenv`_.

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
