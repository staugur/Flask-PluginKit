# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import unittest
from flask import Flask, g, Markup
from flask_pluginkit import Flask as ExFlask, PluginManager, LocalStorage
from flask_pluginkit.exceptions import PEPError, PluginError
from flask_pluginkit._compat import PY2
from jinja2 import ChoiceLoader
EXAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples/fulldemo')
sys.path.append(EXAMPLE_DIR)


#: app1 with flask-pluginkit
app1 = Flask("app1")
app1.config['TESTING'] = True
app1.config['PLUGINKIT_TEST'] = True
PluginManager(app1)

#: app2 without flask-pluginkit
app2 = Flask("app2")
app2.config['TESTING'] = True

#: app3 with flask-pluginkit and exflask
def create_app3():
    app3 = ExFlask("app3")
    app3.config['TESTING'] = True
    pm = PluginManager(pluginkit_config=dict(whoami='app3'))
    pm.init_app(app3)
    return app3

app3 = create_app3()

#: app4 with flask-pluginkit full example
from app import app as app4
app4.testing = True


class PMTest(unittest.TestCase):

    def setUp(self):
        self.app1_pm = app1.extensions.get("pluginkit")
        self.app3_pm = app3.extensions.get("pluginkit")
        self.app4_pm = app4.extensions.get("pluginkit")
        self.app4_client = app4.test_client()

    def test_extself(self):
        self.assertIsInstance(self.app1_pm, PluginManager)
        self.assertIsInstance(self.app3_pm, PluginManager)
        self.assertIsInstance(self.app4_pm, PluginManager)
        self.assertIsInstance(app1.jinja_loader, ChoiceLoader)

    def test_extself_params(self):
        self.assertFalse(os.path.isdir(self.app1_pm.plugins_abspath))
        self.assertFalse(os.path.isdir(self.app3_pm.plugins_abspath))
        self.assertTrue(os.path.isdir(self.app4_pm.plugins_abspath))
        self.assertIsInstance(self.app1_pm.plugin_packages, (tuple, list))
        self.assertTrue(self.app3_pm.static_url_path.startswith('/'))
        self.assertIsInstance(self.app4_pm.pluginkit_config, dict)

    def test_extself_raise(self):
        with self.assertRaises(PluginError) as cm:
            PluginManager(Flask(__name__), plugin_packages=123)
            PluginManager(Flask(__name__), plugin_packages=['non_ppk'])

    def test_extself_tpl_global(self):
        self.assertIn("emit_tep", app1.jinja_env.globals)
        self.assertIn("emit_assets", app3.jinja_env.globals)
        self.assertIn("emit_config", app4.jinja_env.globals)

    def test_exflask(self):
        @app3.before_request
        def my_test():
            pass
        self.assertTrue(hasattr(app3, 'before_request_top'))
        self.assertTrue(hasattr(app3, 'before_request_second'))

    def test_config(self):
        self.assertEqual(self.app3_pm.pluginkit_config['whoami'],'app3')
        self.assertTrue("emit_config" in app1.jinja_env.globals)
        with app1.test_request_context():
            self.assertTrue(self.app1_pm.emit_config("PLUGINKIT_TEST"))

    def test_hook(self):
        with app4.test_request_context('/'):
            app4.preprocess_request()
            local = LocalStorage()
            self.assertTrue("nowtime" in local.list)
            nowhour = time.strftime('%Y-%m-%d %H:', time.localtime(time.time()))
            self.assertIn(nowhour, local.get("nowtime"))

    def test_example(self):
        if not PY2:
            with app4.test_client() as c:
                rv = c.get('/')
                data = rv.data.decode('utf-8')
                self.assertTrue("css/style.css" in data)
                self.assertTrue("js/hello.js" in data)
                self.assertTrue(self.app4_pm.pluginkit_config['whoami'] in data)
        self.assertEqual(len(app4.blueprints), 2)
        self.assertEqual(len(self.app4_pm.get_all_plugins), 2)
        self.assertEqual(len(self.app4_pm.get_enabled_beps), 2)
        self.assertIn(self.app4_pm.static_endpoint, app4.view_functions)
        with app4.test_request_context():
            link = self.app4_pm.emit_assets('localdemo','css/style.css')
            self.assertTrue("stylesheet" in link)
            self.assertTrue("/css/style.css" in link)

if __name__ == '__main__':
    unittest.main()
