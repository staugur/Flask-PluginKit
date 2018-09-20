# -*- coding: utf-8 -*-

import os
import __init__, unittest
from flask_pluginkit import PluginInstaller

def __getattr__(self, name):
    if name in ("assertIs", "assertIsNone"):
        statement = "a is b"
    elif name in ("assertIsNot", "assertIsNotNone"):
        statement = "a is not b"
    elif name == "assertIn":
        statement = "a in b"
    elif name == "assertNotIn":
        statement = "a not in b"
    elif name == "assertIsInstance":
        statement = "isinstance(a, b)"
    elif name == "assertIsNotInstance":
        statement = "not isinstance(a, b)"
    else:
        statement = "True"
 
    def wrapper(a=None, b=None):
        return self.assertTrue(eval(statement))
    return wrapper
 
unittest.TestCase.__getattr__ = __getattr__


class PITest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(PITest, self).__init__(*args, **kwargs)
        self.pi = PluginInstaller('.')

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_addPlugin(self):
        urls = [
            'https://static.saintic.com/download/thirdApp/JQueryAvatarPreviewCut.zip',
            'https://static.saintic.com/download/thirdApp/syncthing-linux-amd64-v0.14.45.tar.gz',
            'https://codeload.github.com/staugur/jwt/zip/master',
            'https://codeload.github.com/staugur/passport/tar.gz/v1.0.3',
        ]
        pkg = os.path.join(self.pi.plugin_abspath, "jwt-master")
        #local
        res = self.pi.addPlugin(method='local', filepath='/tmp/1.tar', remove=True)
        self.assertEqual(res["code"], 1)
        res = self.pi.addPlugin(method='local', filepath='/tmp/1.tbz', remove=True)
        self.assertEqual(res["code"], 1)
        res = self.pi.addPlugin(method='local', filepath='/tmp/1.tgz', remove=True)
        self.assertEqual(res["code"], 1)
        res = self.pi.addPlugin(method='local', filepath='/tmp/1.zip', remove=True)
        self.assertEqual(res["code"], 1)
        #remote
        res = self.pi.addPlugin(url=urls[2])
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
