#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager, Shell
from app import app
from app.extensions import db
from app.blog.models import User, Role, Post, Category
from app.permissions import (role_admin, role_moderator,
                             role_blogger, role_user, role_deny)
import codecs

master = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,
                Post=Post, Category=Category)


master.add_command('shell', Shell(make_context=make_shell_context))
master.add_command('db', MigrateCommand)


@master.option('-p', '--password', dest='password',
               help='user password, required')
def create_admin(password):
    admin_user = User.query.filter_by(
        username=app.config['FLASKY_ADMIN_NAME']).first()
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
                      nickname=app.config['FLASKY_ADMIN_NICK'],
                      about_me=app.config['FLASKY_ADMIN_ABOUT'])
    db.session.add(admin_user)

    admin = Role.query.filter_by(name=role_admin.value).first()
    admin.users.append(admin_user)
    db.session.add(admin)
    db.session.commit()


@master.command
def deploy():
    from flask_migrate import upgrade

    upgrade()


@master.option('-r', '--role', dest='role', default='user',
               help='user role name in [admin, moderator, blogger, user, deny], required')
@master.option('-n', '--name', dest='name', default=None,
               help='user name for Log In')
@master.option('-m', '--email', dest='email',
               help='user email, required')
@master.option('-p', '--password', dest='pwd',
               help='user password, required')
@master.option('-i', '--nick', dest='nick', default='',
               help='user nickname')
@master.option('-b', '--about', dest='about', default='',
               help='about me')
def create_user(role, name, email, pwd, nick, about):
    if role not in (role_admin.value, role_moderator.value,
                    role_blogger.value, role_user.value, role_deny.value):
        raise ValueError('Unknown role name %s' % role)
    user = User(email, pwd, username=name, active=True, nickname=nick, about_me=about)
    role_instance = Role.query.filter_by(name=role).first()
    role_instance.users.append(user)
    db.session.add(user)
    db.session.add(role_instance)
    db.session.commit()


@master.option('-s', '--string', dest='strings', default=None,
               help='add category from string list separated by comma')
@master.option('-f', '--file', dest='json_file', default=None,
               help='add category from json file. {"names":[]}')
def add_category(strings, json_file):
    names = []
    if strings is not None:
        names.extend([s.strip() for s in strings.split(',')])
    if json_file is not None:
        with codecs.open(json_file, encoding='utf-8') as fp:
            import json
            names.extend(json.load(fp)['names'])
    for name in names:
        if name:
            c = Category(name)
            db.session.add(c)
    db.session.commit()


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
