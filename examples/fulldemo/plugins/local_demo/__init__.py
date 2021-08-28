# -*- coding: utf-8 -*-
"""
    local_demo
    ~~~~~~~~~~

    This is a local plugin demo.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
import time
from flask import Blueprint, jsonify, request
from flask_pluginkit import LocalStorage

__plugin_name__ = "localdemo"
__author__ = "Mr.tao <staugur@saintic.com>"
__version__ = "0.1.0"

bp = Blueprint(__plugin_name__, __plugin_name__)


@bp.route("/")
def index():
    return jsonify(dict(hello="localdemo"))


def br():
    local = LocalStorage()
    local.set(
        "nowtime",
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
    )


def view_limit(path):
    if request.method == "GET":
        return jsonify(dict(method="GET", status=200, path=path))
    else:
        return jsonify(dict(method=request.method, status=403, path=path))


def page_not_found(error):
    return jsonify(dict(status=404, msg="Not Found Page")), 404


def update_tcp(repeat_tcp):
    repeat_tcp["im"] = __plugin_name__
    return repeat_tcp


def register():
    return {
        "tep": dict(
            code=u"<p>hello local-demo(from html code)</p>",
            html="localdemo/title.html",
        ),
        "hep": dict(before_request=br),
        "bep": dict(blueprint=bp, prefix="/localdemo"),
        "vep": dict(
            rule="/limit/<path>", view_func=view_limit, methods=["GET", "POST"]
        ),
        "filter": [("demo_filter2", lambda x: "test-filter")],
        "errhandler": {404: page_not_found},
        "tcp": dict(timestamp=int(time.time())),
        "p3": dict(repeatdemo=dict(tcp=update_tcp)),
    }
