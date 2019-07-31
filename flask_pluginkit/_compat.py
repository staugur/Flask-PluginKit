# -*- coding: utf-8 -*-
"""
    flask_pluginkit._compat
    ~~~~~~~~~~~~~~~~~~~~~~~

    A module providing tools for cross-version compatibility.

    :copyright: (c) 2019 by staugur.
    :license: BSD 3-Clause, see LICENSE for more details.
"""

from sys import version_info

PY2 = version_info[0] == 2

if PY2:  # pragma: nocover

    import urllib2
    from urlparse import urlsplit, parse_qs

    def iteritems(d):
        return d.iteritems()

    def itervalues(d):
        return d.itervalues()

    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)

else:  # pragma: nocover

    import urllib.request as urllib2
    from urllib.parse import urlsplit, parse_qs

    def iteritems(d):
        return iter(d.items())

    def itervalues(d):
        return iter(d.values())

    text_type = str
    string_types = (str,)
    integer_types = (int, )

__all__ = [
    'PY2',
    'urllib2',
    'urlsplit',
    'parse_qs',
    'iteritems',
    'itervalues',
    'string_types',
    'integer_types'
]
