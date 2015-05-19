__author__ = 'wangdai'

import time
import hashlib
import datetime
import string
import functools
import math
from pprint import pprint

import markdown
import htmlmin

from flask import render_template, request, abort, session, redirect, url_for, g, jsonify

from sqlalchemy import func

from jerry import APP, DB_SESSION, POSTS_DIR
from jerry.models import Post, Author, Tag


###########################
# decorators for controller
###########################

def login_required(function):
    @functools.wraps(function)
    def decorated_function(*args, **kwargs):
        if 'author_id' not in session:
            return redirect(url_for('login', next=request.url))
        return function(*args, **kwargs)
    return decorated_function


###############
# reader's view
###############

@APP.route('/')
def index():
    db = DB_SESSION()
    start = int(request.args.get('start', 0))
    num = int(request.args.get('num', 10))
    post_metas = db.query(Post).order_by(Post.published.desc()).all()[start:start+num]
    for meta in post_metas:
        print(meta.title)
    return str(start)


@APP.route('/posts/<post_id>', methods=['GET'])
def post_get(post_alias):
    db = DB_SESSION()
    post = db.query(Post).filter_by(alias=post_alias).first()
    return render_template('post.html', post=post)


@APP.route('/install', methods=['POST'])
def install():
    db = DB_SESSION()
    if db.query(Author).all().count() > 0:
        abort(403)  # forbidden
    author_name = request.form['author_name']
    password = request.form['password']
    if not author_name or not password:
        abort(400)  # bad request
    author = Author(author_name, password)
    db.add(author)
    db.commit()


##############
# admin routes
##############

@APP.route('/login', methods=['GET'])
def login_page():
    action = url_for('login')
    if request.args.get('next'):
        action = url_for('login', next=request.args.get('next'))
    return render_template('login.html', action=action)


@APP.route('/login', methods=['POST'])
def login():
    db = g.db
    redirect_url = request.args.get('next') or url_for('manage')
    author_name = request.form['author_name']
    password = request.form['password']
    author = db.query(Author).filter_by(name=author_name).first()
    if not author or author.password != password:
        return redirect('login')
    session['author_id'] = author.id
    session['author_name'] = author.name
    return redirect(redirect_url)


@APP.route('/edit', methods=['GET'])
@login_required
def edit_new():
    return render_template('edit.html', post=None, action=url_for('post_add'), method='POST')


@APP.route('/edit/<int:post_id>', methods=['GET'])
@login_required
def edit_one(post_id):
    db = g.db
    post = db.query(Post).filter_by(id=post_id).one()
    return render_template('edit.html', post=post, action=url_for('post_update', post_id=post_id), method='PUT')


@APP.route('/manage', methods=['GET'])
@login_required
def manage():
    db = g.db
    start = int(request.args.get('start') or 0)
    num = int(request.args.get('num') or 10)
    tag_id = request.args.get('tagid')
    post_count = db.query(func.count('*')).select_from(Post).scalar()
    posts = db.query(Post)[start:num]
    next_url = url_for('manage', start=start+num, tagid=tag_id) if start+num < post_count else ''
    prev_url = url_for('manage', start=start-num, tagid=tag_id) if start-num >= 0 else ''
    return render_template('manage.html', posts=posts, next_url=next_url, prev_url=prev_url)


@APP.route('/posts', methods=['POST'])
@login_required
def post_add():
    db = g.db
    post = Post()
    post.title = request.form['title'].strip()
    post.markdown = request.form['markdown'].strip()
    post.html = htmlmin.minify(markdown.markdown(post.markdown, extensions=['extra', 'codehilite', 'nl2br', 'toc']))
    post.author_id = session['author_id']
    tag_ids = [int(k[4:]) for k in request.form.keys() if k.startswith('tag-')]
    post.tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    db.add(post)
    db.commit()
    return redirect(url_for('manage'))


@APP.route('/posts/<int:post_id>', methods=['POST'])
@login_required
def post_update(post_id):
    db = g.db
    title = request.form['title'].strip()
    md_content = request.form['markdown'].strip()
    tag_ids = [int(k[4:]) for k in request.form.keys() if k.startswith('tag-')]
    post = db.query(Post).filter_by(id=post_id).one()
    if post.title != title:
        post.title = title
    if post.markdown != md_content:
        post.markdown = md_content
        post.html = htmlmin.minify(markdown.markdown(post.markdown, extensions=['extra', 'codehilite', 'nl2br', 'toc']))
    tag_equal = len(tag_ids) == len(post.tags)
    if tag_equal:
        for tag in post.tags:
            if tag.id not in tag_ids:
                tag_equal = False
                break
    if not tag_equal:
        post.tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    if db.dirty:
        post.modified = datetime.datetime.utcnow()
    db.commit()
    return redirect(url_for('manage'))


@APP.route('/tags', methods=['POST'])
@login_required
def tag_add():
    db = g.db
    tag_name = request.form['tag_name']
    tag = db.query(Tag).filter_by(name=tag_name).first()
    if tag:
        return jsonify(tag.to_dict())
    tag = Tag(tag_name)
    db.add(tag)
    db.commit()
    return jsonify(tag.to_dict())


@APP.route('/test', methods=['GET', 'POST'])
def test():
    print(request.path)
    print(request.url)
    for k in request.form.keys():
        print(k)
    return jsonify(request.get_json() or '')


@APP.route('/pages/<page_name>')
def view_page(page_name):
    return render_template('%s.html' % page_name)


@APP.before_request
def before_request():
    g.db = DB_SESSION()


@APP.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()