# -*- coding: utf-8 -*-
#
#系统 :管理员,权限,角色相关模型
#
#
from django.db import models
from .resource import Resource
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)
import time,datetime,urllib
import traceback
from settings import get_app_label



class Menu(models.Model,BaseModelMixin):
    '''菜单模型
    '''

    parent_id = models.IntegerField('父节点id',default=0)
    name = models.CharField('名称',max_length=50,db_index=True,unique=True)
    url = models.CharField('访问地址带参数',max_length=400,blank=True,default='')
    url_path = models.CharField('访问路径',max_length=100,null=False,db_index=True)
    icon = models.CharField('图标',max_length=100,null=True,blank=True,default='')
    css = models.CharField("样式",max_length=100,null=True,blank=True,default='')
    order = models.IntegerField('排序',default=0)
    is_show = models.IntegerField('显示',default=1)
    is_log = models.IntegerField('记录日志',default=0)

    #objects = CacheManager
    
    def __unicode__(self):
        return '%s' % self.name

    @classmethod
    def url_decode(cls,url_params):
        '''URL参数返回一个字典
        '''
        params = {}
        for o in url_params.split('&'):
            if '=' in o:
                kv = o.split('=')
                if len(kv)!=2:
                    continue
                k,v = kv
                params[k] = urllib.unquote_plus(v.encode('utf-8')).decode('utf-8')
        return params

    def get_url_params(self):
        '''返回url的参数字典
        '''
        url_params = self.url.split('?',2)
        if len(url_params)==2:
            return Menu.url_decode(url_params[1])
        return {}

    def is_match_url_parmas(self,menu_parmas):
        return self._is_dict_issubset(self.get_url_params(),menu_parmas)

    def _is_dict_issubset(self,dict1,dict2):
        set1 = set(dict1.items())
        set2 = set(dict2.items())
        return set1.issubset(set2)

    def save(self,*arge,**kwargs):
        self.url_path = self.url.split('?',2)[0]
        if not self.is_show:
            self.css += 'color:gray;'
        super(Menu,self).save(*arge,**kwargs)
    
    class Meta:
        db_table = u'menu_new'
        ordering = ('order',)
        app_label = get_app_label()

class UserDefinedMenu(models.Model):
    ''' 用户自定义菜单模型 '''
    admin_id = models.IntegerField(max_length=8)
    defined_menu = models.TextField(u"用户定义的菜单项", max_length=1000)
    map_menu = models.TextField(u"系统菜单的映射", max_length=1000)
    update_time = models.DateTimeField()

    def __unicode__(self):
        return self.id

    class Meta:
        db_table = u"custom_menu"
        app_label = "analys"

Resource.register('menu',Menu)


