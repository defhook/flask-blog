#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from flask import render_template
from .. import blog


@blog.route('/')
def handle_index():
    return render_template('blog.html')

