# -*- coding: utf-8 -*-
"""
    Flask-PluginKit.utils
    ~~~~~~~~~~~~~~~~~~~~~

    utils: Some tool classes and functions.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import sys
import shelve
import semver
from tempfile import gettempdir

#: check python version 2 or 3
#:
#: .. versionadded:: 1.3.1
PY2 = sys.version_info[0] == 2
if PY2:
    string_types = (str, unicode)
else:
    string_types = (str,)

class BaseStorage(object):

    index = "flask_pluginkit_dat"

    def set(self):
        pass

    def get(self):
        pass


class LocalStorage(BaseStorage):

    def open(self, flag="c"):
        """Open handle"""
        #: set protocol=2 to fix python3
        #:
        #: .. versionadded:: 1.3.1
        return shelve.open(os.path.join(gettempdir(), self.index), flag=flag, protocol=2)

    def set(self, key, value):
        """Set persistent data with shelve.

        :param key: string: Index key

        :param value: All supported data types in python

        :raises:

        :returns:
        """
        db = self.open()
        try:
            db[key] = value
        finally:
            db.close()

    @property
    def list(self):
        """list all data

        :returns: dict
        """
        try:
            data = self.open(flag="r")
        except:
            pass
        else:
            return dict(data)

    def get(self, key):
        """Get persistent data from shelve.

        :returns: data
        """
        try:
            value = self.list[key]
        except:
            return
        else:
            return value


class RedisStorage(BaseStorage):

    def __init__(self, redis_url):
        self._db = self.open(redis_url)

    def open(self, redis_url):
        """open handler, you need install redis module"""
        try:
            from redis import from_url
            db = from_url(redis_url)
        except:
            return
        else:
            return db

    def set(self, key, value):
        """set key data"""
        if self._db:
            self._db.hset(self.index, key, value)

    @property
    def list(self):
        """list redis key hash data"""
        return self._db.hgetall(self.index)

    def get(self, key):
        """get key data from redis"""
        return self._db.hget(self.index, key)


def isValidSemver(version):
    """Semantic version number - determines whether the version is qualified. The format is MAJOR.Minor.PATCH, more with https://semver.org/"""
    if version and isinstance(version, string_types):
        try:
            semver.parse(version)
        except (TypeError,ValueError):
            return False
        else:
            return True
    return False


def sortedSemver(versions, sort="asc"):
    """Semantically sort the list of version Numbers"""
    if versions and isinstance(versions, (list, tuple)):
        if PY2:
            return sorted(versions, cmp=semver.compare, reverse=True if sort.upper() == "DESC" else False)
        else:
            from functools import cmp_to_key
            return sorted(versions, key=cmp_to_key(semver.compare), reverse=True if sort.upper() == "DESC" else False)
    else:
        raise TypeError("Invaild Versions, a list or tuple is right.")
