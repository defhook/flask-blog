#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .wechat import wechat
from .blog import blog
import os

app = Flask(__name__, instance_relative_config=True)
basedir = os.path.abspath(os.path.dirname(__file__))

# 加载配置
app.config.from_json('../config.json')
app.config.from_pyfile('app_config.py')

# 注册蓝图
app.register_blueprint(blog, url_prefix='/blog')
app.register_blueprint(blog, url_prefix='/')
app.register_blueprint(wechat, url_prefix='/wechat')
app.register_blueprint(wechat, url_prefix='/weixin')

# 加载数据库
db = SQLAlchemy(app)

# 导入主视图
from . import index
