# -*- coding: utf-8 -*-
"""
flask_pluginkit.utils
~~~~~~~~~~~~~~~~~~~~~

Some tool classes and functions.

:copyright: (c) 2019 by staugur.
:license: BSD 3-Clause, see LICENSE for more details.
"""

import json
import shelve
from semver.version import Version
from functools import cmp_to_key
from os.path import join, abspath
from tempfile import gettempdir
from collections import deque
from markupsafe import Markup
from time import time
from flask import Response, jsonify
from ._compat import string_types, text_type, iteritems
from .exceptions import PluginError, NotCallableError, ParamError
from typing import List, Any, Optional, Dict


def isValidPrefix(prefix: str, allow_none: bool = False) -> bool:
    """Check if it can be used for blueprint prefix"""
    if prefix is None and allow_none is True:
        return True
    if isinstance(prefix, string_types):
        return (
            prefix.startswith("/")
            and not prefix.endswith("/")
            and "//" not in prefix
            and " " not in prefix
        )
    return False


def isValidSemver(version: str) -> bool:
    """Semantic version number - determines whether the version is qualified.
    The format is MAJOR.Minor.PATCH, more with https://semver.org
    """
    if version and isinstance(version, string_types):
        return Version.is_valid(version)
    return False


def sortedSemver(versions: List[str], sort: str = "ASC") -> List[str]:
    """Semantically sort the list of version Numbers"""
    reverse = True if sort.upper() == "DESC" else False
    if versions and isinstance(versions, (list, tuple)):
        return sorted(
            versions,
            key=cmp_to_key(lambda v1, v2: Version.parse(v1).compare(v2)),
            reverse=reverse,
        )
    else:
        raise TypeError("Invaild versions, a list or tuple is right.")


class BaseStorage(object):
    """This is the base class for storage.
    The available storage classes need to inherit from :class:`~BaseStorage`
    and override the `get` and `set` methods, it's best to implement
    the remote method as well.

    This base class customizes the `__getitem__`, `__setitem__`
    and `__delitem__` methods so that the user can call it like a dict.

    .. versionchanged:: 3.4.1
        Change :attr:`index` to :attr:`DEFAULT_INDEX`
    """

    #: The default index, as the only key, you can override it.
    DEFAULT_INDEX: str = "flask_pluginkit_dat"

    @property
    def index(self):
        """Get the final index

        .. versionadded:: 3.4.1
        """
        return getattr(self, "COVERED_INDEX", None) or self.DEFAULT_INDEX

    @index.setter
    def index(self, _covered_index: str):
        """Set the covered index

        .. versionadded:: 3.6.0
        """
        self.COVERED_INDEX = _covered_index

    def __getitem__(self, key: str):
        if hasattr(self, "get"):
            return self.get(key)
        else:
            raise AttributeError("Please override the get method")

    def __setitem__(self, key: str, value: Any):
        if hasattr(self, "set"):
            return self.set(key, value)
        else:
            raise AttributeError("Please override the set method")

    def __delitem__(self, key: str):
        if hasattr(self, "remove"):
            return self.remove(key)
        else:
            return False

    def __str__(self):
        return "<%s object at %s, index is %s>" % (
            self.__class__.__name__,
            hex(id(self)),
            self.index,
        )

    __repr__ = __str__


class LocalStorage(BaseStorage):
    """Local file system storage based on the shelve module."""

    def __init__(self, path: Optional[str] = None):
        self.COVERED_INDEX = path or join(gettempdir(), self.DEFAULT_INDEX)

    def _open(self, flag: str = "c") -> shelve.Shelf:
        return shelve.open(
            filename=abspath(self.index),
            flag=flag,
            protocol=2,
            writeback=False,
        )

    @property
    def list(self) -> Dict[str, Any]:
        """list all data

        :returns: dict
        """
        db = None
        try:
            db = self._open(flag="r")
        except Exception:
            return dict()
        else:
            return dict(db)
        finally:
            if db:
                db.close()

    def __ck(self, key: str) -> str:
        if not isinstance(key, text_type):
            key = key.decode("utf-8")
        return key

    def set(self, key: str, value: Any):
        """Set persistent data with shelve.

        :param key: str: Index key

        :param value: All supported data types in python

        :raises:

        :returns:
        """
        db = None
        try:
            db = self._open()
            db[self.__ck(key)] = value
        finally:
            if db:
                db.close()

    def setmany(self, **mapping: Dict[str, Any]):
        """Set more data

        :param mapping: the more k=v

        .. versionadded:: 3.4.1
        """
        if mapping and isinstance(mapping, dict):
            db = self._open()
            for k, v in iteritems(mapping):
                db[self.__ck(k)] = v
            db.close()

    def get(self, key: str, default: Any = None):
        """Get persistent data from shelve.

        :returns: data
        """
        try:
            value = self.list[key]
        except KeyError:
            return default
        else:
            return value

    def remove(self, key: str):
        db = self._open()
        del db[key]

    def __len__(self):
        return len(self.list)


