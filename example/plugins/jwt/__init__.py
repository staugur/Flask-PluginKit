# -*- coding: utf-8 -*-
"""
    plugins.jwt
    ~~~~~~~~~~~~~~

    基于Json Web Token(JWT)的用户身份验证和授权插件。

    :copyright: (c) 2017 by taochengwei.
    :license: BSD, see LICENSE for more details.
"""

#: Importing these two modules is the first and must be done.
#: 首先导入这两个必须模块
from __future__ import absolute_import
from libs.base import PluginBase
#: Import the other modules here, and if it's your own module, use the relative Import. eg: from .lib import Lib
#: 在这里导入其他模块, 如果有自定义包目录, 使用相对导入, 如: from .lib import Lib
from .utils import JWTUtil, JWTException
from flask import Blueprint, request, render_template
from flask_restful import Api, Resource


#：Your plug-in name must be consistent with the plug-in directory name.
#：你的插件名称，必须和插件目录名称等保持一致.
__plugin_name__ = "jwt"
#: Plugin describes information. What does it do?
#: 插件描述信息,什么用处.
__description__ = "Json Web Token Plugin for User Authentication."
#: Plugin Author
#: 插件作者
__author__      = "taochengwei <staugur@saintic.com>"
#: Plugin Version
#: 插件版本
__version__     = "0.1.0"
#: Plugin Url
#: 插件主页
__url__         = "https://github.com/staugur/jwt/"
#: Plugin License
#: 插件许可证
__license__     = "BSD"
#: Plugin License File
#: 插件许可证文件
__license_file__= "LICENSE"
#: Plugin Readme File
#: 插件自述文件
__readme_file__ = "README.md"
#: Plugin state, enabled or disabled, default: enabled
#: 插件状态, enabled、disabled, 默认enabled
__state__       = "enabled"

#: 使用者，加密串
_Audience   = b"SaintIC Inc."
_SecretKey  = b"D1D5EB327D55D83EB96EAD9CDD1394E8"
_JwtInstance= JWTUtil(_SecretKey, _Audience)

#: JWT Blueprint
JWTApi_blueprint = Blueprint("jwt", "jwt")
#: 可视化简单登录页
@JWTApi_blueprint.route("/login/")
def getToken():
    return render_template("login.html")
    return """
        <form action="{0}" method="post">
            <p><input type="text" id="username" name="username" autofocus="autofocus" required="required" autocomplete="off" placeholder="请输入用户名" value="" /></p>
            <p><input type="password" id="password" name="password" required="required" placeholder="请输入密码" value="" /></p>
            <p><input type="checkbox" name="remember" value="true">Remember Me 7d</p>
            <input type="submit" value="登录">
        </form>""".format(url_for("jwt.login"))

class JWTApiCreate(Resource):
    """JWT Api Route: create token"""

    def __init__(self):
        super(JWTApiCreate, self).__init__()
        self.jwt = _JwtInstance

    def _getAuthentication(self, username, password):
        """ 登录认证 """
        return True

    def _getUserData(self, username):
        """ 返回公开的简单的用户数据 """
        return {"username": username, "uid": 0}

    def post(self):
        """token生成流程:
        >1. 首先使用用户名和密码去签定身份返回True/False
        >2. 如果True接着获取用户可公开数据
        >3. 之后生成JWT
        具体业务流程自由定义，比如可以保存token到redis中，设置ttl过期时间。
        """
        #1.
        username = request.form.get("username")
        password = request.form.get("password")
        exipres  = 7200
        #expire time(seconds)
        if username and password:
            _authRes = self._getAuthentication(username, password)
        else:
            return {"msg": "invalid username or password"}
        #2.
        if _authRes:
            _payload = self._getUserData(username)
            #3.
            try:
                token = self.jwt.createJWT(_payload, expiredSeconds=exipres)
            except JWTException:
            	return {"msg": "Failed to request token"}
            else:
                return {"token": token}
        else:
            return {"msg": "Authentication failed"}

class JWTApiVerify(Resource):
    """JWT Api Route: verify token"""

    def __init__(self):
        super(JWTApiVerify, self).__init__()
        self.jwt = _JwtInstance

    def post(self):
        """token验证流程
        >1. 首先从cookies中获取token，其次获取头部Authentication
        >2. 调用验证方法，发生异常即认证失败，最后返回token解析好的字典数据
        """
        res = {"success": False}
        #1.
        token = request.cookies.get("token") or request.headers.get("authentication")
        if not token:
            return res
        #2.
        try:
            self.jwt.verifyJWT(token)
        except JWTException as e:
            self.logger.exception(e, exc_info=True)
        else:
            res.update(success=True)
        return res

api = Api(JWTApi_blueprint)
api.add_resource(JWTApiCreate, '/login/', endpoint='login')
api.add_resource(JWTApiVerify, '/verify/', endpoint='verify')


#: 返回插件主类
def getPluginClass():
    return JWTPlugin

#: 插件主类, 不强制要求名称与插件名一致, 保证getPluginClass准确返回此类
class JWTPlugin(object):

    def run(self):
        """ 插件一般运行入口 """
        self.pb = PluginBase()

    def register_bep(self):
        """注册蓝图入口, 返回蓝图路由前缀及蓝图名称"""
        bep = {"prefix": "/jwt", "blueprint": JWTApi_blueprint}
        return bep

    def bindToken(self, **kwargs):
    	token   = request.cookies.get("token") or request.headers.get("authentication")
    	g.token = _JwtInstance.analysisJWT(token)["payload"]


    def register_cep(self):
    	return {"before_request_hook": self.bindToken}
