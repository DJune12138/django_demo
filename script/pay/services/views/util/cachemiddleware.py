# -*- coding: utf-8 -*-
#缓存中间键

from __future__ import unicode_literals
import datetime
import hashlib
try:
    from settings import CACHE_MIDDLEWARE_SECONDS
    DEFAULT_CACAE_TIME = CACHE_MIDDLEWARE_SECONDS
except:
    DEFAULT_CACAE_TIME = 60 * 30

if __name__ == '__main__':
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] ='settings'
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)


from django.db.backends import BaseDatabaseWrapper
from django.core.cache import cache
import traceback
import re
from functools import wraps

from threading import local
import time 
from django.utils.encoding import force_text
from django.utils import six
from django.db import connection
import settings
#from MySQLdb import cursors
try:
    import sqlparse
except:
    pass
_DEBUG = settings.DEBUG
_DEBUG = False

class SQLQueryTriggered(Exception):pass

class ThreadLocalState(local):
    def __init__(self):
        self.enabled = True
        
    @property
    def Wrapper(self):
        if self.enabled:
            return CacheCursorWrapper
        return ExceptionCursorWrapper

    def recording(self, v):
        self.enabled = v


state = ThreadLocalState()
recording = state.recording  


def CursorWrapper(*args, **kwds):  
    return state.Wrapper(*args, **kwds)

def md5(_str):
    return hashlib.new('md5',_str).hexdigest()

class ExceptionCursorWrapper(object):
    def __init__(self, cursor, db, logger):
        pass

    def __getattr__(self, attr):
        raise SQLQueryTriggered()



class MysqlCache(object):
    '''mysql  按表缓存
    '''
    
    IGNORE_TABLES = set(['log_operate','question','pay_action','card'])
    def __init__(self,cursorwrapper):
        self.cursorwrapper = cursorwrapper
        self.reset_attr()
        
    def reset_attr(self):
        '''重置属性
        '''
        self.sql = ''
        self.params = None
        self.action = ''
        self.sql_key = ''
        self.sql_md5_key = ''
        self.table_name_list = []
        self.table_keys = []
        self.is_use = False
        self.is_clear = False
        self.is_executed = False
        
    def set_sql(self,sql,params=None):
        self.reset_attr()
        self.sql = sql
        self.params = params
        if params != None:
            self.sql_key = self.sql + str(params)
        self.sql_md5_key = md5('%s_%s' % (self.cursorwrapper.db_name,self.sql_key))
        self.sql_analys()

    def sql_analys(self):
        sql_analys = [ str(x) for x in self.sql.lower().split() if x]
        self.action = sql_analys[0]
        
        table_name_list = []
        
        if self.action == 'insert' or self.action == 'replace':
            table_name_list.append( sql_analys[2] )
            self.is_clear = True
        elif self.action == 'delete':
            self.is_clear = True
            table_name_list.append( sql_analys[ sql_analys.index('from') + 1] )
        elif self.action == 'update':
            self.is_clear = True
            table_name_list.append( sql_analys[1] )
        elif self.action == 'select':
            self.is_use = True
            table_name_list.append( sql_analys[ sql_analys.index('from') + 1] )
            if 'join' in sql_analys :
                table_name_list.append(sql_analys[ sql_analys.index('join') + 1] )
        else:
            table_name_list = ['']
            
        if len(table_name_list) >=1 :
            table_name_list = [ x.strip('`') for x in table_name_list]
        
        self.table_name_list = table_name_list
        self.table_keys = [ 'table_%s_key' % x for x in table_name_list]
        
        # 忽略的表和有特殊字符的表名不使用缓存
        if len(set(table_name_list) & self.IGNORE_TABLES)>0 or filter(lambda x :re.search('\W',x),table_name_list):
            self.is_use = self.is_clear = False
        if self.is_clear:
            self.clear_cache()
        
        self.is_use = getattr(self.cursorwrapper.cursor,'use_cache',self.is_use)
    def clear_cache(self):
        '''清除查询缓存
        '''
        for key in self.table_keys:
            cache_keys = self.get_table_cache_keys(key)
            cache_keys.add(key)
            if _DEBUG:
                print 'clear cache'
                print cache_keys
            cache.delete_many(cache_keys)
    
    def save_cache(self,data,cache_key=''):
        '''保存缓存
        '''
        cache_key = cache_key or self.sql_md5_key
        cache.set(cache_key,data,DEFAULT_CACAE_TIME)
        for key in self.table_keys:
            table_cache_keys = self.get_table_cache_keys(key)
            table_cache_keys.add(cache_key)
            cache.set(key,table_cache_keys,DEFAULT_CACAE_TIME) #这个表所有的查询
        
    
    def debug_info(self,cache_key,use_cache):
        msg =  ['=' * 40]
        msg.append( 'use cache    : %s' % use_cache )
        msg.append( 'the_cache_key: %s' % cache_key )
        msg.append( 'the_table_key: %s' % self.table_name_list)
        msg.append( 'the_sql      : %s' % self.get_sql() )
        msg.append( '=' * 40 )
        return '\n'.join(msg)
    
    def get_mysql_cache_data(self,method,args=(),other_key=''): 
        if self.is_use:
            cache_key = '%s_%s' % (self.sql_md5_key , other_key)
            _r = cache.get(cache_key,None)
            if _DEBUG:
                print self.debug_info(cache_key, _r != None)
            if  _r == None :
                if not self.is_executed:
                    self._execute()
                _r = apply(method,args)
                self.save_cache(_r,cache_key)
            return _r
        else:
            return apply(method,args)
    
    def get_sql(self):
        if self.params :
            return self.sql % tuple(self.params)
        return self.sql
    
    def get_table_cache_keys(self,key_name):
        return cache.get(key_name,set())
    
    def execute(self,sql,params):
        self.set_sql(sql, params)
        if not self.is_use:  #不是用缓存的直接执行
            return self._execute()
    
    def _execute(self):
        self.is_executed = True
        return self.cursorwrapper.cursor.execute(self.sql,self.params)
        
    
