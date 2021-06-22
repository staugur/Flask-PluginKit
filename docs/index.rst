===============
Flask-PluginKit
===============

Welcome to Flask-PluginKit's documentation.

This is a Flask-based plugin development kit that supports multiple
extension types that you can use to create plugins for web applications
with little or no change to the core code.

Q: Why did you develop this extension?

A: Play.

Get started with :ref:`installation` and then get an overview with the
:ref:`quickstart`. There is also a more detailed :ref:`tutorial`
that shows how to create a small but complete plugin with Flask-PluginKit.
The rest of the docs describe each component of Flask-PluginKit in detail,
with a full reference in the :ref:`api` section.

Flask-PluginKit depends on the `Flask`_.

The plugin based on Flask-PluginKit can be a local directory or a third-party
package (such as pypi), which is the `official plugin organization`_.

.. image:: https://github.com/staugur/Flask-PluginKit/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/staugur/Flask-PluginKit/actions/workflows/ci.yml

.. image:: https://codecov.io/gh/staugur/Flask-PluginKit/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/staugur/Flask-PluginKit

.. image:: https://img.shields.io/pypi/v/Flask-PluginKit.svg?style=popout
    :target: https://pypi.org/project/Flask-PluginKit/

.. note::

    V3.3.1 or later is compatible with some data in v2.x, refer :ref:`faq-cov`

User Guide
----------

Describe in detail how to develop a plugin using Flask-PluginKit.

.. toctree::
    :maxdepth: 2

    installation
    quickstart
    tutorial/index
    webmanager


API Reference
-------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
    :maxdepth: 2

    api


Additional Notes
----------------

Some additional instructions, styleguide, changelog, contributing,
will be supplemented by others.

.. toctree::
    :maxdepth: 2

    changelog
    contributing
    faq
    Pocoo Styleguide <https://flask.palletsprojects.com/styleguide/>


.. _Flask: https://www.palletsprojects.com/p/flask/

.. _official plugin organization: https://github.com/saintic?q=flask-pluginkit
