# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='Flask-PluginKit',
    version='0.1.0',
    url='https://github.com/staugur/Flask-PluginKit',
    license='MIT',
    author='staugur',
    author_email='staugur@saintic.com',
    keywords="flask plugin",
    description='Load and run plugins for your Flask application',
    long_description=long_description,
    long_description_content_type='text/markdown',
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
