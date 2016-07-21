#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from . import app


@app.route('/')
def handle_index():
    return '欢迎来到OAOA的小站'

