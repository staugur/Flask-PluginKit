# -*- coding: utf-8 -*-

import unittest
import urllib2
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
        self.pi.remote_download(urls[1])


if __name__ == '__main__':
    unittest.main()
