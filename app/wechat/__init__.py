#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import Blueprint

wechat = Blueprint('wechat', __name__, static_folder='static', template_folder='templates')

from . import views
