#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask_wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(Form):
    """Accepts a nickname and a room."""
    name = StringField('Name', validators=[DataRequired()])
    room = StringField('Room', validators=[DataRequired()])
    submit = SubmitField('Enter Chatroom')
