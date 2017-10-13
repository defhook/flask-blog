#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from app.blog.models import Role, User, Post, Comment, Category, HomePage, Tag
from app import db, cache
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import blog
from app.permissions import permission_blogger, permission_admin


# 为会出现分类列表的排序做准备，涉及到路由'/post/<int:id>'、'/article'和'/article/<category_name>'
def sort_category():
    if Category.query.all():
        category = Category.query.all()
        dict_cg = {}
        for i in category:
            dict_cg[i] = i.posts.count()
        category = sorted(dict_cg, key=dict_cg.__getitem__, reverse=True)
        return category


# 报告缓慢的数据库查询
"""
这个功能使用 after_app_request 处理程序实现,它和 before_app_request 处理程序的工作方式类似,只不过在视图函数处理完请求之后执行。
Flask 把响应对象传给 after_app_ request 处理程序,以防需要修改响应。
在这里,after_app_request 处理程序没有修改响应,只是获取 Flask-SQLAlchemy 记录 的查询时间并把缓慢的查询写入日志。

"""


@blog.after_app_request
def after_request(response):
    """
    get_debug_queries() 函数返回一个列表,其元素是请求中执行的查询
    遍历 get_debug_queries() 函数获取的列表,把持续时间比设定阈值长的查询写入日志。
    写入的日志被设为“警告”等级。如果换成“错误”等级,发 现缓慢的查询时还会发送电子邮件。
    """
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration, query.context))
    return response


"""
Werkzeug Web 服务器本身就有停止选项,但由于服务器运行在单独的线程中,
关闭服务器的唯一方法是发送一个普通的 HTTP 请求.

只有当程序运行在测试环境中时,这个关闭服务器的路由才可用,在其他配置中调用时将不起作用。
在实际过程中,关闭服务器时要调用 Werkzeug 在环境中提供的关闭函数。
调用这个函数且请求处理完成后,开发服务器就知道自己需要优雅地退出了。
"""


@blog.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@blog.route('/', methods=['GET', 'POST'])
def index():
    homepages = HomePage.query.filter_by(id=1).first()
    if not homepages:
        homepages = HomePage(view_times=1)
        db.session.add(homepages)
        db.session.commit()
    try:
        if homepages.view_times > 0:
            homepages.view_times += 1
        else:
            homepages.view_times = 1
        db.session.add(homepages)
        db.session.commit()
    except:
        pass
    return render_template('index.html')


@blog.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
        # 用户发布的博客文章列表通过 User.posts 关系获取,User.posts 返回的是查询对象,
        # 因此可在其上调用过滤器,例如 order_by()。
    posts = user.posts.order_by(Post.post_date.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@blog.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('资料已更新 (｡・`ω´･)')
        return redirect(url_for('.user', username=current_user.username))
    # 为所有字段设定了初始值
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@blog.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_blogger.require(403)
# 用户由 id 指定
def edit_profile_admin(id):
    # 使用 Flask-SQLAlchemy 提供的 get_or_404() 函数,如果提供的 id 不正确,则会返回 404 错误。
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        # user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.username = form.name.data
        # user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('资料已更新 (｡・`ω´･)')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    # form.confirmed.data = user.confirmed
    form.role.data = user.roles[0].id
    form.name.data = user.username
    # form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


# 博客文章的 URL 使用插入数据库时分配的唯一 id 字段构建
@blog.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    post.body_show = True
    # 这个视图函数实例化了一个评论表单,并将其转入 post.html 模板,以便渲染。
    input_hint = '''### h3标题（注意：换行是先敲两个空格再敲回车！）  
***  
+ 三个星号是分隔线。现在这个加号后面一个空格是列表。  
+ *斜体*  
+  **粗体**  
+ `代码`  
+ [完整版 Markdown 语法说明](http://wowubuntu.com/markdown/index.html)  

> 块引用  

    # Python
    print "每行前面加四个空格是代码块"  
 '''
    form = CommentForm(body=input_hint)
    # 提交表单 后,插入新评论的逻辑和处理博客文章的过程差不多
    if form.validate_on_submit():
        # 和 Post 模型一样,评论的 author 字段也不能直接设为 current_user,因为这个变量是上下文代理对象。
        # 真正的 User 对象要 使用表达式 current_user._get_current_object() 获取。
        comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('评论已提交 (｡・`ω´･)')
        # 提交评论后,请求结果是一个重定 向,转回之前的 URL,但是在 url_for() 函数的参数中把 page 设为 -1,
        # 这是个特殊的页 数,用来请求评论的最后一页,所以刚提交的评论才会出现在页面中。
        return redirect(url_for('.post', id=post.id))
    # 程序从查询字符串 中获取页数,发现值为 -1 时,会计算评论的总量和总页数,得出真正要显示的页数。
    page = request.args.get('page', 1, type=int)
    if page == -1:
        # " // "来表示整数除法，返回不大于结果的一个最大的整数，而" / " 则单纯的表示浮点数除法
        page = (post.comments.count() - 1) // \
               current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    # 文章的评论列表通过 post.comments 一对多关系获取,按照时间戳顺序进行排列,再使 用与博客文章相同的技术分页显示。
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    category = sort_category()
    if post.view_times > 0:
        post.view_times += 1
    else:
        post.view_times = 1
    db.session.add(post)
    db.session.commit()
    # 评论列表对象和分页对象都传入了模板,以便渲染。
    return render_template('post.html', posts=[post], form=form, categories=category, comments=comments,
                           pagination=pagination)
    # 评论的渲染过程在新模板 _comments.html 中进行,类似于 _posts.html,但使用的 CSS 类不 同。
    # _comments.html 模板要引入 post.html 中,放在文章正文下方,后面再显示分页导航。

    """ 这是之前的最后一句：

    post.html 模板接收一个列表作为参数,这个列表就是要渲染的文章。
    这里必须要传入列表,因为只有这样,index.html 和 user.html 引用的 _posts.html 模板才能在这个页面中使用。

    return render_template('post.html', posts=[post])
    """


@blog.route('/edit/<int:id>', methods=['GET', 'POST'])
@permission_blogger.require(403)
def edit(id):
    post = Post.query.get_or_404(id)
    if post.category_id:
        category = Category.query.get_or_404(post.category_id)
    if current_user.id != post.author_id:
        abort(403)
    # 这里使用 的 PostForm 表单类和首页中使用的是同一个。
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.intro = form.intro.data
        post.body = form.body.data
        if form.category_name.data:
            category_name_exists = Category.query.filter_by(category_name=form.category_name.data).first()
            if not category_name_exists:
                category = Category(form.category_name.data)
                db.session.add(category)
                db.session.commit()
                post.category_id = category.id
            else:
                post.category_id = category_name_exists.id
        db.session.add(post)
        db.session.commit()
        flash('文章已提交 (｡・`ω´･)')
        return redirect(url_for('.post', id=post.id))
    form.title.data = post.title
    form.intro.data = post.intro
    form.body.data = post.body
    if post.category_id:
        category = Category.query.filter_by(id=post.category.id).first()
        form.category_name.data = category.category_name
    return render_template('edit_post.html', form=form, post=post)


@blog.route('/all')
@login_required
def show_all():
    # cookie 只能在响应对象中设置,因此这两个路由不能依赖 Flask,要使用 make_response() 方法创建响应对象。
    resp = make_response(redirect(url_for('.article')))
    # set_cookie() 函数的前两个参数分别是 cookie 名和值。可选的 max_age 参数设置 cookie 的过期时间,单位为秒。
    # 如果不指定参数 max_age,浏览器关闭后 cookie 就会过期。
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@blog.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.article')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


# 管理评论的路由
# 这个函数很简单,它从数据库中读取一页评论,将其传入模板进行渲染。除了评论列表之外,还把分页对象和当前页数传入了模板。
@blog.route('/moderate')
@login_required
@permission_blogger.require(403)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination, page=page)


