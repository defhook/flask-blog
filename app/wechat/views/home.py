#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template, abort, session, redirect, url_for, request
from jinja2 import TemplateNotFound
from .. import wechat
from .forms import LoginForm


@wechat.route('/', defaults={'page': 'wechat'})
@wechat.route('/<page>')
def handle_page(page):
    try:
        if page != 'ws_index':
            return render_template('%s.html' % page)
        else:
            raise TemplateNotFound(page, 'Invalid query')
    except TemplateNotFound:
        abort(404)
#
#
# @wechat.route('/control-pc/<mac>')
# def handle_pc(mac=None):
#     return render_template('control-pc.html', mac)


@wechat.route('/ws', methods=['GET', 'POST'])
def handle_ws():
    """"Login form to enter a room."""
    form = LoginForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['room'] = form.room.data
        return redirect(url_for('.handle_chat'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.room.data = session.get('room', '')
    return render_template('ws_index.html', form=form)


@wechat.route('/ws/chat')
def handle_chat():
    """Chat room. The user's name and room must be stored in
    the session."""
    name = session.get('name', '')
    room = session.get('room', '')
    if name == '' or room == '':
        return redirect(url_for('.handle_ws'))
    return render_template('chat.html', name=name, room=room)
