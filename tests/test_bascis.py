#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from flask import current_app
from app import app, db


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)
