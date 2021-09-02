# -*- coding: utf-8 -*-

import unittest
from os import system
from re import compile
from io import open as iopen
from ast import literal_eval
from setuptools import setup, Command


def test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests", pattern="test_*.py")
    return test_suite


def _get_version():
    version_re = compile(r"__version__\s+=\s+(.*)")

    with open("flask_pluginkit/__init__.py", "rb") as fh:
        version = literal_eval(
            version_re.search(fh.read().decode("utf-8")).group(1)
        )

    return str(version)


def _get_author():
    author_re = compile(r"__author__\s+=\s+(.*)")
    mail_re = compile(r"(.*)\s<(.*)>")

    with open("flask_pluginkit/__init__.py", "rb") as fh:
        author = literal_eval(
            author_re.search(fh.read().decode("utf-8")).group(1)
        )

    return (mail_re.search(author).group(1), mail_re.search(author).group(2))


def _get_readme():
    with iopen("README.rst", "rt", encoding="utf8") as f:
        return f.read()


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
        system("pip install -U setuptools twine wheel")
        system("rm -rf build/ dist/ Flask_PluginKit.egg-info/")
        system("python setup.py sdist bdist_wheel")
        if self.test:
            system("twine upload -r testpypi dist/*")
        elif self.release:
            system("twine upload dist/*")
        system("rm -rf build/ dist/ Flask_PluginKit.egg-info/")
        if self.test:
            print("V%s publish to the test.pypi.org successfully" % version)
        elif self.release:
            print("V%s publish to the pypi.org successfully" % version)
        exit()


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
    test_suite="setup.test_suite",
    tests_require=["Flask>=0.11", "Flask-Classful>=0.14.0"],
    packages=["flask_pluginkit"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.3.*,!=3.5.*",
    install_requires=["Flask>=0.12", "semver>=2.10.0"],
    cmdclass={
        "publish": PublishCommand,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Flask",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
