# -*- coding: utf-8 -*-

import unittest
from os import getenv
from os.path import dirname, abspath, join
from shutil import rmtree
from flask_pluginkit.utils import (
    isValidSemver,
    sortedSemver,
    isValidPrefix,
    LocalStorage,
    RedisStorage,
    BaseStorage,
    allowed_uploaded_plugin_suffix,
    Attribution,
    check_url,
    DcpManager,
    pip_install,
    pip_list,
    pip_show,
)
from markupsafe import Markup


class UtilsTest(unittest.TestCase):
    def test_isVer(self):
        self.assertTrue(isValidSemver("0.0.1"))
        self.assertTrue(isValidSemver("1.1.1-beta"))
        self.assertTrue(isValidSemver("1.1.1-beta+compile10"))
        self.assertFalse(isValidSemver("1.0.1.0"))
        self.assertFalse(isValidSemver("v2.19.10"))

    def test_sortVer(self):
        self.assertEqual(
            sortedSemver(["0.0.3", "0.1.1", "0.0.2"]),
            ["0.0.2", "0.0.3", "0.1.1"],
        )
        self.assertRaises(TypeError, sortedSemver, "raise")
        self.assertRaises(ValueError, sortedSemver, ["0.0.1", "v0.0.2"])

    def test_prefix(self):
        self.assertTrue(isValidPrefix("/abc"))
        self.assertTrue(isValidPrefix("/1"))
        self.assertTrue(isValidPrefix("/-"))
        self.assertTrue(isValidPrefix("/!@"))
        self.assertTrue(isValidPrefix("/="))
        self.assertTrue(isValidPrefix("/#"))
        self.assertTrue(isValidPrefix(None, allow_none=True))
        self.assertFalse(isValidPrefix(None))
        self.assertFalse(isValidPrefix("None"))
        self.assertFalse(isValidPrefix("abc"))
        self.assertFalse(isValidPrefix("1"))
        self.assertFalse(isValidPrefix("-"))
        self.assertFalse(isValidPrefix("/"))
        self.assertFalse(isValidPrefix("//"))
        self.assertFalse(isValidPrefix("//abc"))
        self.assertFalse(isValidPrefix("/1/"))
        self.assertFalse(isValidPrefix("/ "))
        self.assertFalse(isValidPrefix(" "))

    def test_localstorage(self):
        storage = LocalStorage()
        self.assertIsInstance(storage, BaseStorage)
        data = dict(a=1, b=2)
        storage.set("test", data)
        newData = storage.get("test")
        self.assertIsInstance(newData, dict)
        self.assertEqual(newData, data)
        self.assertEqual(len(storage), len(storage.list))
        # test setitem getitem
        storage["test"] = "hello"
        self.assertEqual("hello", storage["test"])
        # Invalid, LocalStorage did not implement this method
        del storage["test"]
        self.assertIsNone(storage.get("test"))
        self.assertIsNone(storage["_non_existent_key_"])
        self.assertEqual(1, storage.get("_non_existent_key_", 1))
        self.assertEqual(0, len(storage))

    def test_redisstorage(self):
        """Run this test when it detects that the environment variable
        FLASK_PLUGINKIT_TEST_REDISURL is valid
        """
        redis_url = getenv("FLASK_PLUGINKIT_TEST_REDISURL")
        if redis_url:
            storage = RedisStorage(redis_url=redis_url)
            self.assertIsInstance(storage, BaseStorage)
            storage["test"] = 1
            self.assertEqual(storage["test"], 1)
            self.assertEqual(len(storage), len(storage.list))
            self.assertEqual(len(storage), storage._db.hlen(storage.index))
            self.assertIsNone(storage["_non_existent_key_"])
            self.assertEqual(1, storage.get("_non_existent_key_", 1))
            # RedisStorage allow remove
            del storage["test"]
            self.assertIsNone(storage["test"])
            self.assertEqual(0, len(storage))

    def test_basestorage(self):
        class MyStorage(BaseStorage):
            pass

        ms = MyStorage()
        with self.assertRaises(AttributeError):
            ms.get("test")

    def test_checkurl(self):
        self.assertTrue(check_url("http://127.0.0.1"))
        self.assertTrue(check_url("http://localhost:5000"))
        self.assertTrue(check_url("https://abc.com"))
        self.assertTrue(check_url("https://abc.com:8443"))
        self.assertFalse(check_url("ftp://192.168.1.2"))
        self.assertFalse(check_url("rsync://192.168.1.2"))
        self.assertFalse(check_url("192.168.1.2"))
        self.assertFalse(check_url("example.com"))
        self.assertFalse(check_url("localhost"))
        self.assertFalse(check_url("127.0.0.1:8000"))
        self.assertFalse(check_url("://127.0.0.1/hello-world"))

    def test_uploadsuffix(self):
        z = "https://codeload.github.com/saintic/flask-pluginkit-demo/zip/master"
        self.assertTrue(allowed_uploaded_plugin_suffix("1.tar.gz"))
        self.assertTrue(allowed_uploaded_plugin_suffix("abc.tgz"))
        self.assertTrue(allowed_uploaded_plugin_suffix("demo-1.0.0.zip"))
        self.assertFalse(allowed_uploaded_plugin_suffix(z))
        self.assertFalse(allowed_uploaded_plugin_suffix("hello.tar.bz2"))
        self.assertFalse(allowed_uploaded_plugin_suffix("test.png"))

    def test_attrclass(self):
        d = Attribution(dict(a=1, b=2, c=3))
        with self.assertRaises(AttributeError):
            d.d
        self.assertEqual(d.a, 1)
        self.assertIsInstance(d, dict)

    def test_dcp(self):
        dcp = DcpManager()
        self.assertIsInstance(dcp.list, dict)

        f = lambda: "test"

        dcp.push("f", f)
        self.assertEqual(len(dcp.list), 1)
        self.assertEqual(dcp.emit("f"), Markup("test"))
        self.assertTrue(dcp.remove("f", f))
        self.assertEqual(len(dcp.list), 1)

    def test_pip(self):
        testpkg = "semver"
        testpkgver = "3.0.1"
        tgt = join(dirname(abspath(__file__)), "tgt")
        ret = pip_install(
            "{}=={}".format(testpkg, testpkgver), target_dir=tgt, quiet=False
        )
        self.assertTrue(ret)
        pkgs = pip_list(target_dir=tgt)
        self.assertIn(testpkg, pkgs)
        pkgver = pip_show(testpkg, target_dir=tgt)
        self.assertTrue(isValidSemver(pkgver))  # type: ignore
        self.assertEqual(pkgver, testpkgver)
        # cleanup
        rmtree(tgt, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
