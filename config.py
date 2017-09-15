#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
默认配置，不包含敏感信息，可上传到GitHub进行备份
"""
from __future__ import print_function, unicode_literals, absolute_import

DEBUG = False

# database
SQLALCHEMY_DATABASE_URI = ''
SQLALCHEMY_TRACK_MODIFICATIONS = True
# SQLALCHEMY_RECORD_QUERIES 告诉 Flask-SQLAlchemy 启用记录查询统计数字的功能。
SQLALCHEMY_RECORD_QUERIES = True
FLASKY_SLOW_DB_QUERY_TIME = 0.5
SQLALCHEMY_ECHO = False
SQLALCHEMY_COMMIT_ON_TEARDOWN = True

# wechat
APP_ID = ""
APP_SECRET = ""
TOKEN = ""
ENCODINGAESKEY = ""

# flask
SECRET_KEY = ''
LOGGER_NAME = ''
ROTATING_LOG_PATH = ''
PREFERRED_URL_SCHEME = 'http'
BOOTSTRAP_CDN_FORCE_SSL = False
# SERVER_NAME = 'oaoa.me'
TEMPLATES_AUTO_RELOAD = True

# custom
MAIL_SERVER = 'smtp.qq.com'
# 163服务器端口号: http://help.163.com/10/1111/15/6L7HMASV00753VB8.html
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
FLASKY_MAIL_SUBJECT_PREFIX = '[OAOA的小站]'
FLASKY_MAIL_SENDER = ''
FLASKY_ADMIN_NAME = ''
FLASKY_ADMIN_MAIL = ''
FLASKY_ADMIN_NICK = ''
FLASKY_ADMIN_ABOUT = ''
FLASKY_POSTS_PER_PAGE = 10
FLASKY_FOLLOWERS_PER_PAGE = 20
FLASKY_COMMENTS_PER_PAGE = 10
PUBLIC_CDN_DOMAIN = 'cdn.bootcss.com'  # 公用js文件的cdn地址

# flask-login
SESSION_PROTECTION = 'strong'  # strong basic None

# flask-cdn
CDN_DOMAIN = 'lniwn.oschina.io/flask-blog/app'
CDN_ENDPOINTS = ['static']
CDN_HTTPS = False

# flask-cache
CACHE_TYPE = 'simple'