class CacheCursorWrapper(object):

    def __init__(self, cursor, db, logger):
        self.cursor = cursor
        self.db = db
        self.logger = logger
        self.use_cache = False
        self.db_name = self.db.settings_dict.get('NAME')
        self.count = 0
        self.m_c = MysqlCache(self)
        
    def _quote_expr(self, element):
        if isinstance(element, six.string_types):
            return "'%s'" % force_text(element).replace("'", "''")
        else:
            return repr(element)

    def _quote_params(self, params):
        if not params:
            return params
        if isinstance(params, dict):
            return dict((key, self._quote_expr(value))
                        for key, value in params.items())
        return list(map(self._quote_expr, params))
    
    def _decode(self, param):
        try:
            return force_text(param, strings_only=True)
        except UnicodeDecodeError:
            return '(encoded string)'
        
    def fetchmany(self, size=None):
        self.count += 1
        return self.m_c.get_mysql_cache_data(self.cursor.fetchmany,args=(size,),other_key=self.count)
    
    def fetchall(self):
        return self.m_c.get_mysql_cache_data(self.cursor.fetchall)
        
    def fetchone(self):
        self.count += 1
        return self.m_c.get_mysql_cache_data(self.cursor.fetchone,other_key=self.count)
            
    def execute(self, sql, params=()):
        _r = self.m_c.execute(sql, params)
        if not self.m_c.is_executed :#伪造已经执行过
            execute_sql = sql % tuple(self._quote_params(params))
            setattr(self.cursor,'_executed',execute_sql)       
            setattr(self.cursor,'_last_executed',execute_sql)  
        return _r
#        start_time = time.time()
#        try:
#            return self.m_c.execute(sql, params)
#        finally:
#            try:
#                stop_time = time.time()
#                alias = getattr(self.db, 'alias', 'default')
#                conn = self.db.connection
#                if conn:
#                    engine = conn.__class__.__module__.split('.', 1)[0]
#                else:
#                    engine = 'unknown'
#                
#                params = {
#                    'engine': engine,
#                    'alias': alias,
#                    'sql': self.db.ops.last_executed_query(
#                        self.cursor, sql, self._quote_params(params)),
#                    'start_time': start_time,
#                    'stop_time': stop_time,
#                    'use_cache': self.use_cache
#                }
#                #print params
#                #self.logger.info('alias:%s', alias)
#                #self.logger.info('sql:%s', sql)
#                #self.logger.info('execute sql used:', stop_time - start_time)
#            except Exception, ex:
#                traceback.print_exc()

    def executemany(self, sql, param_list):
        self.m_c.set_sql(sql, param_list) 
        return self.cursor.executemany(sql, param_list)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)
    
    def __get_result(self,size=100):
        while True:
                result = self.fetchmany(size)
                if not result:
                    break
                for line in result:
                    yield line
    
    def __iter__(self):
        self.m_c._execute()             #使用迭代器必须执行一下
        return iter(self.__get_result())



def replace_method(klass, method_name):
    original = getattr(klass, method_name)
    def inner(callback):
        def wrapped(*args, **kwargs):
            return callback(original, *args, **kwargs)
        actual = getattr(original, '__wrapped__', original)
        wrapped.__wrapped__ = actual
        wrapped.__doc__ = getattr(actual, '__doc__', None)
        wrapped.__name__ = actual.__name__
        setattr(klass, method_name, wrapped)
        return wrapped
    return inner

from util.log import Logger
_log = Logger('cache')

@replace_method(BaseDatabaseWrapper, 'cursor')
def cursor(original, self):
    result = original(self)
    return CursorWrapper(result, self, _log)

class CacheMiddleware(object):pass
        
#self.cursorclass = kwargs2.pop('cursorclass', self.default_cursor)

