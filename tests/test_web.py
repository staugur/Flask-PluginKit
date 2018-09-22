# -*- coding: utf-8 -*-

import os
import json
import unittest
from flask import Flask, g
from flask_pluginkit import PluginManager, blueprint

pd = "/tmp/plugins"
if not os.path.isdir(pd):
    os.mkdir("/tmp/plugins")

# app1 with flask-pluginkit
app1 = Flask("app1")
PluginManager(app1, plugins_base="/tmp")
app1.register_blueprint(blueprint)

# app2 without flask-pluginkit
app2 = Flask("app2")
app2.register_blueprint(blueprint)


class PMTest(unittest.TestCase):

    def setUp(self):
        self.app1 = app1.test_client()
        self.app2 = app2.test_client()

    def test_api(self):
        res = json.loads(self.app1.post('/api').data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["code"], 1)
        res = json.loads(self.app2.post('/api').data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["code"], 10000)

    def test_g(self):
        with app1.test_request_context('/'):
            app1.preprocess_request()
            self.assertTrue(hasattr(g, "plugin_manager"))
            self.assertIsInstance(g.plugins, list)
        with app2.test_request_context('/'):
            app2.preprocess_request()
            self.assertFalse(hasattr(g, "plugin_manager"))


if __name__ == '__main__':
    unittest.main()
