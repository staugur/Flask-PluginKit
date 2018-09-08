# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup, Command


version = '0.1.2'


class PublishCommand(Command):

    description = "Publish a new version to pypi"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system("pip install -U setuptools twine wheel pypandoc")
        os.system("python setup.py sdist bdist_wheel")
        os.system("twine upload dist/*")
        print("V%s Released Success" % version)
        sys.exit()


try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
    long_description_content_type = "text/x-rst"
except(IOError, ImportError):
    long_description = open('README.md').read()
    long_description_content_type = "text/markdown"


setup(
    name='Flask-PluginKit',
    version=version,
    url='https://github.com/staugur/Flask-PluginKit',
    license='MIT',
    author='staugur',
    author_email='staugur@saintic.com',
    keywords="flask plugin",
    description='Load and run plugins for your Flask application',
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    py_modules=['flask_pluginkit'],
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
