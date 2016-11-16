#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms import ValidationError
from app.blog.models import User


class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登陆')


class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    """
    这个表单使用 WTForms 提供的 Regexp 验证函数,确保 username 字段只包含字母、数字、下划线和点号。
    这个验证函数中正则表达式后面的两个参数分别是正则表达式的旗标和验证失败时显示的错误消息。
    """
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    # EqualTo这个验证函数要附属到两个密码字段中的一个上,另一个字段则作为参数传入。
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2', message='两次密码要一样噢~')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    """
    这个表单还有两个自定义的验证函数,以方法的形式实现。
    如果表单类中定义了以 validate_ 开头且后面跟着字段名的方法,这个方法就和常规的验证函数一起调用。
    """
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            # 自定义的验证函数要想表示验证失败,可以抛出 ValidationError 异常,其参数就是错误消息
            raise ValidationError('邮箱已被注册啦 ╮(￣▽￣)╭ ')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被使用啦 ╮(￣▽￣)╭')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('当前密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次密码要一样噢~')])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('确认修改密码')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('重设密码')


class PasswordResetForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='两次密码要一样噢~')])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('重设密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('无效邮箱')
