# -*- coding: utf-8 -*-
"""
    flask_pluginkit._compat
    ~~~~~~~~~~~~~~~~~~~~~~~

    A module providing tools for cross-version compatibility.

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

import urllib.request as urllib2
from urllib.parse import urlsplit, parse_qs


def iteritems(d: dict):
    return iter(d.items())


def itervalues(d: dict):
    return iter(d.values())


text_type = str
string_types = (str,)
integer_types = (int,)
