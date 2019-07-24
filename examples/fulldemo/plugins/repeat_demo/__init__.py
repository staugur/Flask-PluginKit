# -*- coding: utf-8 -*-
"""
    repeat_demo
    ~~~~~~~~~~~

    This is a repetitive demonstration of local_demo.

    :copyright: (c) 2019 by staugur.
    :license: BSD, see LICENSE for more details.
"""

from flask import abort, jsonify

__plugin_name__ = "repeatdemo"
__author__ = "Mr.tao <staugur@saintic.com>"
__version__ = "0.1.0"


def view_abort_403():
    return abort(403)


def permission_deny(error):
    return jsonify(dict(status=403, msg="permission deny")),403


def register():
    return {
        'vep': dict(rule='/403', view_func=view_abort_403),
        'filter': dict(repeat_filter=lambda: 'test-filter-repeat'),
        'errhandler': {403: permission_deny},
        'tcp': dict(change_to_str=str),
    }
