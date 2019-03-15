# -*- coding: utf-8 -*-

from django.db import models
from django.db import models
from django.db import connection,connections

from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute,
                   JSONField)

import datetime
import json
import pymongo
import MySQLdb
import traceback
from settings import get_app_label
from .server import *
from .log import Log


def get_time_str(time): 
    if time == '' or time == None:
        return ''
    return time.strftime('%Y-%m-%d %H:%M:%S')



class Player(models.Model,BaseModelMixin):
    STATUS_CHOICES = ((-2,'删号'),(-1,'封号'),(0,'正常'),(1,'游客'),(2,'VIP'),(3,'禁言'))

    TYPE_CHOICES = ((0,'自营'),(1,'当乐'),(2,'UC'),(3,'91'),(4,'云游'),(5,'飞流'),(6,'乐逗'),(8,'小虎'),(9,'4399'),(10,'facebook'),(11,'qq'))
    
    player_id = models.IntegerField(u'玩家标识',default=0,db_index=True,unique=True)
    player_name = models.CharField(u'玩家名称',max_length=50,db_index=True)
    user_type = models.IntegerField(u'账号类型',default=0,db_index=True,choices=TYPE_CHOICES)
    link_key = models.CharField(u'关联第三方登录的KEY',db_index=True,max_length=50)
    create_time = models.DateTimeField(u'最后登录时间',auto_now_add=True,db_index=True)
    last_time =  models.DateTimeField(u'最后登录时间',auto_now_add=True,db_index=True)
    last_ip =  models.CharField(u'最后登录IP',max_length=32)
    last_key = models.CharField(u'最后一次验证参数',max_length=50,null=True,default='',db_index=True)
    login_num =  models.IntegerField(u'登录次数',default=1)
    
#    token = models.CharField(u'令牌',max_length=100,blank=True,null=True)

    status = models.IntegerField(u'账号状态',default=0,choices=STATUS_CHOICES)
    channel_id = models.CharField(u'渠道編號',db_index=True,max_length=20)
    mobile_key = models.CharField(u'手机串号',max_length=50,blank=True,null=True)
    
    other = models.CharField(u'其它信息,子渠道',max_length=500,blank=True,null=True)
    is_old = models.IntegerField(u'新旧玩家', default=0, null=True,choices=((0, '新玩家'),(1, '老玩家')))
    
    def __unicode__(self):
        return '%d_%s'%(self.user_type,self.username)
    
    
    def user_type_name(self):
        return self.TYPE_CHOICES.get(self.user_type,'未知')
    
    def create_time_str(self):
        return get_time_str(self.create_time)
    
    def last_time_str(self):
        return get_time_str(self.last_time)
    
    def is_lock(self):
        if self.status < 0:
            return True
        else:
            return False
         
         
    def get_mongo_info(self,server_model):
        '''获取玩家mongo信息
        '''
        player_info = {}
        try:
            master_server = server_model.master_server
            db_name,mongo_conn = master_server.get_mongo_conn()
            record = mongo_conn[db_name].gl.player.find_one({'pi':self.id})
            player_info = record
            mongo_conn.close()
        except Exception, ex:
            print ex 
        return player_info
    
    inside_table_name = 'log_neibuhao'
    
    @classmethod
    def get_inside_player_model_class(cls):
        Log._meta.db_table = cls.inside_table_name
        return Log    
    
    @classmethod
    def get_inside_player_list(cls):
        InsidePlayer = cls.get_inside_player_model_class()
        inside_player_ids = InsidePlayer.objects.using('read').all().values_list('log_user',flat=True)[:1000]
        return list(inside_player_ids)
    
    class Meta: 
        db_table = u'player_0'
        app_label = get_app_label()
        ordering = ('-id',)


