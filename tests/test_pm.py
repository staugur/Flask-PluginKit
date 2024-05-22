# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import unittest
from flask import Flask, request, g
from markupsafe import Markup
from flask_pluginkit import (
    PluginManager,
    LocalStorage,
    push_dcp,
    blueprint,
)
from flask_pluginkit.exceptions import PluginError, NotCallableError
from flask_pluginkit._compat import iteritems
from jinja2 import ChoiceLoader

EXAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "examples/fulldemo",
)
sys.path.append(EXAMPLE_DIR)


#: app1 with flask-pluginkit
app1 = Flask("app1")
app1.config.update(
    TESTING=True,
    PLUGINKIT_TEST=True,
    PLUGINKIT_AUTH_METHOD="FUNC",
    PLUGINKIT_AUTH_FUNC=lambda: True,
)
PluginManager(app1)
app1.register_blueprint(blueprint)

#: app2 without flask-pluginkit
app2 = Flask("app2")
app2.config["TESTING"] = True
app2.register_blueprint(blueprint)

#: app4 with flask-pluginkit full example
from app import app as app4

app4.testing = True


class PMTest(unittest.TestCase):
    def setUp(self):
        self.app1_pm = app1.extensions.get("pluginkit")
        self.app4_pm = app4.extensions.get("pluginkit")

    def test_extself(self):
        self.assertIsInstance(self.app1_pm, PluginManager)
        self.assertIsInstance(self.app4_pm, PluginManager)
        self.assertIsInstance(app1.jinja_loader, ChoiceLoader)

    def test_extself_params(self):
        self.assertFalse(os.path.isdir(self.app1_pm.plugins_abspath))
        self.assertTrue(os.path.isdir(self.app4_pm.plugins_abspath))
        self.assertIsInstance(self.app1_pm.plugin_packages, (tuple, list))
        self.assertIsInstance(self.app4_pm.pluginkit_config, dict)

    def test_extself_raise(self):
        with self.assertRaises(PluginError) as cm:
            PluginManager(Flask(__name__), plugin_packages=123)
            PluginManager(Flask(__name__), plugin_packages=["non_ppk"])

    def test_extself_tpl_global(self):
        self.assertIn("emit_tep", app1.jinja_env.globals)
        self.assertIn("emit_config", app4.jinja_env.globals)

    def test_config(self):
        self.assertTrue("emit_config" in app1.jinja_env.globals)
        with app1.test_request_context():
            self.assertTrue(self.app1_pm.emit_config("PLUGINKIT_TEST"))

    def test_hook(self):
        with app4.test_request_context("/"):
            app4.preprocess_request()
            local = LocalStorage()
            self.assertTrue("nowtime" in local.list)
            nowhour = time.strftime("%Y-%m-%d %H:", time.localtime(time.time()))
            self.assertIn(nowhour, local.get("nowtime"))
            del local["nowtime"]

    def test_example(self):
        with app4.test_client() as c:
            rv = c.get("/")
            data = rv.data.decode("utf-8")
            self.assertTrue("css/style.css" in data)
            self.assertTrue("js/hello.js" in data)
            self.assertTrue(self.app4_pm.pluginkit_config["whoami"] in data)
        self.assertEqual(len(app4.blueprints), 3)
        self.assertEqual(len(self.app4_pm.get_all_plugins), 3)
        self.assertEqual(len(self.app4_pm.get_enabled_beps), 2)
        self.assertIn(self.app4_pm.static_endpoint, app4.view_functions)
        with app4.test_request_context():
            link = self.app4_pm.emit_assets("localdemo", "css/style.css")
            self.assertTrue("stylesheet" in link)
            self.assertTrue("/css/style.css" in link)

    def test_vep(self):
        self.assertIn("localdemo.bvep_view", app4.view_functions)
        self.assertIn("view_limit", app4.view_functions)
        view_limit_data = self.app4_pm.get_enabled_veps[0]
        self.assertEqual(5, len(view_limit_data))
        with app4.test_request_context("/limit/test"):
            self.assertEqual("view_limit", request.endpoint)

    def test_cvep(self):
        self.assertIn("ClassfulView:index", app4.view_functions)
        self.assertEqual(2, len(self.app4_pm.get_enabled_cveps[0]))
        with app4.test_request_context("/classful/"):
            self.assertEqual("ClassfulView:index", request.endpoint)

    def test_filter(self):
        self.assertIn("repeat_filter", app4.jinja_env.filters)
        self.assertIn("demo_filter2", app4.jinja_env.filters)
        self.assertEqual(
            "test-filter-repeat", app4.jinja_env.filters["repeat_filter"]("x")
        )
        self.assertEqual("test-filter", app4.jinja_env.filters["demo_filter2"]("x"))

    def test_errhandler(self):
        ehs = app4.error_handler_spec[None]
        self.assertIsInstance(ehs, dict)
        self.assertIn(403, ehs)
        self.assertIn(404, ehs)
        with app4.test_client() as c:
            resp404 = c.get("/404")
            self.assertEqual(404, resp404.status_code)
            self.assertIn(b"Not Found Page", resp404.data)
            resp403 = c.get("/403")
            self.assertEqual(403, resp403.status_code)
            self.assertIn(b"permission deny", resp403.data)
            #: raise apierror
            respapierror = c.get("/api_error")
            if isinstance(respapierror.data, bytes):
                data = json.loads(respapierror.data.decode("utf-8"))
            else:
                data = json.loads(respapierror.data)
            self.assertIsInstance(data, dict)
            self.assertIn("msg", data)
            self.assertEqual("test_err_class_handler", data["msg"])
            self.assertEqual(10000, data["code"])

    def test_tcp(self):
        context = {
            k: v
            for i in app4.template_context_processors[None]
            for k, v in iteritems(i())
        }
        self.assertIsInstance(context, dict)
        self.assertIn("timestamp", context)
        self.assertIn("change_to_str", context)
        self.assertTrue(context["change_to_str"], str)
        # test p3
        self.assertIn("im", context)

    """
    def test_dcp(self):
        def callback():
            return "test"

        self.assertRaises(AttributeError, push_dcp, "raise", callback)
        with app4.app_context():
            push_dcp("test", callback)
            result = [f() for f in self.app4_pm._dcp_manager.list["test"]]
            ft = self.app4_pm._dcp_manager.emit("test")
            self.assertRaises(PluginError, push_dcp, ["raise"], callback)
            self.assertRaises(NotCallableError, push_dcp, "raise", "abc")
            self.assertIsInstance(ft, Markup)
            self.assertEqual(ft, Markup("test"))
            self.assertEqual(result, ["test"])
    """

    def test_web(self):
        with app1.test_client() as c1:
            data = c1.post("/api").data
            data = data.decode("utf-8")
            res = json.loads(data)
            self.assertIsInstance(res, dict)
            self.assertEqual(res["code"], 1)
        with app2.test_client() as c2:
            res = c2.post("/api").data
            self.assertIn(b"Authentication failed", res)

        with app1.test_request_context("/"):
            app1.preprocess_request()
            self.assertTrue(hasattr(g, "pluginkit"))
            self.assertIsInstance(g.pluginkit.get_all_plugins, list)
        with app2.test_request_context("/"):
            app2.preprocess_request()
            self.assertFalse(hasattr(g, "pluginkit"))


if __name__ == "__main__" and not os.getenv("TRAVIS"):
    unittest.main()
