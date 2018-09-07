# -*- coding: utf-8 -*-

import os
import unittest
from flask_pluginkit import PluginInstaller


class PITest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(PITest, self).__init__(*args, **kwargs)
        self.pi = PluginInstaller('.')

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_getFilename(self):
        #https://static.saintic.com/test/
        urls = [
            'https://static.saintic.com/download/thirdApp/JQueryAvatarPreviewCut.zip',
            'https://static.saintic.com/download/thirdApp/syncthing-linux-amd64-v0.14.45.tar.gz',
            'https://codeload.github.com/staugur/passport/tar.gz/v1.0.3',
            'https://codeload.github.com/staugur/passport/zip/v1.0.3'
        ]
        pkg = os.path.join(self.pi.plugin_abspath, "passport-1.0.3")
        res = self.pi.addPlugin(url=urls[3])
        self.assertIsInstance(res, dict)
        self.assertEqual(res["code"], 0)
        self.assertTrue(os.path.isdir(pkg))
        self.assertTrue(self.pi._PluginInstaller__isValidUrl(urls[0]))
        self.assertTrue(self.pi._PluginInstaller__isValidUrl("http://192.168.1.1/j.zip"))
        self.assertFalse(self.pi._PluginInstaller__isValidUrl("j.zip"))
        self.assertTrue(self.pi._PluginInstaller__isValidFilename("j.zip"))
        self.assertTrue(self.pi._PluginInstaller__isValidFilename("j.tar.gz"))
        self.assertFalse(self.pi._PluginInstaller__isValidFilename("j.gz"))
        self.assertFalse(self.pi._PluginInstaller__isValidFilename("j.rar"))
        res = self.pi.removePlugin(pkg)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["code"], 0)

if __name__ == '__main__':
    unittest.main()
