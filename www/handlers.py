# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Dman'

import re, json, time, logging, hashlib, base64, asyncio

from coroweb import get, post
from models import User, Blog, Comment, next_id

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


