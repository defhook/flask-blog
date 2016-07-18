#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from . import app


@app.route('/')
def handle_index():
    return '欢迎来到OAOA的小站'

