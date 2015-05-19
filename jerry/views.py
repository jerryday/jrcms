__author__ = 'wangdai'

import time
import hashlib
import datetime
import string
import functools
import math
from pprint import pprint
from dateutil.relativedelta import relativedelta

import markdown
import htmlmin

from flask import render_template, request, abort, session, redirect, url_for, g, jsonify, send_from_directory

from sqlalchemy import func

from jerry import APP, DB_SESSION, POSTS_DIR
from jerry.models import Post, Author, Tag, PostTag


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


def template(tpl=None):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = tpl
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator


###############
# reader's view
###############

@APP.route('/')
def index():
    db = g.db

    p = int(request.args.get('p') or 1)
    tag_id = request.args.get('tag')
    author_id = request.args.get('author')
    month = request.args.get('month')
    tag_name = None
    author_name = None

    query = db.query(Post)
    if tag_id:
        tag_id = int(tag_id)
        tag_name = db.query(Tag.name).filter_by(id=tag_id).first()
        tag_name = tag_name[0] if tag_name else None
        query = query.join(PostTag, Post.id == PostTag.post_id).filter(PostTag.tag_id == tag_id)
    if author_id:
        author_id = int(author_id)
        author_name = db.query(Author.name).filter_by(id=author_id).first()
        author_name = author_name[0] if author_name else None
        query = query.filter(Post.author_id == author_id)
    if month:
        month = datetime.datetime.strptime(month, '%Y-%m')
        query = query.filter(Post.published >= month, Post.published < month + relativedelta(months=1))
    posts = query.filter(Post.status == 'normal').all()[10*(p-1):10*p]

    next_url = url_for('index', tag=tag_id, author=author_id, month=month, p=p+1) if len(posts) == 10 else None
    prev_url = url_for('index', tag=tag_id, author=author_id, month=month, p=p-1) if p > 1 else None

    context = dict(
        posts=posts,
        tag_name=tag_name,
        author_name=author_name,
        month=month,
        next_url=next_url,
        prev_url=prev_url,
        p=p,
    )
    return render_template('index.html', **context)


@APP.route('/posts/<post_id>', methods=['GET'])
def post_get(post_id):
    db = g.db
    post = db.query(Post).filter_by(id=post_id).first()
    return render_template('post.html', post=post)


@APP.route('/archive')
def archive():
    db = g.db
    dates = db.query(Post.published).all()
    hist = {}
    for d in dates:
        date_str = d.published.strftime('%Y-%m')
        if hist.get(date_str, None) is None:
            hist[date_str] = 1
        else:
            hist[date_str] += 1

    tags = db.query(Tag.id, Tag.name, func.count(Tag.id).label('count')).join(PostTag, Tag.id == PostTag.tag_id).group_by(Tag.id)
    return render_template('archive.html', tags=tags)

@APP.route('/install', methods=['POST'])
def install():
    db = g.db
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


@APP.route('/static/<path:path>')
def send(path):
    return send_from_directory('static', path)


@APP.before_request
def before_request():
    g.db = DB_SESSION()


@APP.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()