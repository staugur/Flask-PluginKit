# -*- coding: utf-8 -*-
"""
    Flask-Plugin-Development-Kit.libs.base
    ~~~~~~~~~~~~~~

    base class

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import logging


class ServiceBase(object):
    """ 所有服务的基类 """

    def __init__(self):
        #设置全局超时时间(如连接超时)
        self.timeout= 2
        #Redis连接池
        self.redis = None
        #MySQL连接池
        self.mysql = None
        #Mongodb连接
        self.mongo = None
        #Memcache连接
        self.memcache = None


class PluginBase(ServiceBase):
    """ 插件基类: 提供插件所需要的公共接口与扩展点 """
    
    def __init__(self):
        super(PluginBase, self).__init__()
        self.logger = logging
