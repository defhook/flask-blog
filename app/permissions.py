#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask_login import current_user
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

permission_deny = Permission(role_deny)
permission_user = (Permission(role_user) | permission_deny.reverse())
permission_blogger = (Permission(role_blogger) | permission_user)
permission_moderator = (Permission(role_moderator) | permission_blogger)
permission_admin = (Permission(role_admin) | permission_moderator)


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, "id"):
        identity.provides.add(UserNeed(current_user.id))
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))
