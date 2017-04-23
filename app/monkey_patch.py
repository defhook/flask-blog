#!/usr/bin/python
# -*- encoding:utf-8 -*-
"""
Name: monkey_patch
Date: 2017/4/23 17:14
Author: lniwn
E-mail: lniwn@live.com

"""

from __future__ import print_function, unicode_literals
from flask_bootstrap import WebCDN, ConditionalCDN, BOOTSTRAP_VERSION,\
    JQUERY_VERSION, HTML5SHIV_VERSION, RESPONDJS_VERSION


def patch_bootstrap_cdn(app):
    cdns = app.extensions['bootstrap']['cdns']
    cdn_domain = app.config['PUBLIC_CDN_DOMAIN']
    static = cdns['static']
    local = cdns['local']

    def lwrap(cdn, primary=static):
        return ConditionalCDN('BOOTSTRAP_SERVE_LOCAL', primary, cdn)

    bootstrap = lwrap(
        WebCDN('//%s/bootstrap/%s/' % (cdn_domain,
               BOOTSTRAP_VERSION)), local)

    jquery = lwrap(
        WebCDN('//%s/jquery/%s/' % (cdn_domain,
               JQUERY_VERSION)), local)

    html5shiv = lwrap(
        WebCDN('//%s/html5shiv/%s/' % (cdn_domain,
               HTML5SHIV_VERSION)))

    respondjs = lwrap(
        WebCDN('//%s/respond.js/%s/' % (cdn_domain,
               RESPONDJS_VERSION)))

    cdns['bootstrap'] = bootstrap
    cdns['jquery'] = jquery
    cdns['html5shiv'] = html5shiv
    cdns['respond.js'] = respondjs
