# -*- coding: utf-8 -*-
#
#系统 :管理员 相关模型
#
#

from settings import get_app_label  
from django.db import models
from django.db.models import Q
import hashlib
from .resource import Resource
from .role import Role
from .menu import Menu
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)

import time,datetime,urllib
import traceback
from django.db.models import Q 

class ResourceProxy(object):
    '''资源代理,为了在模版里可以使用request.admin.resource.xxx
    '''
    def __init__(self,admin_obj):
        self.admin_obj = admin_obj       
    
    def __getattr__(self,name):
        if name != 'admin_obj':
                return self.admin_obj.get_resource(name)
        else:
            return super(ResourceProxy,self).__getattr__(name)
        

        
class AdminManagerMixin(object):
    '''用户管理者,扩展admin模型的方法
    '''      
    
    def __init__(self,*args,**kwargs):
        self.resource = ResourceProxy(self)
        super(AdminManagerMixin,self).__init__(*args,**kwargs)
        self.__resource_map = {}
        self.__cache_roles = None
        
    @classmethod
    def get_admin(cls,admin_id):
        '''获取管理员
        '''
        admin_objs =  cls.objects.filter(id=admin_id,status=cls.Status.NORMAL).prefetch_related('role')
        if admin_objs:
            return admin_objs[0]
 
 
    def get_manageable_admin(self):
        '''获取自己的下属
        '''
        return Admin.objects.filter(role__in=self.get_resource('role')).prefetch_related('role').distinct()    
    
    @CacheAttribute
    def is_root(self):
        '''是否超级管理员
        '''
        for r in self.get_roles():
            if r.name == '系统管理员':
                return True
        return False

    @property
    def is_agent(self):
        '''是否渠道用户
        '''
        return self.id < 0
    
    @CacheAttribute
    def is_kefu(self):
        '''是否客服
        '''
        for r in self.get_roles():
            if '客服' in r.name:
                return True
        return False

    @CacheAttribute
    def is_manager(self):
        '''是否管理员
        '''
        return self.is_root or self.get_roles().filter(type=Role.RoleType.ADMIN).exists()
    
    def current_userRole_is_root(self):
        '''兼容某些风云
        '''
        return self.is_manager
    
    def get_resource_ids(self,name,input_list=[]):
        input_list = set([ int(n) for n in input_list if isinstance(n,basestring) and n.isdigit()])
        resource_ids = set( self.get_resource(name).values_list('id',flat=True) )
        new_ids =  list((input_list & resource_ids) or resource_ids)
        return new_ids

    def set_resource(self,name,query_set):
        '''设置资源,平台登录时就设置资源了
        '''
        self.__resource_map[name] = query_set

    
    def get_resource(self,name):
        _r = self.__resource_map.get(name,None)
        if _r == None:
                _r = self._get_resource(name)
        self.__resource_map[name] = _r
        return self.__resource_map[name]

    def _get_resource(self,name):

        if name == 'channel':
            return  Resource.resource_map[name].objects\
                    .filter(
                            Q(agent__id__in=self._get_resource_from_model('agent').values_list('id',flat=True)) | 
                            Q(id__in=self._get_resource_from_model('channel').values_list('id',flat=True) )
                            ).prefetch_related('agent_set').distinct()
                            
        elif name == 'server':
            return  Resource.resource_map[name].objects\
                    .filter(
                            Q(group__id__in=self._get_resource_from_model('server_group').values_list('id',flat=True)) | 
                            Q(id__in=self._get_resource_from_model('server').values_list('id',flat=True) )
                            ).prefetch_related('group_set').distinct()
            
        return self._get_resource_from_model(name)
    
    def _get_resource_from_model(self,name):
        '''按资源名获取所属角色相应的资源
        '''
        ResourceClass = Resource.resource_map[name]
        if self.is_root:
            return  ResourceClass.objects.all()
        else:
            resource_objs = self.get_resource_obj().filter(name=name)
            try:
                if  len(resource_objs) == 1:
                    resource_ids = resource_objs[0].members
                else:
                    resource_ids = reduce(lambda x,y:y|x,resource_objs)
            except TypeError,e:
                    resource_ids = []

            return ResourceClass.objects.filter(id__in=resource_ids).distinct()
        
    def get_resource_obj(self):
        '''获取资源对象,超级管理拥有所有资源对象
        '''
        if self.is_root:
            return Resource.objects.all()
        else:
            return Resource.objects.filter(role__in=self.get_roles())

    def get_roles(self):
        '''获取角色
        '''
        if self.__cache_roles != None:
            return self.__cache_roles
        self.__cache_roles = self.role.all()
        return self.__cache_roles
    
    @classmethod
    def get_kefu_list(cls):
        return Admin.objects.filter(role__name__contains='客服').prefetch_related('role').distinct()  
    
    @classmethod
    def create_root(cls):
        '''创建系统管理员root账户
        '''
        channel_role,_c = Role.objects.get_or_create(name='渠道',type=1)
        _role,_c = Role.objects.get_or_create(name='系统管理员',type=0)
        admin,_c = cls.objects.get_or_create(alias="系统管理员",username='root')
        admin.role_ids = [_role.id]
        admin.status = cls.Status.NORMAL
        admin.password = admin.md5_password('123456')
        admin.save()
        print admin.role.all()
        print cls.objects.all()
        print '创建相关角色后,请务必删除root账户!'
        

        
class Admin(models.Model,BaseModelMixin,AdminManagerMixin):
    '''管理员模型
    '''
    
    class Status:
        NORMAL =  0 #正常 
        LOCK =    1 #锁定
        DELETED = 2 #删除
        
    class AdminType:
        NORMAL = 0  #正常用户
        CHANNEL = 1 #渠道用户
        
    TYPE_CHOICES = ((Status.NORMAL,'正常'),(Status.LOCK,'锁定'),(Status.DELETED,'删除'))
    
    role = models.ManyToManyField(Role,verbose_name='拥有的角色')
    alias = models.CharField('别名',max_length=50,db_index=True)
    username = models.CharField('用户名',max_length=50,db_index=True,unique=True)
    password = models.CharField('密码',max_length=32,db_index=True)
    last_ip = models.CharField('最后登录ip',max_length=20)
    create_time = models.DateTimeField('创建时间',auto_now_add=True)
    last_time = models.DateTimeField('最后登录时间',auto_now_add=True)
    login_count = models.IntegerField('登录次数',default=0)
    status = models.IntegerField('状态',default=0,choices=TYPE_CHOICES )
    session_key = models.CharField('会话key',max_length=40,db_index=True)
    
    
    role_ids = [] #保存角色id列表

            
    def __unicode__(self):
        return '%s' % self.username
    
    class Meta:
        db_table = u'admins_new'
        app_label = get_app_label()
        
        
    def save(self,*args,**kwargs):
        super(Admin,self).save(*args,**kwargs) #新建时没有对象,先保存一下
        if self.role_ids:#如果角色的列表存在,就保存
            self.role.clear()
            self.role.add(*Role.objects.filter(id__in=self.role_ids))
    
    def md5_password(self,password_str=''):
        return hashlib.new('md5', password_str + 'game.sanguo').hexdigest() if password_str else self.password 

class AdminInfo(models.Model,BaseModelMixin):
    '''管理员信息
    '''
    admin = models.ForeignKey(Admin, verbose_name='管理员信息')  
    email = models.EmailField()
    qq = models.CharField('qq',max_length=15)
    
    class Meta:
        db_table = u'admin_info'
        app_label = get_app_label()


Resource.register('admin',Admin)


