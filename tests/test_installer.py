# -*- coding: utf-8 -*-

import os
import unittest
from flask_pluginkit import PluginInstaller
from flask_pluginkit.utils import check_url


class PITest(unittest.TestCase):
    def setUp(self):
        self.pi = PluginInstaller(".")

    def test_addPlugin(self):
        urls = [
            "https://static.saintic.com/download/thirdApp/JQueryAvatarPreviewCut.zip",
            "https://static.saintic.com/download/thirdApp/syncthing-linux-amd64-v0.14.45.tar.gz",
            "https://codeload.github.com/saintic/jwt/zip/master",
            "https://codeload.github.com/staugur/Flask-PluginKit/tar.gz/v3.0.0",
        ]
        pkg = os.path.join(self.pi.plugin_abspath, "jwt-master")
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


if __name__ == "__main__" and not os.getenv("TRAVIS"):
    unittest.main()
