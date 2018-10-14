# -*- coding: utf-8 -*-
"""
    Flask-PluginKit
    ~~~~~~~~~~~~~~~

    utils: Some tool classes and functions.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import shelve
from tempfile import gettempdir


class BaseStorage(object):

    index = "flask_pluginkit.db"

    def set(self):
        pass

    def get(self):
        pass


class LocalStorage(BaseStorage):

    def open(self, flag="c"):
        """Open handle"""
        return shelve.open(os.path.join(gettempdir(), self.index), flag=flag)

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

        :returns dict
        """
        try:
            data = self.open(flag="r")
        except:
            pass
        else:
            return data

    def get(self, key):
        """Get persistent data from shelve.

        :returns data
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
