#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from flask import request, redirect
from wechat_sdk import WechatBasic
import functools


def check_signature(func):
    """
    微信签名验证
    :param func:装饰函数
    :return:
    """
    @functools.wraps
    def wrap_func(*args, **kwargs):
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')

        wechat = init_wechat_sdk()
        if not wechat.check_signature(signature=signature,
                                      timestamp=timestamp,
                                      nonce=nonce):
            if request.method == 'POST':
                return "signature failed"
            else:
                return redirect(app.config['MAIN_URL'])

        return func(*args, **kwargs)

    return wrap_func


def init_wechat_sdk():
    """
    初始化微信sdk
    :return: WechatBasic
    """
    access_token = db.get("wechat:access_token")
    jsapi_ticket = db.get("wechat:jsapi_ticket")
    token_expires_at = db.get("wechat:access_token_expires_at")
    ticket_expires_at = db.get("wechat:jsapi_ticket_expires_at")
    if access_token and jsapi_ticket and token_expires_at and ticket_expires_at:
        wechat = WechatBasic(appid=app.config['APP_ID'],
                             appsecret=app.config['APP_SECRET'],
                             token=app.config['TOKEN'],
                             access_token=access_token,
                             access_token_expires_at=int(token_expires_at),
                             jsapi_ticket=jsapi_ticket,
                             jsapi_ticket_expires_at=int(ticket_expires_at))
    else:
        wechat = WechatBasic(appid=app.config['APP_ID'],
                             appsecret=app.config['APP_SECRET'],
                             token=app.config['TOKEN'])
        access_token = wechat.get_access_token()
        db.set("wechat:access_token", access_token['access_token'], 7000)
        db.set("wechat:access_token_expires_at",
                  access_token['access_token_expires_at'], 7000)
        jsapi_ticket = wechat.get_jsapi_ticket()
        db.set("wechat:jsapi_ticket", jsapi_ticket['jsapi_ticket'], 7000)
        db.set("wechat:jsapi_ticket_expires_at",
                  jsapi_ticket['jsapi_ticket_expires_at'], 7000)

    return wechat