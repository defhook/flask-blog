#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template
from flask_mail import Message
from threading import Thread
from . import mail


def __send_async_email(cur_app, msg):
    with cur_app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    from .manage import app
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    fork = Thread(target=__send_async_email, args=[app, msg])
    fork.start()
    return fork
