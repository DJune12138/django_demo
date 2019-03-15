# -*- coding: utf-8 -*-
#
#资源 相关模型
#
#
from django.db import models
import hashlib
import traceback
from settings import get_app_label

import time,datetime,urllib
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)

    
class ResourceConvert(object):
    '''资源id 转为16进存储
    '''
    @staticmethod
    def ids2hex(id_list):
        hex_str = ''
        try:
            if not id_list:return hex_str
            n_l = [ int(x) for x in id_list]
            bins = []
            for n in xrange(max(n_l)):
                bins.append( '1' if n+1 in n_l else '0' )
            if bins:
                hex_str = hex(int(''.join(bins)[::-1],2)).rstrip('L')
        except Exception,e:
            traceback.print_exc()
        finally:
            return hex_str
        
    @staticmethod
    def hex2ids(hex_str):
        id_list = set()
        try:
            if not hex_str:return id_list
            for i,b in enumerate(bin(int(hex_str,16))[2:][::-1]):
                if b == '1':
                    id_list.add(i+1)
        except Exception,e:
            traceback.print_exc()
        finally:
            return id_list
        
class Resource(models.Model,BaseModelMixin):
    '''资源
    '''
    resource_map = {} #{"server":Server,"channel":Channel,"agent":Agent,"server_group":Group}
    
    name = models.CharField("资源名",max_length=20,null=False,blank=True,db_index=True)
    role_id = models.IntegerField('角色id')
    _members = models.TextField('对象id二进制16进')
    __members_cache = None

    def add_member(self,id_or_ids):
        if not isinstance(id,list):
            id_or_ids = [ id_or_ids ]
        id_or_ids =set(id_or_ids)
        new_ids = self.members
        new_ids |= id_or_ids
        self.members = new_ids
    
     
    @property
    def members(self):
        '''将16进数据返回id列表
        '''
        if  self.__members_cache is None:
            self.__members_cache = ResourceConvert.hex2ids(self._members) 
        return self.__members_cache
    
    @members.setter
    def members(self,id_list):
        assert isinstance(id_list,(list,set)),'the value must list or set!'
        self._members = ResourceConvert.ids2hex(id_list)

    
    def __or__(self, other):
        '''与位
        @other为资源对象或者资源的成员set表
        '''
        if isinstance(other,Resource):
            return self.members.union(other.members)
        return self.members.union(other)
        
    @classmethod  
    def register(cls,modle_name,model_cls):
        '''注册资源
        @模型名
        @模型
        '''
        if isinstance(model_cls,models.base.ModelBase):
            if modle_name not in cls.resource_map.keys():
                cls.resource_map[modle_name] = model_cls
            
    class Meta:
        db_table = u'resource'
        app_label = get_app_label()
     


