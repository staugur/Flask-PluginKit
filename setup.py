# -*- coding: utf-8 -*-
"""
Flask-PluginKit
-------------

这是一个基于Flask的扩展，它旨在为你的应用添加额外的插件，甚至是第三方，而不用修改核心代码。


使用概述(Overview)
`````````````````

安装(Installation)

.. code:: bash

    $ pip install flask-pluginkit

普通模式(Usage)

.. code:: python

    from flask_pluginkit import PluginManager
    plugin = PluginManager(app)

工厂模式(The factory pattern)

.. code:: python

    from flask_pluginkit import PluginManager
    plugin = PluginManager()
    plugin.init_app(app)

资源(Resources)
`````````

* `GitHub <https://github.com/staugur/Flask-PluginKit>`_
* `Author <https://www.saintic.com>`_
* `Docs <http://docs.saintic.com/754273>`_
* `Issues <https://github.com/staugur/Flask-PluginKit/issues>`_

"""

from setuptools import setup

setup(
    name='Flask-PluginKit',
    version='0.1.0',
    url='https://github.com/staugur/Flask-PluginKit',
    license='MIT',
    author='staugur',
    author_email='staugur@saintic.com',
    description='Load and run plugins for your Flask application',
    long_description=__doc__,
    py_modules=['flask_pluginkit'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.6',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Flask',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
