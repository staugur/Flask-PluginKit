# -*- coding: utf-8 -*-
"""
    local_demo
    ~~~~~~~~~~~~~~~~~~~~~

    This is a local plugin demo.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
from flask import Blueprint, current_app, request, jsonify

__plugin_name__ = "localdemo"
__author__ = "Mr.tao <staugur@saintic.com>"
__version__ = "0.1.0"

bp = Blueprint(__plugin_name__, __plugin_name__)


@bp.route('/')
def index():
    return jsonify(dict(hello="localdemo"))


def br():
    #current_app.logger.debug(request.endpoint)
    #current_app.logger.debug(current_app.url_map)
    pass


def register():
    return {
        "tep": dict(code=u'<p>hello local-demo(from html code)</p>', html='localdemo/title.html'),
        'hep': dict(before_request=br),
        'bep': dict(blueprint=bp, prefix='/localdemo')
    }