"""
以下启用路由和禁用路由都是先加载评论对象,把 disabled 字段设为正确的值,再把评论对象写入数据库。
最后,重定向到评论管理页面,如果查询字符串中指定了 page 参数,会将其传入重定向操作。
_comments.html 模板中的按钮指定了 page 参数,重定向后会返回之前的页面。
"""


@blog.route('/moderate/enable/<int:id>')
@login_required
@permission_blogger.require(403)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@blog.route('/moderate/disable/<int:id>')
@login_required
@permission_blogger.require(403)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@blog.route('/article_new', methods=['GET', 'POST'])
@permission_blogger.require(403)
def article_new():
    form = PostForm()
    if request.method == 'POST' and form.validate_on_submit():
        post_obj = Post(title=form.title.data, intro=form.intro.data, body=form.body.data,
                        author=current_user._get_current_object(),
                        category=Category.query.get(form.category.data))
        post_obj.tags.extend([Tag.get_tag(t_n.strip()) for t_n in form.tags.data.split(',') if t_n])
        try:
            db.session.add(post_obj)
        except Exception:
            db.session.rollback()
        else:
            db.session.commit()
        return redirect(url_for('.article'))
    # form.category.data = Category.query.first_or_404()
    return render_template('article_new.html', form=form)
    # 这样修改之后,首页中的文章列表只会显示有限数量的文章。若想查看第 2 页中的文章,
    # 要在浏览器地址栏中的 URL 后加上查询字符串 ?page=2。


@blog.route('/article', methods=['GET', 'POST'])
@cache.cached(timeout=120, key_prefix='home/%s')
def article():
    page = request.args.get('page', 1, type=int)
    query = Post.query
    pagination = query.order_by(Post.post_date.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    # posts = Post.query.order_by(Post.post_date.desc()).all()
    posts = pagination.items
    category = sort_category()
    for post in posts:
        post.body_show = False
    return render_template('article.html', posts=posts, categories=category, show_followed=show_followed,
                           pagination=pagination)


@blog.route('/article/<category_name>', methods=['GET', 'POST'])
def article_category_name(category_name):
    # form = PostForm()
    # if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
    #     post = Post(title=form.title.data, intro=form.intro.data, body=form.body.data,
    # author=current_user._get_current_object())
    #     db.session.add(post)
    #     return redirect(url_for('.article'))
    page = request.args.get('page', 1, type=int)
    if not Category.query.filter_by(category_name=category_name).all():
        abort(404)
    _category = Category.query.filter_by(category_name=category_name).first()
    pagination = Post.query.filter_by(category_id=_category.id).order_by(Post.post_date.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    category = sort_category()
    for post in posts:
        post.body_show = False
    return render_template('article.html', posts=posts, categories=category, show_followed=show_followed,
                           pagination=pagination)


@blog.route('/delete-article/<int:id>')
@login_required
@permission_blogger.require(403)
def delete_article(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('你已成功删除了文章《%s》' % post.title)
    return redirect(url_for('.article'))


@blog.route('/delete-comment/<int:id>')
@login_required
@permission_blogger.require(403)
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('你已成功删除了文章《%s》的评论"%s"' % (comment.comment_of_which_post, comment.body))
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@blog.route('/resume')
@cache.cached(timeout=120, key_prefix='home/%s')
def resume():
    return render_template('resume.html')


@blog.route('/contact')
@cache.cached(timeout=120, key_prefix='home/%s')
def contact():
    return render_template('contact.html')


@blog.route('/lab')
@cache.cached(timeout=120, key_prefix='home/%s')
def lab():
    return render_template('lab.html')
