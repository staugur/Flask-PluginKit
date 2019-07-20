Flask-PluginKit
===============

Web program plugin development kit based on flask.

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

-  `简体中文 <https://flask-pluginkit.readthedocs.io/zh_CN/latest/>`__

-  `English <https://flask-pluginkit.readthedocs.io/en/latest/>`__


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
-  Projects using *Flask-PluginKit* https://github.com/topics/flask-pluginkit
-  Official plugins based on *Flask-PluginKit* https://github.com/flask-pluginkit


LICENSE
-------

BSD 3-Clause License, more see LICENSE.


END
---

Welcome to submit pull request and star.

.. |Build Status| image:: https://travis-ci.com/staugur/Flask-PluginKit.svg?branch=master
    :target: https://travis-ci.com/staugur/Flask-PluginKit
.. |Documentation Status| image:: https://readthedocs.org/projects/flask-pluginkit/badge/?version=latest
    :target: https://flask-pluginkit.readthedocs.io/
.. |codecov| image:: https://codecov.io/gh/staugur/Flask-PluginKit/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/staugur/Flask-PluginKit
.. |PyPI| image:: https://img.shields.io/pypi/v/Flask-PluginKit.svg?style=popout
    :target: https://pypi.org/project/Flask-PluginKit/
