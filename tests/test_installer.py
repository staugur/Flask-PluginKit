# -*- coding: utf-8 -*-

import os
import unittest
from unittest import mock
from flask_pluginkit import PluginInstaller
from flask_pluginkit._installer import parse_header
from flask_pluginkit.utils import check_url


class PITest(unittest.TestCase):
    def setUp(self):
        self.pi = PluginInstaller(".")

    def test_parse_header_compat(self):
        value, params = parse_header('attachment; filename="demo.zip"')
        self.assertEqual(value, "attachment")
        self.assertEqual(params["filename"], "demo.zip")

    def test_addPlugin(self):
        urls = [
            "https://static.saintic.com/download/thirdApp/JQueryAvatarPreviewCut.zip",
            "https://static.saintic.com/download/thirdApp/syncthing-linux-amd64-v0.14.45.tar.gz",
            "https://codeload.github.com/saintic/flask-pluginkit-demo/zip/master",
            "https://codeload.github.com/staugur/Flask-PluginKit/tar.gz/v3.0.0",
        ]
        pkg = os.path.join(self.pi.plugin_abspath, "flask-pluginkit-demo-master")
        # local
        res = self.pi.addPlugin(
            method="local", filepath="/tmp/1.tar", remove=True
        )
        self.assertEqual(res["code"], 1)
        res = self.pi.addPlugin(
            method="local", filepath="/tmp/1.tbz", remove=True
        )
        self.assertEqual(res["code"], 1)
        res = self.pi.addPlugin(
            method="local", filepath="/tmp/1.tgz", remove=True
        )
        self.assertEqual(res["code"], 1)
        res = self.pi.addPlugin(
            method="local", filepath="/tmp/1.zip", remove=True
        )
        self.assertEqual(res["code"], 1)
        # remote
        res = self.pi.addPlugin(url=urls[2])
        self.assertIsInstance(res, dict)
        self.assertEqual(res["code"], 0)
        self.assertTrue(os.path.isdir(pkg))
        self.assertTrue(check_url(urls[0]))
        self.assertTrue(check_url("http://192.168.1.1/j.zip"))
        self.assertFalse(check_url("j.zip"))
        self.assertTrue(self.pi._PluginInstaller__isValidFilename("j.zip"))
        self.assertTrue(self.pi._PluginInstaller__isValidFilename("j.tar.gz"))
        self.assertFalse(self.pi._PluginInstaller__isValidFilename("j.gz"))
        self.assertFalse(self.pi._PluginInstaller__isValidFilename("j.rar"))
        res = self.pi.removePlugin(pkg)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["code"], 0)
        self.assertFalse(os.path.isdir(pkg))
        # remote
        pkg = os.path.join(self.pi.plugin_abspath, "Flask-PluginKit-3.0.0")
        res = self.pi.addPlugin(url=urls[3])
        self.assertEqual(res["code"], 0)
        res = self.pi.removePlugin(pkg)
        self.assertEqual(res["code"], 0)
        self.assertFalse(os.path.isdir(pkg))

    def test_pip_install_uses_utils_pip_install(self):
        """_pip_install delegates to utils.pip_install and passes options.

        target_dir/index/upgrade/quiet are forwarded as-is, and the result
        code reflects the pip exit status.
        """
        with mock.patch("flask_pluginkit._installer.pip_install") as m:
            m.return_value = True
            res = self.pi._pip_install(
                "flask-pluginkit-demo",
                target_dir="/tmp/plugin-target",
                index="https://pypi.org/simple",
            )
            self.assertEqual(res["code"], 0)
            m.assert_called_once_with(
                "flask-pluginkit-demo",
                target_dir="/tmp/plugin-target",
                index="https://pypi.org/simple",
            )

        with mock.patch("flask_pluginkit._installer.pip_install") as m:
            m.return_value = False
            res = self.pi._pip_install("flask-pluginkit-demo", target_dir="")
            self.assertEqual(res["code"], 1)
            self.assertEqual(res["msg"], "Installation failed with pip command")

        res = self.pi._pip_install("")
        self.assertEqual(res["code"], 1)
        self.assertEqual(res["msg"], "Invalid parameter package_or_url")


if __name__ == "__main__" and not os.getenv("TRAVIS"):
    unittest.main()
