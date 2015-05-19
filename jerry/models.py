__author__ = 'wangdai'

from datetime import datetime
from jerry import MODEL_BASE
from sqlalchemy import Column, ForeignKey, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import Integer, String, Text, DateTime, Boolean


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
    status = Column(String(10), nullable=False, default='normal')

    author = relationship('Author', backref='posts')
    tags = relationship('Tag', secondary=PostTag.__table__, backref='posts')


class Tag(MODEL_BASE):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False, unique=True)

    def __init__(self, name):
        self.name = name


class Author(MODEL_BASE):
    __tablename__ = 'author'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False, unique=True)
    password = Column(String(60), nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password

