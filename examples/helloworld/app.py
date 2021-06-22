# -*- coding: utf-8 -*-

from flask import Flask
from flask_pluginkit import PluginManager

app = Flask(__name__)
pm = PluginManager(app)


@app.route("/")
def index():
    return "hello world"
