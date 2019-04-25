# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Dman'

import re, json, time, logging, hashlib, base64, asyncio

from coroweb import get, post
from models import User, Blog, Comment, next_id

@get('/test')
async def test(request):
    users = await User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }

@get('/')
async def index(request):
  summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
  blogs = [
    Blog(id='1', name='Test Blog', summary=summary, created_at=time.time() - 120),
    Blog(id='2', name='Something New', summary=summary, created_at=time.time() - 3600),
    Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time() - 7200)
  ]
  logging.info('request index... blogs: %s' % blogs)
  return {
    '__template__': 'index.html',
    'blogs': blogs
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