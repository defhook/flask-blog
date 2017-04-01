#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from flask import current_app
from app import app, db


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_app_exists(self):
        self.assertFalse(current_app is None)
