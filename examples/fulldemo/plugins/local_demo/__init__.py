# -*- coding: utf-8 -*-
"""
    local_demo
    ~~~~~~~~~~~~~~~~~~~~~

    This is a local plugin demo.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
import time
from flask import Blueprint, jsonify
from flask_pluginkit import LocalStorage

__plugin_name__ = "localdemo"
__author__ = "Mr.tao <staugur@saintic.com>"
__version__ = "0.1.0"

bp = Blueprint(__plugin_name__, __plugin_name__)


@bp.route('/')
def index():
    return jsonify(dict(hello="localdemo"))


def br():
    local = LocalStorage()
    local.set("nowtime",
              time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
              )


def register():
    return {
        "tep": dict(code=u'<p>hello local-demo(from html code)</p>', html='localdemo/title.html'),
        'hep': dict(before_request=br),
        'bep': dict(blueprint=bp, prefix='/localdemo')
    }
