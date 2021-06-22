# -*- coding: utf-8 -*-
"""
    repeat_demo
    ~~~~~~~~~~~

    This is a repetitive demonstration of local_demo.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from flask import abort, jsonify, request
from flask_classful import FlaskView

__plugin_name__ = "repeatdemo"
__author__ = "Mr.tao <staugur@saintic.com>"
__version__ = "0.3.0"


def view_abort_403():
    return abort(403)


def permission_deny(error):
    return jsonify(dict(status=403, msg="permission deny")), 403


class ApiError(Exception):
    def __init__(self, code, message, status_code=200):
        super(ApiError, self).__init__()
        self.code = code
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        rv = dict(code=self.code, msg=self.message)
        return rv


def handle_api_error(e):
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response


def raise_api_error_view():
    raise ApiError(10000, "test_err_class_handler")


class ClassfulView(FlaskView):
    def index(self):
        return "test"


def bvep_view():
    return request.endpoint


def register():
    return {
        "cvep": dict(view_class=ClassfulView),
        "vep": [
            dict(rule="/403", view_func=view_abort_403),
            dict(rule="/api_error", view_func=raise_api_error_view),
            dict(rule="/bvep", view_func=bvep_view, _blueprint="localdemo"),
        ],
        "filter": dict(repeat_filter=lambda x: "test-filter-repeat"),
        "errhandler": [
            dict(error=403, handler=permission_deny),
            dict(error=ApiError, handler=handle_api_error),
        ],
        "tcp": dict(change_to_str=str),
    }
