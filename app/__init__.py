#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from flask import Flask, request
from .wechat import wechat
from .blog import blog

app = Flask(__name__, instance_relative_config=True)

# 加载配置
app.config.from_json('../default_config.json')
app.config.from_pyfile('app_config.py')

# 注册蓝图
app.register_blueprint(blog, url_prefix='/blog')
app.register_blueprint(blog, url_prefix='/')
app.register_blueprint(wechat, url_prefix='/wechat')
app.register_blueprint(wechat, url_prefix='/weixin')

# 导入主视图
import index
