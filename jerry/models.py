__author__ = 'wangdai'

from datetime import datetime

from sqlalchemy import Column, ForeignKey, PrimaryKeyConstraint, func
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, String, Text, DateTime, Boolean
from flask import g
from dateutil.relativedelta import relativedelta

from jerry import MODEL_BASE


# many to many relation table
class PostTag(MODEL_BASE):
    __tablename__ = 'post_tag'
    __table_args__ = (
        PrimaryKeyConstraint('post_id', 'tag_id'),
    )

    post_id = Column('post_id', Integer, ForeignKey('post.id'))
    tag_id = Column('tag_id', Integer, ForeignKey('tag.id'))


class Post(MODEL_BASE):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    author_id = Column(Integer, ForeignKey('author.id'), nullable=False)
    html = Column(Text, nullable=False)
    markdown = Column(Text, nullable=False)
    # should be aware that datetime.now() doesn't contain timezone
    # TODO test timezone problem
    published = Column(DateTime, nullable=False, default=datetime.utcnow())
    modified = Column(DateTime, nullable=False, default=datetime.utcnow())
    deleted = Column(Boolean, nullable=False, default=False)
    sticky = Column(Boolean, nullable=False, default=False)

    author = relationship('Author', backref='posts')
    tags = relationship('Tag', secondary=PostTag.__table__, backref='posts')

    def __repr__(self):
        return "<Post(%d, '%s', '%s', '%s')>" % (self.id, self.title, self.published.strftime('%Y-%m-%d'), self.modified.strftime('%Y-%m-%d'))

    @staticmethod
    def query(p=1, num=10, **kwargs):
        tag_id = kwargs.get('tag_id')
        author_id = kwargs.get('author_id')
        deleted = kwargs.get('deleted', 0)
        month = kwargs.get('month')

        q = g.db.query(Post)
        c = g.db.query(func.count('*')).select_from(Post)
        if tag_id:
            tag_id = int(tag_id)
            q = q.join(PostTag, Post.id == PostTag.post_id).filter(PostTag.tag_id == tag_id)
            c = c.join(PostTag, Post.id == PostTag.post_id).filter(PostTag.tag_id == tag_id)
        if author_id:
            author_id = int(author_id)
            q = q.filter(Post.author_id == author_id)
            c = c.filter(Post.author_id == author_id)
        if deleted in [0, 1]:
            q = q.filter(Post.deleted == deleted)
            c = c.filter(Post.deleted == deleted)
        if month:
            assert isinstance(month, datetime)
            q = q.filter(Post.published >= month, Post.published < month + relativedelta(months=1))
            c = c.filter(Post.published >= month, Post.published < month + relativedelta(months=1))
        count = c.scalar()
        posts = q.order_by(Post.sticky.desc(), Post.published.desc()).all()[(p-1)*num:p*num]
        return posts, count


class Tag(MODEL_BASE):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Tag(%d, '%s')>" % (self.id, self.name)

    @staticmethod
    def query_and_create(tag_names):
        if not tag_names:
            return None
        assert isinstance(tag_names, list)
        db = g.db
        exist_tags = db.query(Tag).filter(Tag.name.in_(tag_names)).all()
        exist_tag_names = [t.name for t in exist_tags]
        new_tags = [Tag(tn) for tn in tag_names if tn not in exist_tag_names]
        g.db.add_all(new_tags)
        return exist_tags + new_tags


class Author(MODEL_BASE):
    __tablename__ = 'author'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False, unique=True)
    password = Column(String(60), nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return "<Author(%d, '%s', '%s')>" % (self.id, self.name, self.password)
