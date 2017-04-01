#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import

from flask import Flask
from sqlalchemy import create_engine
from .extensions import *

import os

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, instance_relative_config=True)


# 导入模块
# from .wechat_channel import ws
# from .wechat import wechat
from .blog import blog
from . import index


def __init_watchdog():
    import logging
    from logging.handlers import SMTPHandler, RotatingFileHandler

    mail_handler = SMTPHandler(
        (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        app.config['FLASKY_MAIL_SENDER'],
        [app.config['FLASKY_ADMIN_MAIL']],
        app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + 'Application Error',
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']),
        secure=app.config['MAIL_USE_SSL']
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    file_handler = RotatingFileHandler(
        app.config['ROTATING_LOG_PATH'],
        maxBytes=2*1024*1024,
        backupCount=1
    )
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)


def init_app():
    # 加载配置
    app.config.from_pyfile(os.path.join(basedir, '../config.py'))
    app.config.from_pyfile('config_dev.py')

    # 注册蓝图
    app.register_blueprint(blog, url_prefix='/blog')
    # app.register_blueprint(blog, url_prefix='/')
    # app.register_blueprint(wechat, url_prefix='/wechat')
    # app.register_blueprint(wechat, url_prefix='/weixin')

    # 初始化插件
    mail_engine.init_app(app)
    db.init_app(app)
    cache.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    page_down.init_app(app)
    principal.init_app(app)
    login_master.init_app(app)
    __init_watchdog()

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)

    meta.create_all(bind=engine)
    # ws.init_app(app)

    if not app.config['DEBUG'] and not app.config['DEV']:
        from flask_sslify import SSLify
        SSLify(app, subdomains=True)


init_app()
