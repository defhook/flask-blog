#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from .extensions import mail_engine


def __send_async_email(cur_app, msg):
    with cur_app.app_context():
        mail_engine.send(msg)


def send_email(to, subject, template, **kwargs):
    msg = Message(current_app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=current_app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    fork = Thread(target=__send_async_email, args=[current_app, msg])
    fork.start()
    return fork



