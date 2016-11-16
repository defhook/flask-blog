#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import

from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_cache import Cache
from flask_blogging import BloggingEngine
# from flask_blogging import SQLAStorage
from markdown.extensions.codehilite import CodeHiliteExtension

import os


basedir = os.path.abspath(os.path.dirname(__file__))


# 加载插件
db = SQLAlchemy()
login_master = LoginManager()
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
pagedown = PageDown()
blog_engine = BloggingEngine(extensions=CodeHiliteExtension({}))
cache = Cache()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # 加载配置
    app.config.from_pyfile(os.path.join(basedir, '../config.py'))
    app.config.from_pyfile('config_dev.py')
    __init_app(app)

    # 注册蓝图
    app.register_blueprint(blog, url_prefix='/blog')
    app.register_blueprint(blog, url_prefix='/')
    app.register_blueprint(wechat, url_prefix='/wechat')
    app.register_blueprint(wechat, url_prefix='/weixin')

    # 初始化插件
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_master.session_protection = 'strong'
    login_master.init_app(app)
    pagedown.init_app(app)
    blog_engine.init_app(app, cache)
    ws.init_app(app)

    if not app.config['DEBUG'] and not app.config['DEV']:
        from flask_sslify import SSLify
        SSLify(app, subdomains=True)
    
    return app


def __init_app(app):
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


# 导入模块
from .wechat_channel import ws
from .wechat import wechat
from .blog import blog
from . import index
