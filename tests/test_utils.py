# -*- coding: utf-8 -*-

import os
import unittest
from flask_pluginkit import isValidSemver, sortedSemver


class UtilsTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(UtilsTest, self).__init__(*args, **kwargs)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_isVer(self):
        self.assertTrue(isValidSemver("0.0.1"))
        self.assertTrue(isValidSemver("1.1.1-beta"))
        self.assertTrue(isValidSemver("1.1.1-beta+compile10"))
        self.assertFalse(isValidSemver("1.0.1.0"))
        self.assertFalse(isValidSemver("v2.19.10"))

    def test_sortVer(self):
        self.assertEqual(sortedSemver(['0.0.3','0.1.1','0.0.2']), ['0.0.2', '0.0.3', '0.1.1'])
        self.assertRaises(TypeError, sortedSemver, 'raise')
        self.assertRaises(ValueError, sortedSemver, ["0.0.1", "v0.0.2"])


if __name__ == '__main__':
    unittest.main()
