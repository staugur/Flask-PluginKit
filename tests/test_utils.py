# -*- coding: utf-8 -*-

import os
import unittest
from flask_pluginkit import isValidSemver, sortedSemver, LocalStorage


class UtilsTest(unittest.TestCase):

    def test_isVer(self):
        self.assertTrue(isValidSemver("0.0.1"))
        self.assertTrue(isValidSemver("1.1.1-beta"))
        self.assertTrue(isValidSemver("1.1.1-beta+compile10"))
        self.assertFalse(isValidSemver("1.0.1.0"))
        self.assertFalse(isValidSemver("v2.19.10"))

    def test_sortVer(self):
        self.assertEqual(sortedSemver(['0.0.3', '0.1.1', '0.0.2']), ['0.0.2', '0.0.3', '0.1.1'])
        self.assertRaises(TypeError, sortedSemver, 'raise')
        self.assertRaises(ValueError, sortedSemver, ["0.0.1", "v0.0.2"])

    def test_localstorage(self):
        storage = LocalStorage()
        data = dict(a=1)
        storage.set('test', data)
        newData = storage.get('test')
        self.assertIsInstance(newData, dict)
        self.assertEqual(newData, data)

if __name__ == '__main__':
    unittest.main()
