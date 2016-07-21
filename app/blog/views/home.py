#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template
from .. import blog


@blog.route('/')
def handle_index():
    return render_template('blog.html')

