# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Dman'

import re, json, time, logging, hashlib, base64, asyncio
from aiohttp import web

from www.coroweb import get, post
from www.models import User, Blog, Comment, next_id
from www.apis import *
from www.config import configs
import markdown2

COOKIE_NAME = 'dk_apw_auth'
_COOKIE_KEY = configs.session.secret

async def checkAdmin(u):
    if u is None or u.amdin <= 0:
        raise APIPermissionError()

def text2html(text):
    list = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strp() != '',), text.split('\n'))
    return ''.join(list)

async def cookie2user(cookieStr):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookieStr:
        return None
    try:
        L = cookieStr.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid user: %s ' % user.email)
            return None
        user.passwd = '******'
        return user
    except Exception as ex:
        logging.exception(ex)
        return None


@get('/test')
async def test(request):
    users = await User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }

@get('/')
async def index(*, page='1'):
    pageIndex = get_page_index(page)
    total = await Blog.findNumber('count(0)')
    p = Page(total, pageIndex)
    if total > 0:
        blogs = await Blog.findAll(orderBb='created_at desc', limit=(p.offset, p.limit))
    else:
        blogs = []
    logging.info('request index... blogs: %s, page:%s' % (blogs,p))
    return {
        '__template__': 'index.html',
        'blogs': blogs,
        'page':p
    }

@get('/api/users')
async def api_get_user(*, page='1'):
    pageIndex = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = getPage(num, pageIndex, 10)
    if num <= 0:
        return dict(page=p, users=())
    #users = User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    users = await User.findAll(orderBy='created_at desc')
    logging.info(' api/users.. users: %s' % users)
    for u in users:
        u.password = '******'
    return dict(page=p, users=users)

def get_page_index(num):
    try:
        return int(num)
    except ValueError:
        result = []
        for c in num:
            if not ('0' <= c <= '9'):
                break
            result.append(c)
        if len(result) == 0:
            return 0
        return int(''.join(result))

def getPage(num, pageIndex, pageSize):
    if pageIndex <= 1:
        pageIndex = 1
    totalPageNum = (num + pageSize - 1) / pageSize
    if pageIndex > totalPageNum:
        pageIndex = totalPageNum
    offset = (pageIndex - 1) * pageSize
    return dict(offset=offset, limit=pageSize)

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')
_COOKIE_KEY = 'yt89j465s4fqw'

@get('/register')
async def user_register(request):
    return {
        '__template__': 'register.html',
    }

@get('/signin')
async def user_signin(request):
    return {
        '__template__': 'signin.html',
    }

@post('/api/auth')
async def auth(*, email, passwd):
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError(field='email',  message='Invalid email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError(field='passwd',  message='Invalid password')
    users = await User.findAll('email=?', [email])
    if len(users) <= 0:
        raise APIValueError(field='email',  message='Email not exist.')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError(field='passwd',  message='Invalid password')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/signout')
async def signout(request):
    cookieStr = request.cookies.get(COOKIE_NAME)
    uemail = ''
    if cookieStr:
        user = await cookie2user(cookieStr)
        uemail = user.email
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user logout: %s' % uemail)
    return r

# 计算加密cookie:
def user2cookie(user, max_age):
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

@post('/api/user/register')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError(field='name', message='invalid name')
    if not email or not name.strip() or not _RE_EMAIL.match(email):
        raise APIValueError(field='email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError(field='passwd')
    usersCnt = await User.findNumber('count(0)', where='email=?', args=[email])
    if usersCnt > 0:
        raise APIError('register failed', 'email', 'email is already used.')
    uid = next_id()
    sha1Pwd = '%s:%s' % (uid, passwd)
    user = User(id = uid, name = name.strip(), email = email, passwd = hashlib.sha1(sha1Pwd.encode('utf-8')).hexdigest(),
                image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest() )
    rows = await user.save()
    if rows < 1:
        logging.error(' 用户注册失败.. user: %s' % user)
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/blog/{id}')
async def blog_get(id):
    blog = await Blog.find(id)
    comments = await Comment.findAll('blog_id=?', [id])
    for c in comments:
        c.html_content = text2html(c.content)
    if blog:
        blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog_dtl.html',
        'blog': blog,
        'comments': comments
    }

@get('/manage/')
def manage():
    return 'redirect:/manage/comments'

@get('/manage/comments')
def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'pageIndex': get_page_index(page)
    }

@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'blogs.html',
        'page_index': get_page_index(page)
    }

@get('/manage/blog/create')
def blog_edit(request):
    return {
        '__template__': 'manage_blog_edit.html',
        'action': '/api/blog/edit'
    }

@get('/manage/users')
def user_list(*, page='1'):
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }

@get('/api/comments/')
async def api_comments(*, page='1'):
    pageIndex = get_page_index(page)
    num = await Comment.findNumber('count(0)')
    p = Page(num, pageIndex)
    if num <= 0:
        return dict(page=p, comments=())
    list = await Comment.findAll(orderBy='created_ad desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=list)

@post('/api/blog/{id}/comments')
async def api_comments_create(id, request, *, content):
    user = request.curUser
    if user is None:
        raise APIPermissionError(message='please signin first')
    blog = Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError(field='Blog', message='blog is not found')
    if not content or not content.strip():
        raise APIValueError(field='content', message='content is not empty')
    newCmt = Comment(blog_id=id, user_id=user.id, user_name=user.name, user_image=user.image, content=content)
    await newCmt.save()
    return newCmt

@post('/api/comment/{id}/delete')
async def api_comments_delete(id, request):
    checkAdmin(request)
    comment = await Comment.find(id)
    if not comment:
        raise APIResourceNotFoundError('comment')
    comment.remove()
    return dict(id=id)


@get('/api/blog/{id}')
async def api_blog_get(request, *, id):
    if not id or not id.strip():
        raise APIValueError(field='id',  message='ID不能为空.')
    u = request.curUser
    blog = await Blog.find(id)

    return blog



@get('/api/blogs')
async def api_blog_list(*, page='1'):
    pageIndex = get_page_index(page)
    num = await Blog.findNumber('count(0)')
    p = Page(num, pageIndex)
    if(num <= 0):
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

@post('/api/blog/edit')
async def api_blog_edit(request, *, name, summary, content, id=None):
    #checkAdmin(request)
    if not name or not name.strip():
        raise APIValueError(field='name', message='name is empty.')
    if not summary or not summary.strip():
        raise APIValueError(field='summary',  message='摘要不能为空.')
    if not content or not content.strip():
        raise APIValueError(field='content',  message='正文不能为空.')
    u = request.curUser
    #id = None
    if id:
        blog = await Blog.find(id)
        if blog:
            blog.name=name.strip()
            blog.summary=summary.strip()
            blog.content=content.strip()
            await blog.save()
            return blog
        raise APIResourceNotFoundError(field='Blog',  message='找不到对应日志。')
    else:
        newBlog = Blog(id=next_id(), user_id=u.id, user_name=u.name, user_image=u.image, name=name.strip(), summary=summary.strip(), content=content.strip())
        await newBlog.save()
        return newBlog

@post('/api/blog/{id}/delete')
async def api_blog_get(request, *, id):
    if not id or not id.strip():
        raise APIValueError(field='id',  message='ID不能为空.')
    u = request.curUser
    checkAdmin(u)
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    blog.remove()
    return 1