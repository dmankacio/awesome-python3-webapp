#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Dman'
'''
Json API definition
'''
import json, inspect, logging, functools

class Page(object):
    '''
    Page object for display pages.
    '''
    def __init__(self, itemCount, pageIndex=1, pageSize=3):
        self.itemCount = itemCount
        self.pageSize = pageSize
        self.pageCnt = itemCount // pageSize + (1 if itemCount % pageSize > 0 else 0)
        self.pageIndex = pageIndex
        if (itemCount == 0) or (pageIndex > self.pageCnt):
            self.offset = 0
            self.limit = 0
            self.pageIndex = 1
        else:
            self.pageIndex = pageIndex
            self.offset = self.pageSize * (pageIndex - 1)
            self.limit = self.pageSize
        self.hasNext = self.pageIndex < self.pageCnt
        self.hasPre = self.pageIndex > 2
    def __str__(self):
        return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (self.itemCount, self.pageCnt, self.pageIndex, self.pageSize, self.offset, self.limit)
    __repr__ = __str__

class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).
    '''
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.message = message
        self.data = data

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('value:invalid', field, message)

class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''
    def __init__(self, field, message=''):
        super(APIResourceNotFoundError, self).__init__('value:not found', field, message)

class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''
    def __init__(self, field, message=''):
        super(APIPermissionError, self).__init__(self, field, message)



