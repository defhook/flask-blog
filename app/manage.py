#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager, Shell
from . import create_app, db
from app.blog.models import User, Follow, Role, Permission, Post, Comment, HomePage


app = create_app()
master = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission, Post=Post)

master.add_command('shell', Shell(make_context=make_shell_context))
master.add_command('db', MigrateCommand)


@master.command
def deploy():
    from flask_migrate import upgrade
    from app.blog.models import Role, User

    # 定义这些函数时考虑到了多次执行的情况,所以即使多次执行也不会产生问题。
    # 因此每次安装或升级程序时只需运行 deploy 命令就能完成所有操作。
    # 把数据库迁移到最新修订版本
    upgrade()

    # 创建用户角色
    Role.insert_roles()

    # 让所有用户都关注此用户
    User.add_self_follows()


@master.command
def test():
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
