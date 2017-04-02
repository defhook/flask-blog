#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager, Shell
from app import app
from app.extensions import db
from app.blog.models import User, Role, Post
from app import permissions
from app.permissions import (role_admin, role_moderator,
                             role_blogger, role_user, role_deny)

master = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,
                permissions=permissions, Post=Post)

master.add_command('shell', Shell(make_context=make_shell_context))
master.add_command('db', MigrateCommand)


def create_admin(password, **kwargs):
    admin_user = User.query.filter_by(username=app.config['FLASKY_ADMIN_NAME']).first()
    if admin_user is not None:
        return

    # 创建roles表
    roles = (Role(name=role_admin.value, description='超级管理员'),
             Role(name=role_moderator.value, description='版主'),
             Role(name=role_blogger.value, description='有写博客的权限'),
             Role(name=role_user.value, description='有读博客的权限'),
             Role(name=role_deny.value, description='禁止访问')
             )
    for r in roles:
        role = Role.query.filter_by(name=r.name).first()
        if role is None:
            role = r
        role.users = []
        db.session.add(role)

    # 创建admin用户
    admin_user = User(app.config['FLASKY_ADMIN_MAIL'],
                      password,
                      username=app.config['FLASKY_ADMIN_NAME'],
                      active=True,
                      **kwargs)
    db.session.add(admin_user)

    admin = Role.query.filter_by(name=role_admin.value).first()
    admin.users.append(admin_user)
    db.session.add(admin)
    db.session.commit()


@master.option('-p', '--passwd', dest='pwd', default=None, help='administrator password')
def deploy(pwd):
    """
    :param pwd: admin用户的密码，如果是第一次创建，该选项必填
    :return: 
    """
    from flask_migrate import upgrade

    upgrade()
    create_admin(pwd, nickname=app.config['FLASKY_ADMIN_NICK'],
                 about_me=app.config['FLASKY_ADMIN_ABOUT'])


@master.command
def test():
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@master.option('-l', '--length', dest='length', default=25)
@master.option('-d', '--dir', dest='profile_dir', default=None)
def profile(length, profile_dir):
    """Start the application under the code profiler."""
    # 使用 python manage.py profile 启动程序后,终端会显示每条请求的分析数据,其中包含运行最慢的 25 个函数。
    # --length 选项可以修改报告中显示的函数数量
    # 如果指定了--profile-dir 选项,每条请求的分析数据就会保存到指定目录下的一个文件中
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()
