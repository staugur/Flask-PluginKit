Flask-PluginKit
===============

Web program plugin development kit based on Flask.

|Build Status| |Documentation Status| |codecov| |PyPI|


Installation
------------

- Production Version

    `$ pip install -U Flask-PluginKit`

- Development Version

    `$ pip install -U git+https://github.com/staugur/Flask-PluginKit.git@master`


Quickstart
----------

- The normal pattern

.. code:: python

    from flask_pluginkit import PluginManager
    pm = PluginManager(app)

- The factory pattern

.. code:: python

    from flask_pluginkit import PluginManager
    pm = PluginManager()
    pm.init_app(app)


Documentation
-------------

-  `简体中文 <https://flask-pluginkit.rtfd.vip/zh_CN/latest/>`__

-  `English <https://flask-pluginkit.rtfd.vip/en/latest/>`__


Contributing
------------

For setting up the development environment,
and how to contribute to Flask-PluginKit,
please see `contributing guidelines`_.

.. _contributing guidelines: https://github.com/staugur/Flask-PluginKit/blob/master/CONTRIBUTING.rst


Links
-----

-  GitHub https://github.com/staugur/Flask-PluginKit
-  Author https://www.saintic.com
-  Issues https://github.com/staugur/Flask-PluginKit/issues
-  Official plugins based on `Flask-PluginKit <https://github.com/saintic?q=flask-pluginkit>`_


LICENSE
-------

BSD 3-Clause License, more see LICENSE.


END
---

Welcome to submit pull request and star.

.. |Build Status| image:: https://github.com/staugur/Flask-PluginKit/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/staugur/Flask-PluginKit/actions/workflows/ci.yml
.. |Documentation Status| image:: https://open.saintic.com/rtfd/badge/flask-pluginkit
    :target: https://flask-pluginkit.rtfd.vip
.. |codecov| image:: https://codecov.io/gh/staugur/Flask-PluginKit/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/staugur/Flask-PluginKit
.. |PyPI| image:: https://img.shields.io/pypi/v/Flask-PluginKit.svg?style=popout
    :target: https://pypi.org/project/Flask-PluginKit/
