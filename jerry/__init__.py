__author__ = 'wangdai'

import os

from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

JERRY_DIR = os.path.dirname(__file__)
DB_PATH = 'sqlite:///%s/jerry.db' % JERRY_DIR
DB_ENGINE = create_engine(DB_PATH)
MODEL_BASE = declarative_base(bind=DB_ENGINE)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

APP = Flask(__name__)
APP.secret_key = os.urandom(24)
# APP.permanent_session_lifetime = 10
APP.jinja_env.filters['date_format'] = lambda date, format_string='%Y-%m-%d': date.strftime(format_string)

import jerry.views  # register routes to APP
import jerry.models  # register models to MODEL_BASE.metadata
from jerry.utils import Obfuscator

MODEL_BASE.metadata.create_all()
MODEL_BASE.to_dict = lambda self: {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
MODEL_BASE.get = classmethod(lambda cls, obj_id: None if not obj_id else g.db.query(cls).filter_by(id=obj_id).first())
MODEL_BASE.idstr = property(lambda self: Obfuscator.obfuscate(self.id))
