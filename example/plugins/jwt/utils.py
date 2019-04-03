# -*- coding: utf-8 -*-
"""
    plugins.jwt.utils
    ~~~~~~~~~~~~~~

    JWT的实用工具。

    :copyright: (c) 2017 by taochengwei.
    :license: MIT, see LICENSE for more details.
"""

import hashlib, hmac, time, datetime, random, base64, json, logging

class JWTException(Exception): pass
class SignatureBadError(JWTException): pass
class TokenExpiredError(JWTException): pass
class InvalidTokenError(JWTException): pass

class JWTUtil(object):
    """ Json Web Token Utils """

    def __init__(self, secretkey, audience="SaintIC Inc."):
        """ 定义公共变量
        @param secretkey str: 签名加密串,建议足够复杂,切勿丢失;
        @param audience str: 标准载荷声明中的aud,即接收方;
        标准载荷声明:
            iss: 签发者
            sub: 主题
            aud: 接收方
            exp: 过期时间，UNIX时间戳，这个过期时间必须要大于签发时间
            nbf: 指定一个UNIX时间戳之前，此token是不可用的
            iat: 签发时间，UNIX时间戳
            jti: 唯一身份标识
        """
        self.secretkey= secretkey
        self._header  = {
            "typ": "JWT",
            "alg": "HS256"
        }
        self._payload = {
            "iss": "JWTPlugin staugur@saintic.com",
            "sub": "Json Web Token",
            "aud": audience,
            "jti": self.md5(self.secretkey),
        }
        self._payloadkey = ("iss", "sub", "aud", "exp", "nbf", "iat", "jti")
        #logging.info("header: {0}, payload: {1}".format(self._header, self._payload))

    def md5(self, pwd):
        return hashlib.md5(pwd).hexdigest()

    def get_current_timestamp(self):
        """ 获取本地当前时间戳: Unix timestamp：是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒 """
        return int(time.mktime(datetime.datetime.now().timetuple()))

    def timestamp_after_timestamp(self, timestamp=None, seconds=0, minutes=0, hours=0, days=0):
        """ 给定时间戳,计算该时间戳之后多少秒、分钟、小时、天的时间戳(本地时间) """
        #1. 默认时间戳为当前时间
        timestamp = self.get_current_timestamp() if timestamp is None else timestamp
        #2. 先转换为datetime
        d1 = datetime.datetime.fromtimestamp(timestamp)
        #3. 根据相关时间得到datetime对象并相加给定时间戳的时间
        d2 = d1 + datetime.timedelta(seconds=int(seconds), minutes=int(minutes), hours=int(hours), days=int(days))
        #4. 返回某时间后的时间戳
        return int(time.mktime(d2.timetuple()))

    def timestamp_datetime(self, timestamp):
        """ 将uninx时间戳转换为可读性的时间 """
        format = '%Y-%m-%d %H:%M:%S'
        # timestamp为传入的值为时间戳(10位整数)，如：1332888820
        timestamp = time.localtime(timestamp)
        ## 经过localtime转换后变成
        ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
        # 最后再经过strftime函数转换为正常日期格式。
        return time.strftime(format, timestamp)

    def signatureJWT(self, message):
        """ Python generate HMAC-SHA-256 from string """
        return hmac.new(
            key=self.secretkey,
            msg=message,
            digestmod=hashlib.sha256
        ).hexdigest()

    def createJWT(self, payload={}, expiredSeconds=3600):
        """ 生成token: https://tools.ietf.org/html/rfc7519
        @param payload dict: 自定义公有或私有载荷, 存放有效信息的地方;
        @param expiredSeconds int: Token过期时间,单位秒,签发时间是本地当前时间戳,此参数指定签发时间之后多少秒过期;
        """
        #1. check params
        if isinstance(payload, dict):
            for i in self._payloadkey:
                if i in payload:
                    raise KeyError("Standard key exists in payload")
        else:
            raise TypeError("payload is not a dict")

        #2. predefined data
        payload.update(self._payload)
        payload.update(
            exp=self.timestamp_after_timestamp(self.get_current_timestamp(), seconds=expiredSeconds),
            iat=self.get_current_timestamp()
        )

        #3. base64 urlsafe encode
        #头部编码
        first_part  = base64.urlsafe_b64encode(json.dumps(self._header, sort_keys=True, separators=(',', ':')))
        #载荷消息体编码
        second_part = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(',', ':')))
        #签名以上两部分: 把header、playload的base64url编码加密后再次base64编码
        third_part  = base64.urlsafe_b64encode(self.signatureJWT("{0}.{1}".format(first_part, second_part)))

        #4. returns the available token
        token = first_part + '.' + second_part + '.' + third_part
        logging.info("Generating token ok")
        return token

    def analysisJWT(self, token):
        """ 解析token, 返回解码后的header、payload、signature等 """
        _header, _payload, _signature = token.split(".")
        data = {
            "header": json.loads(base64.urlsafe_b64decode(str(_header))),
            "payload": json.loads(base64.urlsafe_b64decode(str(_payload))),
            "signature": base64.urlsafe_b64decode(str(_signature))
        }
        logging.debug("analysis token: {0}".format(data))
        return data

    def verifyJWT(self, token):
        """ 验证token
        @param token str unicode: 请求生成的token串
        >> 1. 验证并拆分token为header、payload、signature, 分别解码验证;
        >> 2. 验证header
        >> 3. payload一致性验证后, 验证过期时间;
        >> 4. 根据header、payload用密钥签名对比请求的signature;
        """
        logging.debug("verify token: {0}".format(token))
        #1. 拆分解析
        if isinstance(token, (str, unicode)):
            if token.count(".") == 2:
                token = self.analysisJWT(token)
            else:
                raise InvalidTokenError("invalid token")
        else:
            raise TypeError("token is in string or Unicode format")

        #2. 验证header
        if self._header == token["header"]:
            payload = token["payload"]
        else:
            raise InvalidTokenError("header missmatch")

        #3. 验证payload
        for i in self._payloadkey:
            if i in ("exp", "iat"): continue
            #logging.debug("verify payload key: {0}: {1}".format(i, payload.get(i) == self._payload.get(i)))
            if payload.get(i) != self._payload.get(i):
                raise InvalidTokenError("payload contains standard declaration keys")
        if self.get_current_timestamp() > payload["exp"]:
            raise TokenExpiredError("token expired")

        #4. 验证签名
        #头部编码
        first_part  = base64.urlsafe_b64encode(json.dumps(token["header"], sort_keys=True, separators=(',', ':')))
        #载荷消息体编码
        second_part = base64.urlsafe_b64encode(json.dumps(token["payload"], sort_keys=True, separators=(',', ':')))
        #签名以上两部分: 把header、playload的base64url编码加密后再次base64编码.
        third_part  = self.signatureJWT("{0}.{1}".format(first_part, second_part))
        #此处......
        if token["signature"] == third_part:
            logging.info("verify token pass")
            return True
        else:
            raise SignatureBadError("invalid signature")
