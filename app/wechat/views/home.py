#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template, abort
from jinja2 import TemplateNotFound
from .. import wechat


@wechat.route('/', defaults={'page': 'wechat'})
@wechat.route('/<page>')
def handle_page(page):
    try:
        return render_template('%s.html' % page)
    except TemplateNotFound:
        abort(404)


@wechat.route('/control-pc/<mac>')
def handle_pc(mac=None):
    return render_template('control-pc.html', mac)
