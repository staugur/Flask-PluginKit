# -*- coding: utf-8 -*-
"""
    plugins.jwt.test
    ~~~~~~~~~~~~~~

    测试用例

    :copyright: (c) 2017 by taochengwei.
    :license: MIT, see LICENSE for more details.
"""

import unittest, os, json, base64, logging
from utils import *

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
)

class JWTtest(unittest.TestCase):

    ##初始化工作
    def setUp(self):
        self.key = "test" #加密密钥
        self.exp = 3600 #过期时间一小时
        self.jwt = JWTUtil(self.key)

    #退出清理工作
    def tearDown(self):
        pass

    #测试时间戳的几个函数 
    def test_timestamp(self):
        t1 = self.jwt.get_current_timestamp()
        self.assertEqual(len(str(t1)), 10)
        self.assertEqual(type(t1), int)
        print "\n当前时间是%s" %self.jwt.timestamp_datetime(t1)
        t2 = self.jwt.timestamp_after_timestamp(minutes=10)
        print "当前时间10分钟后的时间戳是%s" %t2
        self.assertEqual(len(str(t2)), 10)
        self.assertEqual(type(t2), int)
        self.assertLess(t1, t2)
        self.assertTrue(type(t1), type(t2))
        print "当前时间10分钟后的时间戳本地时间是%s" %self.jwt.timestamp_datetime(t2)

    def test_createjwt(self):
        payload = {"uid": 0, "username": "admin"}
        token   = self.jwt.createJWT(payload)
        #print "\n",token
        self.assertEqual(token.count("."), 2)
        _header, _payload, _signature = token.split(".")
        _header  = json.loads(base64.urlsafe_b64decode(_header))
        self.assertDictEqual({'alg': 'HS256', 'typ': 'JWT'}, _header)
        _payload = json.loads(base64.urlsafe_b64decode(_payload))
        self.assertIn("JWT", _header.values())
        self.assertIn("HS256", _header.values())
        self.assertIn("iss", _payload.keys())
        self.assertIn("sub", _payload.keys())
        self.assertIn("aud", _payload.keys())
        self.assertEqual("SaintIC Inc.", _payload["aud"])
        self.assertEqual(payload["uid"], _payload["uid"])
        self.assertEqual(payload["username"], _payload["username"])

    def test_raise(self):
        self.assertRaises(TypeError, self.jwt.createJWT, [])
        self.assertRaises(KeyError, self.jwt.createJWT, {"iss": "test"})

    def test_verifyjwt(self):
        #print "\n"
        token = self.jwt.createJWT()
        self.jwt.verifyJWT(token)

if __name__ =='__main__':
    unittest.main()