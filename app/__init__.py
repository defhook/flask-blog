#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import

from flask import Flask
from flask_blogging import SQLAStorage
from sqlalchemy import create_engine
from .extensions import *

import os

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, instance_relative_config=True)


def init_mail():
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(
        (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        app.config['FLASKY_MAIL_SENDER'],
        [app.config['FLASKY_ADMIN']],
        app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + 'Application Error',
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']),
        secure=app.config['MAIL_USE_SSL']
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)


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
    init_mail()

    login_master.session_protection = 'strong'

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
    with app.app_context():
        sql_storage = SQLAStorage(engine=engine, metadata=meta, db=db)
    # meta.create_all(bind=engine)
    blog_engine.init_app(app, sql_storage, cache)
    # ws.init_app(app)

    if not app.config['DEBUG'] and not app.config['DEV']:
        from flask_sslify import SSLify
        SSLify(app, subdomains=True)


# 导入模块
# from .wechat_channel import ws
# from .wechat import wechat
from .blog import blog
from . import index

init_app()
