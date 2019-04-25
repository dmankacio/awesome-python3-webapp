# !/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Dman'

import re, json, time, logging, hashlib, base64, asyncio

from coroweb import get, post
from models import User, Blog, Comment, next_id

@get('/')
async def index(request):
  users = await User.findAll()
  logging.info('request index... users: %s' % users)
  return {
    '__template__': 'test.html',
    'users': users
  }


