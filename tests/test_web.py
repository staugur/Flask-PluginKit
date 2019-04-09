# -*- coding: utf-8 -*-

import os
import json
import unittest
from flask import Flask, g
from flask_pluginkit import Flask as FixFlask, PluginManager, blueprint, LocalStorage, PY2, push_dcp, DCPError, NotCallableError
from jinja2 import Markup

# app1 with flask-pluginkit
app1 = Flask("app1")
app1.config['TESTING'] = True
app1.config['PLUGINKIT_TEST'] = True
plugin = PluginManager(app1, s3="local")
app1.register_blueprint(blueprint)

# app2 without flask-pluginkit
app2 = Flask("app2")
app2.config['TESTING'] = True
app2.register_blueprint(blueprint)

# app3 with fixflask
app3 = FixFlask("app3")
app3.config['TESTING'] = True

def callback():
    return "test"

class PMTest(unittest.TestCase):

    def setUp(self):
        self.c1 = app1.test_client()
        self.c2 = app2.test_client()

    def api2dict(self, res):
        if PY2:
            return json.loads(res)
        else:
            return json.loads(res.decode('utf-8'))

    def test_extself(self):
        self.assertIsInstance(app1.extensions.get("pluginkit"), PluginManager)

    def test_api(self):
        res = self.api2dict(self.c1.post('/api').data)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["code"], 1)
        res = self.api2dict(self.c2.post('/api').data)
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

    def test_storage(self):
        with app1.test_request_context('/'):
            app1.preprocess_request()
            apps = app1.extensions['pluginkit'].storage()
            ls = LocalStorage()
            ls.set("test", True)
            self.assertEqual(apps.list, ls.list)
            self.assertTrue(apps.get("test"))

    def test_fixflask(self):
        @app3.before_request
        def test():
            pass
        self.assertTrue(app3.before_request_funcs[None][0] == test)
        self.assertIsInstance(app3.static_folder, list)
        self.assertTrue(hasattr(app3,'before_request_top'))

    def test_dcp(self):
        self.assertRaises(AttributeError, push_dcp, 'raise', callback)
        with app1.test_request_context():
            app1.preprocess_request()
            push_dcp("test", callback)
            result = [f() for f in app1.extensions["pluginkit"]._dcp_funcs["test"]]
            ft = app1.extensions["pluginkit"].emit_dcp("test")
            self.assertRaises(DCPError, push_dcp, ['raise'], callback)
            self.assertRaises(NotCallableError, push_dcp, 'raise', "abc")
            self.assertIsInstance(ft, Markup)
            self.assertEqual(ft, Markup("test"))
            self.assertEqual(result, ["test"])

    def test_dfp(self):
        plugin.push_func("test", callback)
        self.assertEqual("test", plugin.emit_func("test"))
        self.assertRaises(NotCallableError, plugin.push_func,'test','xxx')

    def test_config(self):
        conf = plugin.get_config
        self.assertIsInstance(conf, dict)
        self.assertIn("PLUGINKIT_TEST", conf)
        self.assertTrue(conf["PLUGINKIT_TEST"], True)
        

if __name__ == '__main__':
    unittest.main()