class ExpiredLocalStorage(BaseStorage):
    """Local file system storage based on the shelve module, support exire time."""

    def __init__(self, path: Optional[str] = None):
        self.COVERED_INDEX = path or join(gettempdir(), self.DEFAULT_INDEX)

    def set(self, key: str, value: Any, ttl: int = 0):
        """Set persistent data with expired time.
        :param key: str: Index key
        :param value: All supported data types in python
        :param ttl: int: expired time in seconds, default is 0(no expired)
        :raises:
        """
        if not key or not value or ttl < 0:
            raise ParamError("Invalid key or value or ttl")
        with shelve.open(self.COVERED_INDEX) as db:
            etime = int(time()) + ttl if ttl > 0 else 0
            db[key] = {"value": value, "etime": etime}

    def get(self, key: str) -> Any:
        """获取键值，若已过期则自动删除并返回 None"""
        with shelve.open(self.COVERED_INDEX) as db:
            entry = db.get(key)
            if not entry:
                return None

            etime = entry["etime"]
            if etime == 0:
                return entry["value"]
            elif time() > etime:
                del db[key]  # 删除过期条目
                return None
            return entry["value"]

    def remove(self, key):
        """主动删除键"""
        with shelve.open(self.COVERED_INDEX) as db:
            if key in db:
                del db[key]

    @property
    def list(self) -> Dict[str, Any]:
        """list all data"""
        with shelve.open(self.COVERED_INDEX) as db:
            now = int(time())
            # 过滤掉过期的键值对
            valid_data = {
                k: v for k, v in db.items() if v["etime"] > now or v["etime"] == 0
            }
            return {k: v["value"] for k, v in valid_data.items()}


class RedisStorage(BaseStorage):
    """Use redis stand-alone storage"""

    def __init__(self, redis_url=None, redis_connection=None):
        self._db = self._open(redis_url) if redis_url else redis_connection

    def _open(self, redis_url):
        try:
            from redis import from_url
        except ImportError:
            raise ImportError("Please install the redis module, eg: pip install redis")
        else:
            return from_url(redis_url)

    @property
    def list(self) -> Dict[str, Any]:
        """list redis hash data"""
        return {k: json.loads(v) for k, v in iteritems(self._db.hgetall(self.index))}

    def set(self, key: str, value: Any):
        """set key data"""
        return self._db.hset(self.index, key, json.dumps(value))

    def setmany(self, **mapping: Dict[str, Any]):
        """Set more data

        :param mapping: the more k=v

        .. versionadded:: 3.4.1
        """
        if mapping and isinstance(mapping, dict):
            mapping = {k: json.dumps(v) for k, v in iteritems(mapping)}
            return self._db.hmset(self.index, mapping)

    def get(self, key: str, default: Any = None) -> Any:
        """get key original data from redis"""
        v = self._db.hget(self.index, key)
        if v:
            if not isinstance(v, text_type):
                v = v.decode("utf-8")
            return json.loads(v)
        return default

    def remove(self, key: str):
        """delete key from redis"""
        return self._db.hdel(self.index, key)

    def __len__(self):
        return self._db.hlen(self.index)


class JsonResponse(Response):
    """In response to a return type that cannot be processed.
    If it is a dict, return json.

    .. versionadded:: 3.4.0
    """

    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv, dict):
            rv = jsonify(rv)
        return super(JsonResponse, cls).force_type(rv, environ)


class Attribution(dict):
    """A dict that allows for object-like property access syntax."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class DcpManager(object):
    def __init__(self):
        self._listeners = {}

    @property
    def list(self):
        return self._listeners

    def push(self, event, callback, position="right"):
        """Connect a dcp, push a function.

        :param event: a unique identifier name for dcp.

        :param callback: corresponding to the event to perform a function.

        :param position: the position of the insertion function,
                         right(default) or left. The default right is inserted
                         at the end of the event, and left is inserted into
                         the event first.

        :raises PluginError: the param event or position error

        :raises NotCallableError: the param callback is not callable

        .. versionadded:: 3.2.0
        """
        if event and isinstance(event, string_types):
            if not callable(callback):
                raise NotCallableError("The event %s cannot be called" % event)
            if position not in ("left", "right", "after", "before"):
                raise PluginError("Invalid position")
            if event not in self._listeners:
                self._listeners[event] = deque([callback])
            elif position in ("left", "before"):
                self._listeners[event].appendleft(callback)
            else:
                self._listeners[event].append(callback)
        else:
            raise PluginError("Invalid event")

    def remove(self, event, callback):
        """Remove a callback again."""
        try:
            self._listeners[event].remove(callback)
        except (KeyError, ValueError):
            return False
        else:
            return True

    def emit(self, event, *args, **kwargs):
        """Emits events for the template context.

        :returns: strings with :class:`~flask.Markup`
        """
        results = []
        funcs = self._listeners.get(event) or []
        for f in funcs:
            rv = f(*args, **kwargs)
            if isinstance(rv, (list, tuple)):
                rv = "".join(rv)
            if rv:
                if not isinstance(rv, text_type):
                    rv = rv.decode("utf-8")
                results.append(rv)
        return Markup("".join(results))


def allowed_uploaded_plugin_suffix(filename: str) -> bool:
    """Check suffix for uploaded filename

    .. versionadded:: 3.3.0
    """
    allow_suffix = [".tar.gz", ".tgz", ".zip"]
    if isinstance(filename, string_types):
        for suffix in allow_suffix:
            if filename.endswith(suffix):
                return True
    return False


def check_url(addr: str) -> bool:
    """Check whether UrlAddr is in a valid format, for example::

        http://ip:port
        https://abc.com

    .. versionadded:: 3.3.0
    """
    from re import compile, IGNORECASE

    regex = compile(
        r"^(?:http)s?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
        r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        IGNORECASE,
    )
    if addr and isinstance(addr, string_types):
        if regex.match(addr):
            return True
    return False
