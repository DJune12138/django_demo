# -*- coding: utf-8 -*-
#
#角色相关模型
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
     
     
class RoleManagerMixin(object):
    
    
    def add_resource_member(self,name,id):
        '''增加资源对象
        @name  资源名
        @id    资源对象id
        '''
        resource_objs = self.resource.all().filter(name=name)
        if resource_objs:
            resource_objs[0].add_member(id)
            resource_objs[0].save()
        
    def get_resource(self,name):
        resource_ids = self.resource.get(name=name).members
        return Resource.resource_map[name].objects.filter(id__in=resource_ids).distinct()   
    
    
    def create_resource(self,name,id_list):
        '''角色创建资源
        @资源名
        @id列表
        '''
        if not self.id:#新建时没有对象,先保存一下
            self.save()
        resource,created = Resource.objects.get_or_create(name = name,role_id=self.id)
        resource.members = id_list
        resource.save()
        self.resource.add(resource)
            
        
class Role(models.Model,BaseModelMixin,RoleManagerMixin):
    '''角色模型
    '''
    
    class RoleType:
        ADMIN =   0   #管理员
        NORMAL =  1   #普通账号
    
    TYPE_CHOICES = ((RoleType.NORMAL,'普通'),(RoleType.ADMIN,'管理员'))
    
    name = models.CharField('角色名',max_length=50,unique=True,db_index=True)
    parent_name = models.CharField('主管名',max_length=50,default='',db_index=True)
    resource = models.ManyToManyField(Resource,verbose_name='资源对象') 
    type = models.IntegerField('角色类型',default=1, choices=TYPE_CHOICES)
    remark = models.CharField('角色描述',default='',max_length=1000)
    
    @CacheAttribute
    def resource_ids(self):
        _r = {}
        for r in self.resource.all():
            _r[r.name] = r.members
        return _r
    
    @property
    def is_manager(self):
        return self.type == self.RoleType.ADMIN
    
    
    def save(self,*args,**kwargs):
        super(Role,self).save(*args,**kwargs)    
        
    def delete(self,*args,**kwargs):
        for r in self.resource.all():
            r.delete()
        self.resource.clear()
        super(Role,self).delete(*args,**kwargs)
   
    def __unicode__(self):
        return '%s' % self.name
   
    class Meta:
        db_table = u'role_new'
        app_label = get_app_label()


Resource.register('role',Role)

