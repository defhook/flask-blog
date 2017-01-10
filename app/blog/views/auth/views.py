#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.blog.models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm
from app import db, login_master
from app.email import send_email
from app.blog import blog


# 登入用户，登录路由
@blog.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # db.create_all() 别人说先这个方法没用啊
    if form.validate_on_submit():
        # 反正可以运行到下面这句话之前，而且form.email.data是存在的。用print试过了。
        # login and validate the user... 在此处去执行回调函数，说明还是回调那里的问题，跟这边应该无关。通过回调函数的验证才能继续执行下面的代码
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            # “记住我”布尔值如果值为 False,那么关闭浏览器后用户会话就过期了,所以下次用户访问时要重新登录。
            # 如果值为 True,那么会在用户浏览器中写入一个长期有效的 cookie,使用这个 cookie 可以复现用户会话
            login_user(user, form.remember_me.data)
            """
            按照第 4 章介绍的“Post/ 重定向 /Get 模式”,提交登录密令的 POST 请求最后也做了重定向,不过目标 URL 有两种可能:
            用户访问未授权的 URL 时会显示登录表单,Flask-Login 会把原地址保存在查询字符串的 next 参数中,这个参数可从 request.args 字典中读取。
            如果查询字符串中没有 next 参数,则重定向到首页。
            """
            return redirect(request.args.get('next') or url_for('blog.article'))
        flash('用户名或密码不正确 ╮(￣▽￣)╭')
    # 当请求类型是 GET 时,视图函数直接渲染模板,即显示表单。因为15行的那个条件判断后为False,根本不会执行
    # 当表单在 POST 请求中提交时, Flask-WTF 中的 validate_on_submit() 函数会验证表单数据,然后尝试登入用户
    return render_template('./auth/login.html', form=form)
    """
    Flask 认为模板的路径是相对于程序模板文件夹而言的。
    为避免与 main 蓝本和后续添加的蓝本发生模板命名冲突,可以把蓝本使用的模板保存在单独的文件夹中。

    我们也可将蓝本配置成使用其独立的文件夹保存模板。
    如果配置了多个模板文件夹,render_template() 函数会首先搜索程序配置的模板文件夹,然后再搜索蓝本配置的模板文件夹。
    """

    """
    在生产服务器上,登录路由必须使用安全的 HTTP,从而加密传送给服务器的表单数据。
    如果没使用安全的 HTTP,登录密令在传输过程中可能会被截取,在服务器上花再多的精力用于保证密码安全都无济于事。
    """


# 登出用户，退出路由
@blog.route('/logout')
@login_required
def logout():
    # 调用 Flask-Login 中的 logout_user() 函数,删除并重设用户会话
    logout_user()
    flash('你已退出。ヾ(￣▽￣)Bye~Bye~')
    return redirect(url_for('blog.index'))


# 用户注册路由
@blog.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
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
