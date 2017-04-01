#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, with_statement
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_principal import Principal
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_cache import Cache
from flask_mail import Mail
from flask_bootstrap import Bootstrap


__all__ = ['mail_engine', 'db', 'cache', 'bootstrap', 'moment',
           'page_down', 'principal', 'login_master', 'meta']

mail_engine = Mail()
db = SQLAlchemy()
cache = Cache()
bootstrap = Bootstrap()
moment = Moment()
page_down = PageDown()
principal = Principal()
login_master = LoginManager()
meta = MetaData()
