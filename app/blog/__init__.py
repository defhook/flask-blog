#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import Blueprint, current_app, request

blog = Blueprint('blog', __name__, static_folder='static', template_folder='templates')

from . import views
from . import models
from urllib.parse import urljoin
from app import permissions


def url_for_cdn(filename):
    cdn_https = current_app.config.get('CDN_HTTPS', False)
    scheme = 'http'
    if cdn_https or request.is_secure:
        scheme = 'https'
    return urljoin(scheme + '://' + current_app.config['PUBLIC_CDN_DOMAIN'], filename)


@blog.app_context_processor
def inject_permissions():
    return dict(permissions=permissions, url_for_cdn=url_for_cdn)
