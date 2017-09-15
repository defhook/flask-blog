#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import send_from_directory, redirect, url_for
from . import basedir
from . import app
import os.path


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(basedir, 'static/img'),
                               'favicon.ico')


@app.route('/')
def redirect_blog():
    return redirect(url_for('blog.index'))
