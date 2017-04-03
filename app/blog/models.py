#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import

from datetime import datetime
from flask import current_app
from werkzeug.utils import cached_property, escape
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin, AnonymousUserMixin
from markdown import markdown
from app import login_master
from app.extensions import db
from app.permissions import permission_admin, permission_moderator, permission_blogger
import bleach
import hashlib
import urllib

users_roles = db.Table('users_roles',
             # meta,
             db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
             db.Column('role_id', db.Integer, db.ForeignKey('roles.id')))


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))

    def __init__(self, *args, **kwargs):
        super(Role, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)
    username = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(64))
    password_hash = db.Column(db.String(128), nullable=False)
    # db.String 和 db.Text 的区别在于后者不需要指定最大长度
    about_me = db.Column(db.String(100))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic',
                            cascade='all, delete-orphan')
    active = db.Column(db.Boolean, default=False, nullable=False)
    roles = db.relationship(
        'Role',
        secondary=users_roles,
        backref=db.backref('users', lazy='dynamic')
    )

    """
    回引中的 lazy 参数指定为 joined。这个 lazy 模式可以实现立即从联结查询中加载相关对象

    例如,如果某个用户关注了 100 个用户,调用 user.followed.all() 后会返回一个列表,
    其中包含 100 个 Follow 实例,每一个实例的 follower 和 followed 回引属性都指向相应的用户。
    设定为 lazy='joined' 模式,就可在一次数据库查询中完成这些操作。
    如果把 lazy 设为默认值 select,那么首次访问 follower 和 followed 属性时才会加载对应的用户,
    而且每个属性都需要一个单独的查询,这就意味着获取全部被关注用户时需要增加 100 次额外的数据库查询。
    """
    # lazy 参数都在“一”这一侧设定, 返回的结果是“多”这一侧中的记录。
    # 使用dynamic则关系属性不会直接返回记录,而是返回查询对象,所以在执行查询之前还可以添加额外的过滤器。
    """
    cascade 参数配置在父对象上执行的操作对相关对象的影响。
    比如,层叠选项可设定为: 将用户添加到数据库会话后,要自动把所有关系的对象都添加到会话中。
    层叠选项的默认值能满足大多数情况的需求,但对这个多对多关系来说却不合用。
    删除对象时,默认的层叠行为是把对象联接的所有相关对象的外键设为空值。
    但在关联表中,删除记录后正确的行为应该是把指向该记录的实体也删除,因为这样能有效销毁联接。这就是层叠选项值 delete-orphan 的作用。

    cascade 参数的值是一组由逗号分隔的层叠选项.all 表示除了 delete-orphan 之外的所有层叠选项。
    设为 all, delete-orphan 的意思是启用所有默认层叠选项,而且还要删除孤儿记录。
    """
    # followed = db.relationship('Follow',
    #                            foreign_keys=[Follow.follower_id],
    #                            backref=db.backref('follower', lazy='joined'),
    #                            lazy='dynamic',
    #                            cascade='all, delete-orphan')
    # followers = db.relationship('Follow',
    #                             foreign_keys=[Follow.followed_id],
    #                             backref=db.backref('followed', lazy='joined'),
    #                             lazy='dynamic',
    #                             cascade='all, delete-orphan')
    # 为了完成对数据库的修改,User 和 Post 模型还要建立与 comments 表的一对多关系
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    # 添加到 User 模型中的类方法,用来生成虚拟数据
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            # 这些虚拟对象的属性由 ForgeryPy 的随机信息生成器生成,其中的名字、电子邮件地址、句子等属性看起来就像真的一样
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     # confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            # ForgeryPy 随机生成这些信息,因此有重复的风险
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                # 这个异常的处理方式是,在继续操作之前回滚会话。在循环中生成重复内容时不会把用户写入数据库,因此生成的虚拟用户总数可能会比预期少

    def __init__(self, email, pwd, active=False, **kwargs):
        super().__init__(**kwargs)
        self.email = email
        self.password = pwd
        self.active = active

    """
    Python内置的@property装饰器就是负责把一个方法变成属性调用的.

    我们在对实例属性操作的时候，就知道该属性很可能不是直接暴露的，而是通过getter和setter方法来实现的。
    还可以定义只读属性，只定义getter方法，不定义setter方法就是一个只读属性.
    反之就变成不可读了，是名为password的只写属性。也就是下面这里的用法。
    如果试图读取 password 属性的值,则会返回错误,因为生成散列值后就无法还原成原来的密码了。
    """

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        if password is None:
            raise TypeError('password is not nullable')
        self.password_hash = generate_password_hash(password)

    # 如果这个方法返回 True,就表明密码是正确的。
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        # dumps() 方法为指定的数据生成一个加密签名,然后再对数据和签名进行序列化,生成令牌字符串。
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            # 为了解码令牌,序列化对象提供了 loads() 方法,其唯一的参数是令牌字符串
            data = s.loads(token)
        except Exception:
            return False
        if data.get('confirm') != self.id:
            return False
        # self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    # 检查管理员权限的功能经常用到,因此使用单独的方法 is_administrator() 实现。
    @cached_property
    def is_administrator(self):
        return permission_admin.can()

    @cached_property
    def is_moderator(self):
        return permission_moderator.can()

    @property
    def is_authenticated(self):
        return not isinstance(self, AnonymousUserMixin)

    @property
    def is_blogger(self):
        return permission_blogger.can()

    # last_seen 字段创建时的初始值也是当前时间,但用户每次访问网站后,这个值都会被刷新。所以添加此处的方法完成这个操作
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.active

    @cached_property
    def avatar(self):
        # Set your variables here
        email = self.email
        default = 'monsterid'
        size = 40

        # construct the url
        gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower().encode('utf-8')).hexdigest() + "?"
        gravatar_url += urllib.parse.urlencode({'d':default, 's':str(size)})
        return gravatar_url

    def __repr__(self):
        return '<User %r>' % self.username

    def __str__(self):
        return self.nickname


