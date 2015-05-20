__author__ = 'wangdai'

import functools
import math
from datetime import datetime

import markdown
import htmlmin
from flask import render_template, request, abort, session, redirect, url_for, g, jsonify, send_from_directory
from jinja2.exceptions import TemplateNotFound
from sqlalchemy import func

from jerry import APP, DB_SESSION
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
    p = int(request.args.get('p') or 1)
    tag_id = request.args.get('tag')
    author_id = request.args.get('author')
    month = request.args.get('month')
    if month:
        month = datetime.strptime(month, '%Y-%m')

    tag_name = getattr(Tag.get(tag_id), 'name', None)
    author_name = getattr(Author.get(author_id), 'name', None)
    posts, count = Post.query(p=p, tag_id=tag_id, author_id=author_id, month=month)

    next_url = url_for('index', p=p+1, tag=tag_id, author=author_id, month=month) if p < math.ceil(count / 10) else None
    prev_url = url_for('index', p=p-1, tag=tag_id, author=author_id, month=month) if p > 1 else None

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
    month = {}
    for d in dates:
        date_str = d.published.strftime('%Y-%m')
        if month.get(date_str, None) is None:
            month[date_str] = 1
        else:
            month[date_str] += 1

    tags = db.query(Tag.id, Tag.name, func.count(Tag.id).label('count')).join(PostTag, Tag.id == PostTag.tag_id).group_by(Tag.id)
    return render_template('archive.html', month=month, tags=tags)


@APP.route('/install', methods=['POST'])
def install():
    db = g.db
    if db.query(func.count('*')).select_from(Author).scalar() > 0:
        abort(403)  # forbidden
    author_name = request.form['author_name']
    password = request.form['password']
    if not author_name or not password:
        abort(400)  # bad request
    author = Author(author_name, password)
    db.add(author)
    db.commit()
    return redirect(url_for('manage'))


@APP.route('/<page>', methods=['GET'])
def static_page(page):
    try:
        return render_template(page + '.html')
    except TemplateNotFound as e:
        abort(404)


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
    p = int(request.args.get('p') or 1)
    tag_id = request.args.get('tag')
    deleted = int(request.args.get('deleted') or 0)

    posts, count = Post.query(p=p, tag_id=tag_id, author_id=session['author_id'], deleted=deleted)

    next_url = url_for('manage', p=p+1, tagid=tag_id) if p < math.ceil(count / 10) else ''
    prev_url = url_for('manage', p=p-1, tagid=tag_id) if p > 1 else ''
    return render_template('manage.html', posts=posts, next_url=next_url, prev_url=prev_url, deleted=deleted)


@APP.route('/posts', methods=['POST'])
@login_required
def post_add():
    title = request.form['title'].strip()
    md_content = request.form['markdown'].strip()
    tag_names = request.form.getlist('tags')

    post = Post()
    post.title = title
    post.markdown = md_content
    post.html = htmlmin.minify(markdown.markdown(md_content, extensions=['extra', 'codehilite', 'nl2br', 'toc']))
    post.author_id = session['author_id']
    post.tags = Tag.query_and_create(tag_names)
    post.published = post.modified = datetime.utcnow()

    db = g.db
    db.add(post)
    db.commit()
    return redirect(url_for('manage'))


@APP.route('/posts/<int:post_id>', methods=['POST'])
@login_required
def post_update(post_id):
    title = request.form.get('title')
    md_content = request.form.get('markdown')
    tag_names = request.form.getlist('tags')

    p = Post.get(post_id)
    if title:
        p.title = title.strip()
    if md_content:
        p.markdown = md_content.strip()
        p.html = htmlmin.minify(markdown.markdown(md_content, extensions=['extra', 'codehilite', 'nl2br', 'toc']))
    if tag_names:
        p.tags = Tag.query_and_create(tag_names)

    db = g.db
    if db.dirty:
        db.commit()
    return redirect(url_for('manage'))


@APP.route('/posts/<int:post_id>', methods=['PUT'])
@login_required
def post_delete_or_stick(post_id):
    db = g.db
    rows = db.query(Post).filter_by(id=post_id).update({request.form['column']: int(request.form['value'])})
    db.commit()
    return jsonify(dict(rows_affected=rows))


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