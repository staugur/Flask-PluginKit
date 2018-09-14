# -*- coding: utf-8 -*-
"""
    ProcessName_XXX.views.FrontView
    ~~~~~~~~~~~~~~

    The blueprint for front view.

    :copyright: (c) 2018 by staugur.
    :license: MIT, see LICENSE for more details.
"""

from flask import Blueprint, g, redirect
from utils.web import login_required
from config import SSO

# 初始化前台蓝图
FrontBlueprint = Blueprint("front", __name__)

@FrontBlueprint.route('/')
def index():
    # 首页
    return "登录状态: {}".format(g.signin)

@FrontBlueprint.route("/setting/")
@login_required
def userSet():
    # 用户设置
    return redirect("{}/user/setting/".format(SSO["sso_server"].strip("/")))
