#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, MetaData
# from sqlalchemy.orm import scoped_session, sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
from flask_blogging import SQLAStorage, BloggingEngine
from flask_cache import Cache
from markdown.extensions.codehilite import CodeHiliteExtension
from flask_sqlalchemy import SQLAlchemy


blog_engine = BloggingEngine(extensions=CodeHiliteExtension({}))
# db_session = scoped_session(sessionmaker(autocommit=False,
#                                          autoflush=False,
#                                          bind=engine))
# Base = declarative_base()
# Base.query = db_session.query_property()
db = SQLAlchemy()


def init_app(app):
    """
    http://flask.pocoo.org/docs/0.11/patterns/sqlalchemy/
    :return:
    """
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
    meta = MetaData()
    cache = Cache()
    db.init_app(app)
    sql_storage = SQLAStorage(engine=engine, metadata=meta, db=db)

    meta.create_all(bind=engine)
    blog_engine.init_app(app, sql_storage, cache)
