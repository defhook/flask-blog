#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask_login import current_user
# from functools import wraps
# from flask import abort
from flask_principal import (identity_loaded,
                             Permission, RoleNeed, UserNeed)
from app import app


# class Permissions(object):
#     FOLLOW = 0x01
#     COMMENT = 0x02
#     WRITE_ARTICLES = 0x04
#     MODERATE_COMMENTS = 0x08
#     ADMINISTER = 0x80

role_admin = RoleNeed('admin')
role_blogger = RoleNeed('blogger')  # 可以编辑自己的博文
role_moderator = RoleNeed('moderator')  # 可以编辑所有博文
role_user = RoleNeed('user')  # 刚注册的普通用户
role_deny = RoleNeed('deny')  # 黑名单

permission_deny = Permission(role_deny).reverse()
permission_admin = Permission(role_admin)
permission_moderator = Permission(role_moderator, role_admin) & permission_deny
permission_blogger = Permission(role_blogger, role_moderator, role_admin) & permission_deny
permission_user = Permission(role_user, role_blogger, role_moderator, role_admin) & permission_deny


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, "id"):
        identity.provides.add(UserNeed(current_user.id))
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))


# def permission_required_any(*needs):
#     def decorator(f):
#         @wraps(f)
#         def decorator_func(*args, **kwargs):
#             if not _permission_can(*needs, f=any):
#                 abort(403)
#             return f(*args, **kwargs)
#         return decorator_func
#     return decorator
#
#
# def permission_required_all(*needs):
#     def decorator(f):
#         @wraps(f)
#         def decorator_func(*args, **kwargs):
#             if not _permission_can(*needs, f=all):
#                 abort(403)
#             return f(*args, **kwargs)
#         return decorator_func
#     return decorator
#
#
# def admin_required(f):
#     return permission_required_all(permission_admin)(f)
#
#
# def blogger_required(f):
#     return permission_required_any(permission_admin, permission_moderator, permission_blogger)(f)
#
#
# def _permission_can(*needs, f=None):
#     return f(need.can() for need in needs)
