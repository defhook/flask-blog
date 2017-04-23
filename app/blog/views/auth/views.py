#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template, redirect, request, url_for, flash, current_app, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import (identity_changed, Identity,
                             AnonymousIdentity)
from app.blog.models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm
from app import db
from app.email import send_email
from app.blog import blog
from app.permissions import permission_deny, permission_admin


# 登入用户，登录路由
@blog.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # 反正可以运行到下面这句话之前，而且form.email.data是存在的。用print试过了。
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            # notify the change of role
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

            # 在黑名单内的用户禁止登陆
            if not permission_deny.can():
                identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
                flash('你已经被限制登录 ╮(￣▽￣)╭')
                return form.redirect('blog.index')

            # “记住我”布尔值如果值为 False,那么关闭浏览器后用户会话就过期了,所以下次用户访问时要重新登录。
            # 如果值为 True,那么会在用户浏览器中写入一个长期有效的 cookie,使用这个 cookie 可以复现用户会话
            login_user(user, form.remember_me.data)
            return form.redirect('blog.article')

        flash('用户名或密码不正确 ╮(￣▽￣)╭')
    return render_template('./auth/login.html', form=form)


# 登出用户，退出路由
@blog.route('/logout')
@login_required
def logout():
    # 调用 Flask-Login 中的 logout_user() 函数,删除并重设用户会话
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    # notify the change of role
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    flash('你已退出。ヾ(￣▽￣)Bye~Bye~')
    return redirect(url_for('blog.index'))


# 用户注册路由
@blog.route('/register', methods=['GET', 'POST'])
@permission_admin.require(401)  # 禁止用户注册
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(form.email.data, form.password.data, username=form.username.data)
        db.session.add(user)
        db.session.commit()
        """
        即便通过配置,程序已经可以在请求末尾自动提交数据库变化,这里也要添加 db.session.commit() 调用。
        问题在于,提交数据库之后才能赋予新用户 id 值,而确认令 牌需要用到 id,所以不能延后提交。
        """
        user.generate_confirmation_token()
        # send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
        flash('现在可以登录啦 ˋ▽ˊ')
        return redirect(url_for('blog.login'))
    return render_template('./auth/register.html', form=form)


@blog.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('你的密码已更新 (｡・`ω´･)')
            return redirect(url_for('blog.index'))
        else:
            flash('当前密码不对 ╮(￣▽￣)╭')
    return render_template("./auth/change_password.html", form=form)


@blog.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('blog.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '重设密码',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('已向 %s 发送了一封邮件，请从邮件重设你的密码 o(*￣▽￣*)ブ' % form.email.data)
        return redirect(url_for('blog.login'))
    return render_template('./auth/reset_password.html', form=form)


@blog.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('blog.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('你的密码已更新 (｡・`ω´･)')
            return redirect(url_for('blog.login'))
        else:
            return redirect(url_for('blog.index'))
    return render_template('./auth/reset_password.html', form=form)
