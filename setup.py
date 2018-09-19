# -*- coding: utf-8 -*-
"""
Flask-PluginKit
===============

基于Flask的插件式开发工具(Web program plugin development kit based on flask).

使用概述(Overview)
~~~~~~~~~~~~~~~~~~

安装(Installation)

::

    $ pip install flask-pluginkit

普通模式(Usage)

::

    from flask_pluginkit import PluginManager
    plugin = PluginManager(app)

工厂模式(The factory pattern)

::

    from flask_pluginkit import PluginManager
    plugin = PluginManager()
    plugin.init_app(app)

文档(Documentation)
~~~~~~~~~~~~~~~~~~~

`点击这(Click here) <http://docs.saintic.com/754273>`__

LICENSE
~~~~~~~

`MIT LICENSE <http://flask.pocoo.org/docs/license/#flask-license>`__

"""

import os
import sys
from setuptools import setup, Command


version = '0.1.5'


class PublishCommand(Command):

    description = "Publish a new version to pypi"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system("pip install -U setuptools twine wheel")
        os.system("python setup.py sdist bdist_wheel")
        os.system("twine upload dist/*")
        print("V%s Released Success" % version)
        sys.exit()


setup(
    name='Flask-PluginKit',
    version=version,
    url='https://github.com/staugur/Flask-PluginKit',
    license='MIT',
    author='staugur',
    author_email='staugur@saintic.com',
    keywords="flask plugin",
    description='Load and run plugins for your Flask application',
    long_description=__doc__,
    long_description_content_type="text/x-rst",
    packages=['flask_pluginkit'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.6',
    ],
    cmdclass={
        'publish': PublishCommand,
    },
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
