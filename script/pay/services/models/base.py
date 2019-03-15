# -*- coding: utf-8 -*-

from django.forms import ModelForm
from django.db import models
from functools import wraps
from django.db.models import Q
from django.db.models.sql import compiler
from django.db import connection,connections,router
from django.core.cache import cache
from django.core.management.color import no_style
import traceback
from django.db.models import query
import settings
import json
    
    


def close_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:
            c.close()
        except:
            pass
    
class BaseModelMixin(object):
    '''模型的通用方法
    '''
    
    def set_attr(self,name,value,value_handler=None,null=False):
        '''设置模型的属性
        '''
        attr = getattr(self,name)
        if value_handler:
            value = value_handler(value)
        if not null:
            assert  value,'%s 不能为空!' % self.get_verbose_name(name)
        setattr(self,name,value)
    

    def get_verbose_name(self,field_name):
        '''返回模型属性描述
        '''
        for x in  self.__class__.get_fields():
            if field_name == x.name:
                return x.verbose_name
    
    @classmethod
    def get_create_model_sql(cls,replace_table_name=''):
        '''获取创建模型的SQL语句
        @replace_table_name 需要替换的表名
        '''
        sql, _ = connection.creation.sql_create_model(cls, no_style())

        sql = sql[0].replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS').rstrip(';')
        sql = '%s ENGINE=InnoDB ;' % sql
        if replace_table_name:
            sql = sql.replace(cls._meta.db_table,replace_table_name)
        return sql
    
    @classmethod
    def get_db_name(cls):
        return settings.DATABASES.get(cls.objects.db,{}).get('NAME','')
    
    @classmethod
    def get_table_name(cls):
        '''返回模型的表名
        '''
        return cls._meta.db_table

        
    @classmethod
    def get_fields(cls):
        '''返回模型的相关字段定义
        '''
        return cls._meta.fields
    
class JSONField(models.TextField):  
    __metaclass__ = models.SubfieldBase  
    description = "Json"
    
    def __init__(self,*args,**kwargs):
        super(JSONField,self).__init__(*args,**kwargs)
        
    def to_python(self, value):  
        v = super(JSONField,self).to_python(value)  
        if not isinstance(value,basestring):
            return v
        try:  
            _r =  json.loads(v)
        except:  
            _r = {}  
        return _r
    
    def get_prep_value(self, value):  
        try:
            if isinstance(value,basestring):
                json.loads(value)
                _v = value
            else:
                _v = json.dumps(value,ensure_ascii=False)
        except:
            _v =  '{}'
        return _v

class CacheAttribute(object):
    '''计算对象属性,并缓存之
    '''
    def __init__(self,method,name=None):
        self.method = method
        self.name  = name or method.__name__
    
    def __get__(self,inst,cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst,self.name,result)
        return result

class CachedClassAttribute(CacheAttribute):
    '''计算类属性,并在类中缓存之
    '''
    def __get__(self,inst,cls):
        return super(CacheAttribute,self).__get__(cls,cls)
        
    
