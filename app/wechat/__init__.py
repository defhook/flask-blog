#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from flask import Blueprint

wechat = Blueprint('wechat', __name__, static_folder='static', template_folder='templates')

import views
