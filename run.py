#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from app import app, ws

if __name__ == '__main__':
    ws.run(app)
