__author__ = 'wangdai'

import os
import configparser

from flask import Flask
import jinja2

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


JERRY_DIR = os.path.dirname(__file__)
CONFIG = configparser.ConfigParser()
CONFIG.read(JERRY_DIR + '/config.ini')

APP = Flask(__name__)
APP.secret_key = os.urandom(24)

if CONFIG['database']['backend'].startswith('sqlite'):
    DB_PATH = 'sqlite:///' + CONFIG['database']['database']
else:
    # oops! dirty code
    DB_PATH = '%s://%s:%s@%s:%d/%s' % (CONFIG['database']['backend'],
                                       CONFIG['database']['user'], CONFIG['database']['password'],
                                       CONFIG['database']['host'], int(CONFIG['database']['port']),
                                       CONFIG['database']['database'])

DB_ENGINE = create_engine(DB_PATH, echo=True)
MODEL_BASE = declarative_base(bind=DB_ENGINE)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

POSTS_DIR = JERRY_DIR + '/posts'

MY_LOADER = jinja2.ChoiceLoader([
    APP.jinja_loader,
    jinja2.FileSystemLoader([POSTS_DIR + '/html'])
])
APP.jinja_loader = MY_LOADER
def date_format(date, format_string='%Y-%m-%d'):
    return date.strftime(format_string)
APP.jinja_env.filters['date_format'] = date_format

import jerry.views  # register routes to APP
import jerry.models  # register models to MODEL_BASE.metadata


MODEL_BASE.metadata.create_all()


def to_dict(self):
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

MODEL_BASE.to_dict = to_dict