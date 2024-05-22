# -*- coding: utf-8 -*-

from re import compile
from io import open as iopen
from ast import literal_eval
from setuptools import setup


def _get_version():
    version_re = compile(r"__version__\s+=\s+(.*)")

    with open("flask_pluginkit/__init__.py", "rb") as fh:
        version = literal_eval(version_re.search(fh.read().decode("utf-8")).group(1))

    return str(version)


def _get_author():
    author_re = compile(r"__author__\s+=\s+(.*)")
    mail_re = compile(r"(.*)\s<(.*)>")

    with open("flask_pluginkit/__init__.py", "rb") as fh:
        author = literal_eval(author_re.search(fh.read().decode("utf-8")).group(1))

    return (mail_re.search(author).group(1), mail_re.search(author).group(2))


def _get_readme():
    with iopen("README.rst", "rt", encoding="utf8") as f:
        return f.read()


version = _get_version()
(author, email) = _get_author()
gh = "https://github.com/staugur/Flask-PluginKit"
setup(
    name="Flask-PluginKit",
    version=version,
    url=gh,
    download_url="{gh}/releases/tag/v{v}".format(gh=gh, v=version),
    project_urls={
        "Code": gh,
        "Issue tracker": "{gh}/issues".format(gh=gh),
        "Documentation": "https://flask-pluginkit.rtfd.vip",
    },
    license="BSD 3-Clause",
    author=author,
    author_email=email,
    keywords="flask plugin",
    description="Load and run plugins for your Flask application",
    long_description=_get_readme(),
    packages=["flask_pluginkit"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=["Flask>=3.0.0", "semver>=3.0.0"],
    extras_require={"redis": ["redis>=5.0.0"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Flask",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