# 出于一致性考虑,我们还定义了 AnonymousUser 类,并实现了 can() 方法和 is_administrator() 方法。
class AnonymousUser(AnonymousUserMixin):
    provides = []

    @cached_property
    def is_administrator(self):
        return False

    @cached_property
    def is_moderator(self):
        return False

    @cached_property
    def is_authenticated(self):
        return False

    @cached_property
    def is_blogger(self):
        return False

    def allows(self, identity):
        return False


# 将 AnonymousUser 类设为用户未登录时 current_user 的值。
# 这样程序不用先检查用户是否登录,就能自由调用 current_user.can() 和 current_user.is_administrator()。
login_master.anonymous_user = AnonymousUser

"""
Flask-Login 要求程序实现一个回调函数,使用指定的标识符加载用户
加载用户的回调函数接收以 Unicode 字符串形式表示的用户标识符。
如果能找到用户,这个函数必须返回用户对象;否则应该返回 None.

记住Flask-Login里的user_id一直是unicode类型的，所以在我们把id传递给Flask-SQLAlchemy时，有必要把它转化成integer类型
"""


@login_master.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    # title_html = db.Column(db.Text)
    intro = db.Column(db.Text)
    # intro_html = db.Column(db.Text)
    body = db.Column(db.Text)
    publish = db.Column(db.Boolean, default=True)  # 不公开的文章只有moderator及以上才可见
    post_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # 和 User 模型之间是一对多关系
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    view_times = db.Column(db.Integer, default=1)

    @property
    def category_name(self):
        return Category.query.filter_by(id=self.category_id).first().category_name

    # 添加到 Post 模型中的类方法,用来生成虚拟数据
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            """
            随机生成文章时要为每篇文章随机指定一个用户。
            为此,我们使用 offset() 查询过滤器。这个过滤器会跳过参数中指定的记录数量。
            通过设定一个随机的偏移值,再调用 first() 方法,就能每次都获得一个不同的随机用户。
            """
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(title=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                     intro=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                     body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

    @staticmethod
    # on_changed_body 函数把 body 字段中的文本渲染成 HTML 格式,结果保存在 body_html 中,
    # 自动且高效地完成 Markdown 文本到 HTML 的转换。
    # def on_changed_title(target, value, oldvalue, initiator):
    #     allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code',
    #                     'em', 'i', 'strong',
    #                     'h1', 'h2', 'h3']
    # def on_changed_intro(target, value, oldvalue, initiator):
    #     allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
    #                     'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
    #                     'h1', 'h2', 'h3', 'p']
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'h4', 'p', 'q',
                        'img', 'hr', 'sub', 'sup', 'del',
                        'dl', 'dt', 'dd']
        # 加了这个终于可以显示图片了，否则哪怕有上面的也不行
        attrs = {
            '*': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt'],
        }
        """
        真正的转换过程分三步完成。
        首先,markdown() 函数初步把 Markdown 文本转换成 HTML。
        然后,把得到的结果和允许使用的 HTML 标签列表传给 clean() 函数。clean() 函数删除所有不在白名单中的标签。
        转换的最后一步由 linkify() 函数完成,这个函数由 Bleach 提供,把纯文本中的 URL 转换成适当的 <a> 链接。

        最后一步是很有必要的,因为 Markdown 规范没有为自动生成链接提供官方支持。
        PageDown 以扩展的形式实现了这个功能,因此在服务器上要调用 linkify() 函数。
        """
        # target.title_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
        # tags=allowed_tags, strip=True))
        # target.intro_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
        # tags=allowed_tags, strip=True))
        target.body_html = bleach.linkify(
            bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, attributes=attrs, strip=True))


# on_changed_body 函数注册在 body 字段上,是 SQLAlchemy“set”事件的监听程序,
# 这意味着只要这个类实例的 body 字段设了新值,函数就会自动被调用
# db.event.listen(Post.title, 'set', Post.on_changed_title)
# db.event.listen(Post.intro, 'set', Post.on_changed_intro)
db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # Comment 模型的属性几乎和 Post 模型一样,不过多了一个 disabled 字段。这是个布尔值字段,协管员通过这个字段查禁不当评论。
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @property
    def comment_of_which_post(self):
        post = Post.query.filter_by(id=self.post_id).first()
        if post:
            return post.title
        else:
            return "已删除文章"

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['p', 'a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong',
                        'h3', 'h4', 'li', 'ol', 'ul', 'blockquote', 'pre', 'hr', 'img', 'sub', 'sup']
        attrs = {
            '*': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt'],
        }
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, attributes=attrs, strip=True))

    """
    和博客文章一样,评论也定义了一个事件,在修改 body 字段内容时触发,自动把 Markdown 文本转换成 HTML。
    转换过程和第 11 章中的 博客文章一样,不过评论相对较短,而且对 Markdown 中允许使用的 HTML 标签要求更严格,要删除与段落相关的标签,只留下格式化字符的标签。
    """


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


# 为了完成对数据库的修改,User 和 Post 模型还要建立与 comments 表的一对多关系


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(64))
    posts = db.relationship('Post', backref='category', lazy='dynamic')


class HomePage(db.Model):
    __tablename__ = 'homepages'
    id = db.Column(db.Integer, primary_key=True)
    view_times = db.Column(db.Integer, default=1)
