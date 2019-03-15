# -*- coding: utf-8 -*-

import memcache, threading
import time,datetime
import traceback

from django.core.cache import cache
from util import md5

import functools


class CACHE_TYPE(object):
    CENTER_CACHE = 'CENTER_CACHE_KEYS'
    LOG_CACHE = 'LOG_CACHE_KEYS'
    MENU_CACHE = 'MENU_CACHE_KEYS'

def cache_func(cache_key,func,args=(),timeout=0,cache_type_key=CACHE_TYPE.LOG_CACHE):
    result  = cache.get(cache_key,None)
    result_cache_time_key = '%s_time' % cache_key                                 #设置缓存时间的key
    result_cache_time = ''
    timeout = timeout or 60 * 20
    if result == None:
        result = apply(func,args)
        cache.set(result_cache_time_key,int(time.time()),timeout=timeout) #设置缓存时间
        cache.set(cache_key,result,timeout=timeout)
        cache_keys = cache.get(cache_type_key,set())
        cache_keys.add(result_cache_time_key)
        cache_keys.add(cache_key)
        cache.set(cache_type_key,cache_keys)
    else:
        result_cache_time = cache.get(result_cache_time_key,0)
    return result,result_cache_time



def clear_cache(cache_type_key):
    '''删除缓存
    '''
    cache_keys = cache.get(cache_type_key,set())
    cache_keys.add(cache_type_key)
    if cache_keys:
        cache.delete_many(cache_keys)
    
    
    