#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import Blueprint

blog = Blueprint('blog', __name__, static_folder='static', template_folder='templates')

from . import views
from . import models
from app import permissions


@blog.app_context_processor
def inject_permissions():
    """
    在模板中可能也需要检查权限,所以 Permission 类为所有位定义了常量以便于获取。
    为了避免每次调用 render_template() 时都多添加一个模板参数,可以使用上下文处理器。
    上下文处理器能让变量在所有模板中全局可访问。
    """
    return dict(permissions=permissions)
