# -*- coding: utf-8 -*-

import re
import ast
from setuptools import setup

def _get_meta(meta):
    """Metadata can be obtained by this function
    when the plugin cannot be imported directly.

    version = _get_meta("version")
    license = _get_meta("license")
    description = _get_meta("description")
    """
    pat = re.compile(r'__%s__\s+=\s+(.*)' % meta)
    with open('flask_pluginkit_demo/__init__.py', 'rb') as fh:
        meta_str = ast.literal_eval(pat.search(fh.read().decode('utf-8')).group(1))
    return str(meta_str)

def _get_author():
    mail_re = re.compile(r'(.*)\s<(.*)>')
    author_email = _get_meta("author")
    return (mail_re.search(author_email).group(1), mail_re.search(author_email).group(2))

(author, email) = _get_author()
setup(
    name='flask-pluginkit-demo',
    version=_get_meta("version"),
    license=_get_meta("license"),
    author=author,
    author_email=email,
    url='https://github.com/flask-pluginkit/demo',
    download_url="https://github.com/flask-pluginkit/demo",
    keywords="flask-pluginkit",
    description=_get_meta("description"),
    packages=['flask_pluginkit_demo',],
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'Flask-PluginKit>=3.0.0'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)