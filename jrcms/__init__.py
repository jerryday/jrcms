from __future__ import unicode_literals

__author__ = 'wangdai'

import os

from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

PACKAGE_DIR = os.path.dirname(__file__)
DB_NAME = 'jrcms.sqlite3'
DB_PATH = PACKAGE_DIR + '/' + DB_NAME
DB_ENGINE_URL = 'sqlite:///' + DB_PATH
DB_ENGINE = create_engine(DB_ENGINE_URL)
MODEL_BASE = declarative_base(bind=DB_ENGINE)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

APP = Flask(__name__)
APP.secret_key = os.urandom(24)
# APP.permanent_session_lifetime = 10
APP.jinja_env.filters['date_format'] = lambda date, format_string='%Y-%m-%d': date.strftime(format_string)

import jrcms.views  # register routes to APP
import jrcms.models  # register models to MODEL_BASE.metadata
from jrcms.utils import Obfuscator

MODEL_BASE.metadata.create_all()
MODEL_BASE.to_dict = lambda self: {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
MODEL_BASE.get = classmethod(lambda cls, obj_id: None if not obj_id else g.db.query(cls).filter_by(id=obj_id).first())
MODEL_BASE.idstr = property(lambda self: Obfuscator.obfuscate(self.id))
