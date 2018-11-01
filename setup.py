# -*- coding: utf-8 -*-
"""
Flask-PluginKit
===============

基于Flask的插件式开发工具(Web program plugin development kit based on flask).

使用概述(Overview)
~~~~~~~~~~~~~~~~~~

安装(Installation)

.. code:: bash

    $ pip install Flask-PluginKit

普通模式(Usage)

.. code:: python

    from flask_pluginkit import PluginManager
    plugin = PluginManager(app)

工厂模式(The factory pattern)

.. code:: python

    from flask_pluginkit import PluginManager
    plugin = PluginManager()
    plugin.init_app(app)

文档(Documentation)
~~~~~~~~~~~~~~~~~~~

`文档(Document) <https://flask-pluginkit.readthedocs.io>`__

LICENSE
~~~~~~~

`MIT LICENSE <http://flask.pocoo.org/docs/license/#flask-license>`__

"""

import os
import unittest
from setuptools import setup, Command
from flask_pluginkit import version, author, email


def test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite


class PublishCommand(Command):

    description = "Publish a new version to pypi"

    user_options = [
        # The format is (long option, short option, description).
        ("test", None, "Publish to test.pypi.org"),
        ("release", None, "Publish to pypi.org"),
    ]

    def initialize_options(self):
        """Set default values for options."""
        self.test = False
        self.release = False

    def finalize_options(self):
        """Post-process options."""
        if self.test:
            print("V%s will publish to the test.pypi.org" % version)
        elif self.release:
            print("V%s will publish to the pypi.org" % version)

    def run(self):
        """Run command."""
        os.system("pip install -U setuptools twine wheel")
        os.system("rm -rf build/ dist/ Flask_PluginKit.egg-info/")
        os.system("python setup.py sdist bdist_wheel")
        if self.test:
            os.system("twine upload --repository-url https://test.pypi.org/legacy/ dist/*")
        elif self.release:
            os.system("twine upload dist/*")
        os.system("rm -rf build/ dist/ Flask_PluginKit.egg-info/")
        if self.test:
            print("V%s publish to the test.pypi.org successfully" % version)
        elif self.release:
            print("V%s publish to the pypi.org successfully" % version)
        exit()


setup(
    name='Flask-PluginKit',
    version=version,
    url='https://github.com/staugur/Flask-PluginKit',
    download_url="https://github.com/staugur/Flask-PluginKit/releases/tag/v%s" %version,
    license='MIT',
    author=author,
    author_email=email,
    keywords="flask plugin",
    description='Load and run plugins for your Flask application',
    long_description=__doc__,
    test_suite='setup.test_suite',
    packages=['flask_pluginkit'],
    include_package_data=True,
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
