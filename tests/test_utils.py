# -*- coding: utf-8 -*-

import unittest
from os import getenv
from flask_pluginkit.utils import isValidSemver, sortedSemver, isValidPrefix, \
    LocalStorage, RedisStorage, BaseStorage


class UtilsTest(unittest.TestCase):

    def test_isVer(self):
        self.assertTrue(isValidSemver("0.0.1"))
        self.assertTrue(isValidSemver("1.1.1-beta"))
        self.assertTrue(isValidSemver("1.1.1-beta+compile10"))
        self.assertFalse(isValidSemver("1.0.1.0"))
        self.assertFalse(isValidSemver("v2.19.10"))

    def test_sortVer(self):
        self.assertEqual(sortedSemver(['0.0.3', '0.1.1', '0.0.2']),
                         ['0.0.2', '0.0.3', '0.1.1'])
        self.assertRaises(TypeError, sortedSemver, 'raise')
        self.assertRaises(ValueError, sortedSemver, ["0.0.1", "v0.0.2"])

    def test_prefix(self):
        self.assertTrue(isValidPrefix('/abc'))
        self.assertTrue(isValidPrefix('/1'))
        self.assertTrue(isValidPrefix('/-'))
        self.assertTrue(isValidPrefix('/!@'))
        self.assertTrue(isValidPrefix('/='))
        self.assertTrue(isValidPrefix('/#'))
        self.assertTrue(isValidPrefix(None, allow_none=True))
        self.assertFalse(isValidPrefix(None))
        self.assertFalse(isValidPrefix('None'))
        self.assertFalse(isValidPrefix('abc'))
        self.assertFalse(isValidPrefix('1'))
        self.assertFalse(isValidPrefix('-'))
        self.assertFalse(isValidPrefix('/'))
        self.assertFalse(isValidPrefix('//'))
        self.assertFalse(isValidPrefix('//abc'))
        self.assertFalse(isValidPrefix('/1/'))
        self.assertFalse(isValidPrefix('/ '))
        self.assertFalse(isValidPrefix(' '))

    def test_localstorage(self):
        storage = LocalStorage()
        self.assertIsInstance(storage, BaseStorage)
        data = dict(a=1, b=2)
        storage.set('test', data)
        newData = storage.get('test')
        self.assertIsInstance(newData, dict)
        self.assertEqual(newData, data)
        self.assertEqual(len(storage), len(storage.list))
        # test setitem getitem
        storage["test"] = "hello"
        self.assertEqual("hello", storage["test"])
        # Invalid, LocalStorage did not implement this method
        del storage["test"]
        self.assertEqual("hello", storage["test"])
        self.assertIsNone(storage['_non_existent_key_'])
        self.assertEqual(1, storage.get('_non_existent_key_', 1))
        # test other index
        storage.index = '_non_existent_index_'
        self.assertEqual(0, len(storage))

    def test_redisstorage(self):
        """Run this test when it detects that the environment variable
        FLASK_PLUGINKIT_TEST_REDISURL is valid
        """
        redis_url = getenv("FLASK_PLUGINKIT_TEST_REDISURL")
        if redis_url:
            from redis.exceptions import DataError
            storage = RedisStorage(redis_url=redis_url)
            self.assertIsInstance(storage, BaseStorage)
            self.assertRaises(DataError, storage.set, 'test', dict(a=1, b=2))
            storage['test'] = 1
            self.assertEqual(storage['test'], b"1")
            self.assertEqual(len(storage), len(storage.list))
            self.assertEqual(len(storage), storage._db.hlen(storage.index))
            self.assertIsNone(storage['_non_existent_key_'])
            self.assertEqual(1, storage.get('_non_existent_key_', 1))
            # RedisStorage allow remove
            del storage['test']
            self.assertIsNone(storage['test'])
            # test other index
            storage.index = '_non_existent_index_'
            self.assertEqual(0, len(storage))

    def test_basestorage(self):
        class MyStorage(BaseStorage):
            pass
        ms = MyStorage()
        with self.assertRaises(AttributeError):
            ms.get('test')


if __name__ == '__main__':
    unittest.main()