class Gang(models.Model,BaseModelMixin):
    '''部族表模型'''
    STATUS_CHOICES = ((-1,'删除'),(0,'正常'))

    gang_id = models.IntegerField(u'部族标识',default=0,db_index=True,unique=True)
    gang_name = models.CharField(u'部族名称',max_length=50,db_index=True)
    create_time = models.DateTimeField(u'创建时间',auto_now_add=True,db_index=True)
    status = models.IntegerField(u'部族状态',default=0,choices=STATUS_CHOICES)
    level = models.IntegerField(u'部族等级',default=0)
    gang_master = models.IntegerField(u'宗长ID',default=0)
    build_level = models.CharField(u'部族建筑等级',default='{}',max_length=500)
    gang_assets = models.IntegerField(u'部族资金',default=0)
    declaration = models.CharField(u'部族宣言',max_length=500)
    gang_members = models.IntegerField(u'部族成员数',default=0,max_length=10)
    other = models.CharField(u'其它信息',max_length=500,blank=True,null=True)


    def create_time_str(self):
        return get_time_str(self.create_time)
    
    def last_time_str(self):
        return get_time_str(self.last_time)

    class Meta: 
        db_table = u'gang_0'
        app_label = get_app_label()
        ordering = ('-id',)

class ServerPlayer(object):
    '''
    '''
    def __init__(self,player_id):
        self.__mysql_conn = None

        self.sid = int(player_id) >> 20
        self.player_id = player_id
        self.setattr()

    def setattr(self):
        player_info = self._get_player_info()
        self.player_name = player_info.get('player_name','')
        self.user_type = player_info.get('user_type','')
        self.link_key = player_info.get('link_key','')
        self.login_num = player_info.get('login_num','')
        self.mobile_key = player_info.get('mobile_key','')
        self.last_time = player_info.get('last_time','')
        self.create_time = player_info.get('create_time','')
        self.other = player_info.get('other','')
        self.status = player_info.get('status','')
        self.player_id = player_info.get('player_id','')
        self.player_info = player_info

    def _get_player_info(self):
        try:
            self.__mysql_conn = Server.get_conn(self.sid)
            cur = self.__mysql_conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            sql='''select * from player_%s p WHERE player_id=%d''' % (self.sid,self.player_id )
            cur.execute(sql)
            player_info =  cur.fetchone()
            return player_info
        except:
            traceback.print_exc()
            return {}

    def update_info(self,key,value):
        try:
            _update_sql = '''update player_%s set `%s`='%s' where player_id=%d  ''' % (self.sid,key,value,self.player_id)
            filter_sql(_update_sql)
            cur = self.__mysql_conn.cursor()
            cur.execute(_update_sql)
            self.__mysql_conn.commit()
        except:
            print '[%s] update [%s]player info error !' % (datetime.datetime.now(),self.player_id)
            traceback.print_exc()

    def __del__(self):
        try:
            if self.__mysql_conn:
                self.__mysql_conn.close()
        except:
            traceback.print_exc()
        #super(ServerPlayer,self).__del__()


class Player_operation(models.Model,BaseModelMixin):
    player_id = models.IntegerField(u'角色id', max_length=100, db_index=True)
    type = models.CharField(u'操作类型', max_length=200, db_index=True)
    scene_id = models.CharField(u'场景id', max_length=100, db_index=True)
    account = models.CharField(u'玩家账号', max_length=200, db_index=True)
    content = models.CharField(u'数据', max_length=1000)
    create_time = models.DateTimeField(u'创建时间', auto_now_add=True, db_index=True)
    app_name = models.CharField(u'应用名',max_length=200)
    bundle_id = models.CharField(u'bundle_id',max_length=200, db_index=True)
    device_id = models.CharField(u'设备id',max_length=200, db_index=True)
    channel_key = models.CharField(u'渠道key',max_length=200, db_index=True)
    extra = models.CharField(u'附加参数',max_length=500, db_index=True)

    def create_time_str(self):
        return get_time_str(self.create_time)

    class Meta:
        db_table = u'player_operation'
        app_label = get_app_label()