# -*- coding: utf-8 -*-
"""
    flask-pluginkit-demo
    ~~~~~~~~~~~~~~~~~~~~~

    This is a demo for plugin.
    Your Plugin Description.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from os.path import dirname, abspath
from flask import Blueprint, make_response, jsonify, request


plugin_blueprint = Blueprint("demo", "demo", static_folder='static', root_path=dirname(abspath(__file__)))
@plugin_blueprint.route("/")
def index():
    return "third plugin demo"


def api_limit():
    """Api request current limit"""
    ip = request.headers.get('X-Real-Ip', request.remote_addr)
    response = make_response(jsonify(msg="RateLimiter", ip=ip), 429)
    #: Remove the comment from the next line and intercept the request
    #response.is_return = True
    return None
