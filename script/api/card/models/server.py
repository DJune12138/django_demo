# -*- coding: utf-8 -*-

from django.db import models
from django.db import connection,connections
from django.core.management.color import no_style

from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)

from util import datetime_to_str,trace_msg

import datetime,os
import json
from pymongo import MongoClient
import MySQLdb
import traceback
from models.resource import Resource
from models.player import Player,Gang
from models.log import Log
import json
from settings import DATABASES
from settings import get_app_label
from settings import STATIC_ROOT

class GmServermixin(object):
    '''游戏服Gm相关
    '''
    @CacheAttribute
    def gm_address(self):
        return 'http://%s:%s/service' % (self.game_addr,self.get_log_db_config().get('gm_port','80'))


class ServerModelMysqlMixin(object):
    '''游戏服mysql相关
    '''
    @classmethod
    def get_created_index(cls,conn,db_name):
        '''获取已经创建的了的索引
        '''
        sql = '''SELECT index_name FROM information_schema.STATISTICS where TABLE_SCHEMA="%s" AND INDEX_NAME!='PRIMARY';''' % (db_name)
        created_index_list = []
        cur = conn.cursor()
        cur.execute(sql)
        for index_name in cur.fetchall():
            created_index_list.append(index_name)
        return created_index_list
    
    def get_base_database_sql(self):
        return 'CREATE DATABASE IF NOT EXISTS %s  default charset utf8 COLLATE utf8_unicode_ci;' % self.db_name
    
    def get_create_player_table_sqls(self):
        sqls = [Player.get_create_model_sql('player_%s' % self.id)]
        #player索引建立
        player_index = connection.creation.sql_indexes_for_model(Player, no_style())
        sqls.extend([pi_sql.replace(Player.get_table_name(), 'player_%s' % self.id).replace('ON ', 'ON %s.'% self.db_name) for pi_sql in player_index])
        return sqls

    def get_create_gang_table_sqls(self):
        sqls = [Gang.get_create_model_sql('gang_%s' % self.id)]
        #player索引建立
        gang_index = connection.creation.sql_indexes_for_model(Gang, no_style())
        sqls.extend([pi_sql.replace(Gang.get_table_name(), 'gang_%s' % self.id).replace('ON ', 'ON %s.'% self.db_name) for pi_sql in gang_index])
        return sqls
    
    def get_drop_base_log_sql(self):
        return 'drop table IF EXISTS %s ;' % Log._Meta.db_table
        
    def get_create_base_log_sql(self):
        Log._meta.db_table = Log._Meta.db_table
        return Log.get_create_model_sql()
    
    def create_database(self):
        '''创建数据库
        '''
        sql = self.get_base_database_sql()
        try:
            conn = self.mysql_conn(select_db=False)
            cur = conn.cursor()
            cur.execute(sql)
        except MySQLdb.Warning,e:
            pass
        except:
            traceback.print_exc()
        
    def create_base_table(self):
        '''创建基本log表和player_表
        '''
        self.create_database()
        for sql in self.get_create_player_table_sqls() + self.get_create_gang_table_sqls() + [self.get_drop_base_log_sql(),self.get_create_base_log_sql()]:
            try:
                self.execute_sql(sql)
            except MySQLdb.Warning,e:
                pass
            except MySQLdb.OperationalError,e:
                pass
            
    def execute_sql(self,sql):
        conn  = self.mysql_conn()
        cur = conn.cursor()
        cur.execute(sql)
        return (conn,cur)
    
    db_prefix = 'ss_log'
    
    @CacheAttribute
    def db_name(self):
        return self.get_log_db_config().get('db','') or '%s%s' % (self.db_prefix,self.id)


class Server(models.Model,BaseModelMixin,GmServermixin,ServerModelMysqlMixin):
    '''服务器模型
    '''
    
    class Status:
        DELETED     = -1
        STOP        = 0
        MAINTENANCE = 1
        NORMAL      = 2
        BUSY        = 3
        FULL        = 4
        HOT         = 5
        TEST        = 6
        
    # STATUS_CHOICES = ((-1, '已删除'),(0,'停机'),(1,'维护'),(2,'良好'),(3,'繁忙'),(4,'爆满'),(5, '火爆'),(6, '测试'))
    STATUS_CHOICES = ((-1, '已删除'),(0,'停服'),(1,'维护'),(2,'顺畅'),(3,'拥挤'),(4,'爆满'),(6,'测试'))
    # COMMEND_CHOICES = ((0,'无'),(1,'推荐'),(2,'新服'),(3,'热门'),)
    COMMEND_CHOICES = ((0,'无'),(1,'推荐'),(2,'新服'),)

    client_ver = models.CharField(u'针对客户端版本',max_length=500,default='')
    name = models.CharField(u'服务器名称',max_length=50)
    alias = models.CharField(u'服务器别名',max_length=20,default='')
    game_addr = models.CharField(u'服务器地址',max_length=100)
    game_port = models.IntegerField(u'服务器端口',default=0)
    log_db_config = models.CharField(u'日志数据库',max_length=500)
    report_url = models.CharField(u'战报地址',max_length=100)
    status =  models.IntegerField(u'服务器状态',default=0,choices=STATUS_CHOICES)
    create_time = models.DateTimeField(u'开服时间',auto_now_add=True)
    require_ver =  models.IntegerField(u'需要客户端最低版本',default=0)
    remark = models.CharField(u'备注',max_length=200)
    json_data = models.CharField(u'附加JSON数据',default='',max_length=1000)
    order = models.IntegerField(u'排序',default=0)
    commend = models.IntegerField(u'推荐',default=0,choices=COMMEND_CHOICES)
    is_ios = models.IntegerField(u'是否IOS服务器', default=0)
    last_time = models.DateTimeField(u'最后修改时间',auto_now_add=True)
    tabId = models.IntegerField(u"分组ID",default=0)
    game_data = models.CharField(u'游戏里的JSON数据(战力,等级)',default="",max_length=1000)
    __conn = None
    __cache_log_db_config = {}
    
    @classmethod
    def get_conn(cls,server_id=0,databases='default',connect_timeout=10):
        the_conn = None
        try:
            if server_id:
                the_server = cls.objects.using('read').get(id=server_id)
                the_conn = the_server.mysql_conn(True)
            else:
                the_conn_str = DATABASES.get(databases, {})
                the_conn = MySQLdb.connect(host=the_conn_str['HOST'], user=the_conn_str['USER'], passwd=the_conn_str['PASSWORD'], port=int(the_conn_str.get('PORT',3306)),db=the_conn_str['NAME'], charset='utf8',connect_timeout=connect_timeout)
            the_conn.autocommit(1)
        except Exception, e:
            print('get mysql conn has error :%d,%s' % (server_id, e))
            raise Exception, e
        return the_conn
    
    def mysql_conn(self,select_db=True,connect_timeout=10):
        '''mysql的连接
        '''
        if not self.__conn:
            try:
                the_conn_str = self.get_log_db_config()
                the_conn = MySQLdb.connect(host=the_conn_str['host'], user=the_conn_str['user'], passwd=str(the_conn_str['password']), port=the_conn_str.get('port',3306), charset='utf8',connect_timeout=connect_timeout)
                the_conn.autocommit(1)
                self.__conn = the_conn
            except  Exception, e:
                print trace_msg()
        if self.__conn:
            if select_db:
                    self.__conn.select_db(self.db_name)
        return self.__conn
    
    def get_log_db_config(self):
        try:
            _r = self.__cache_log_db_config or json.loads(self.log_db_config)
            self.__cache_log_db_config = _r
            return self.__cache_log_db_config
        except:
            return {}
        
    
    def get_json_data(self):
        try:
            json_data = self.json_data if self.json_data.find('{')==0 else '{%s}' % self.json_data
            server_config = json.loads(json_data)
            return server_config
        except:
            return {}
        
    def set_json_data(self,data):
        if isinstance(data,dict):
            data = json.dumps(data,ensure_ascii=False)
        self.json_data = data[1:-1]
    
    def set_log_db_config(self,data):
        if isinstance(data,dict):
            data = json.dumps(data,ensure_ascii=False)
        self.log_db_config = data
    
        
            
    def get_mongo_conn(self):   
        db_config = self.get_log_db_config()
        db_port = int(db_config.get('mongo_port',27017))
        db_user = db_config.get('mongo_user','')
        db_password = db_config.get('mongo_password','')
        db_address = db_config.get('mongo_host','')
        db_name = 'sid%s' % self.id
        mongo_con = None
        uri = "mongodb://{0}:{1}".format(db_address,db_port)
        try:
            if db_user and db_password:
                uri = "mongodb://{0}:{1}@{2}:{3}/the_database?authMechanism=MONGODB-CR".format(db_user,db_password,db_address,db_port)
            mongo_con = MongoClient(uri)
        except:
            traceback.print_exc()
        return (db_name,mongo_con)
        
    @CacheAttribute
    def master_server(self):
        master_id = self.master_id
        if master_id != self.id:
            try:
                return self.__class__.objects.using(self.__class__.objects.db).get(id=master_id)
            except:
                pass
        return self
    
    @CacheAttribute
    def master_id(self):
        return self.get_master_id()
    
    def get_master_id(self):
        result = self.id
        try:
            if self.json_data != '':
                json_data = '{%s}' % self.json_data
                cfg = json.loads(json_data)
                result = cfg.get('master_server_id', self.get_log_db_config().get('master_server_id',self.id))
        except Exception, ex:
            print 'get_master_id error %s(%s) :%s'% (self.name,self.id,str(ex))
        return result 

    @CacheAttribute
    def son_id(self):
        return self.get_son_id()

    def get_son_id(self):
        pass

    
    def __unicode__(self):
        return '%s(%s)' % (self.name,self.id)
    
    def create_time_str(self):
        return datetime_to_str(self.create_time) if self.create_time else ''

    def write_domain_ip(self):
        import socket
        parse_domain = socket.gethostbyname(self.game_addr)
        get_ip = self.get_domain_ip()
        is_change = True
        if get_ip:
            if get_ip != parse_domain:
                self.remark = self.remark.replace("域名IP:%s" % get_ip, "域名IP:%s" % parse_domain)
            else:
                is_change = False
        else:
            self.remark += "(域名IP:%s)" % parse_domain
            
        if is_change:
            self.save()

    def get_domain_ip(self):
        import re
        s_ip = re.compile("\(域名IP:(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})\)")
        re_result = s_ip.findall(self.remark)
        if re_result:
            return re_result[0]
        else:
            return False
    
    @classmethod
    def get_server_list(cls):
        return cls.objects.filter(~models.Q(status=cls.Status.DELETED)).order_by('-status')

    @classmethod
    def get_group_version(cls):
        try:
            return cls.group_set.all()[0].version if cls.group_set.all()[0].version else 0
        except BaseException as e:
            print e
            return 0

    @classmethod
    def get_group_name(cls):
        try:
            return cls.group_set.all()[0].name if cls.group_set.all()[0].name else ""
        except BaseException as e:
            print e
            return ""
    
    class Meta: 
        db_table = u'servers'
        ordering = ('order',)
        app_label = get_app_label()


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
        self.last_ip = player_info.get('last_ip','')
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


class Group(models.Model):
    group_key = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    server = models.ManyToManyField(Server)
    login_url = models.CharField(u'登陆服地址',max_length=100)
    card_url = models.CharField(u'礼包卡地址',max_length=100)
    notice_url = models.CharField(u'公告地址',max_length=100)
    cdn_url = models.CharField(u'cdn地址',max_length=100)
    sdk_url = models.CharField(u'平台地址',max_length=100)
    custom_url = models.CharField(u'客服地址',max_length=100)
    audit_version = models.IntegerField(u'审核版本',max_length=40)
    audit_server = models.IntegerField(u'审核服',max_length=40)
    audit_versions = models.CharField(u'审核版本s',max_length=100)
    audit_servers = models.CharField(u'审核服s',max_length=100)
    notice_select = models.IntegerField(u'分区公告',default=0)
    remark = models.CharField(u'备注',max_length=200)
    other = models.CharField(u'附加json', max_length=500)
    pid_list = models.CharField(u'联运ID列表', max_length=500)
    version = models.IntegerField(u'版本号',max_length=40)
    resource_version = models.IntegerField(u'资源版本号',max_length=40)
    last_time = models.DateTimeField(blank=True,null=True)

    @property
    def other_dict(self):

        try:
            _other = self.other.strip()
            if _other[0] != '{':
                _other = '{%s' % _other
            if _other[-1] != '}':
                _other = '%s}' % _other
        except:
            _other = "{}"
        return json.loads(_other)

    def last_time_str(self):
        return datetime_to_str(self.last_time) if self.last_time else ''

    @other_dict.setter
    def other_dict(self,value):
        self.other = json.dumps(value or {},ensure_ascii=False)

    class Meta: 
        db_table = u'groups'
        app_label = get_app_label()

class GroupList(models.Model):
    key = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    order = models.IntegerField(u'排序',default=0)
    server = models.ManyToManyField(Server)
    partion = models.ForeignKey(Group)

    class Meta:
        db_table = u'grouplist'
        app_label = get_app_label()

class KuaFuServer(models.Model,BaseModelMixin,GmServermixin,ServerModelMysqlMixin):
    '''跨服模型
    '''

    class Status:
        DELETED     = -1
        STOP        = 0
        MAINTENANCE = 1
        NORMAL      = 2
        BUSY        = 3
        FULL        = 4
        HOT         = 5
        TEST        = 6

    STATUS_CHOICES = ((-1, '已删除'),(0,'停机'),(1,'维护'),(2,'良好'),(3,'繁忙'),(4,'爆满'),(5, '火爆'),(6, '测试'))
    COMMEND_CHOICES = ((0,'无'),(1,'推荐'),(2,'新服'),(3,'热门'),)

    client_ver = models.CharField(u'针对客户端版本',max_length=500,default='')
    name = models.CharField(u'服务器名称',max_length=20)
    alias = models.CharField(u'服务器别名',max_length=20,default='')
    game_addr = models.CharField(u'服务器地址',max_length=100)
    game_port = models.IntegerField(u'服务器端口',default=0)
    log_db_config = models.CharField(u'日志数据库',max_length=500)
    report_url = models.CharField(u'战报地址',max_length=100)
    status =  models.IntegerField(u'服务器状态',default=0,choices=STATUS_CHOICES)
    create_time = models.DateTimeField(u'开服时间',auto_now_add=True)
    require_ver =  models.IntegerField(u'需要客户端最低版本',default=0)
    remark = models.CharField(u'备注',max_length=200)
    json_data = models.CharField(u'附加JSON数据',default='',max_length=1000)
    order = models.IntegerField(u'排序',default=0)
    commend = models.IntegerField(u'推荐',default=0,choices=COMMEND_CHOICES)
    is_ios = models.IntegerField(u'是否IOS服务器', default=0)
    __conn = None
    __cache_log_db_config = {}

    @classmethod
    def get_conn(cls,server_id=0,databases='default',connect_timeout=10):
        the_conn = None
        try:
            if server_id:
                the_server = cls.objects.using('read').get(id=server_id)
                the_conn = the_server.mysql_conn(True)
            else:
                the_conn_str = DATABASES.get(databases, {})
                the_conn = MySQLdb.connect(host=the_conn_str['HOST'], user=the_conn_str['USER'], passwd=the_conn_str['PASSWORD'], port=int(the_conn_str.get('PORT',3306)),db=the_conn_str['NAME'], charset='utf8',connect_timeout=connect_timeout)
            the_conn.autocommit(1)
        except Exception, e:
            print('get mysql conn has error :%d,%s' % (server_id, e))
            raise Exception, e
        return the_conn

    def mysql_conn(self,select_db=True,connect_timeout=10):
        '''mysql的连接
        '''
        if not self.__conn:
            try:
                the_conn_str = self.get_log_db_config()
                the_conn = MySQLdb.connect(host=the_conn_str['host'], user=the_conn_str['user'], passwd=str(the_conn_str['password']), port=the_conn_str.get('port',3306), charset='utf8',connect_timeout=connect_timeout)
                the_conn.autocommit(1)
                self.__conn = the_conn
            except  Exception, e:
                print trace_msg()
        if self.__conn:
            if select_db:
                    self.__conn.select_db(self.db_name)
        return self.__conn

    def get_log_db_config(self):
        try:
            _r = self.__cache_log_db_config or json.loads(self.log_db_config)
            self.__cache_log_db_config = _r
            return self.__cache_log_db_config
        except:
            return {}


    def get_json_data(self):
        try:
            json_data = self.json_data if self.json_data.find('{')==0 else '{%s}' % self.json_data
            server_config = json.loads(json_data)
            return server_config
        except:
            return {}

    def set_json_data(self,data):
        if isinstance(data,dict):
            data = json.dumps(data,ensure_ascii=False)
        self.json_data = data[1:-1]

    def set_log_db_config(self,data):
        if isinstance(data,dict):
            data = json.dumps(data,ensure_ascii=False)
        self.log_db_config = data



    def get_mongo_conn(self):
        db_config = self.get_log_db_config()
        db_port = int(db_config.get('mongo_port',27017))
        db_user = db_config.get('mongo_user','')
        db_password = db_config.get('mongo_password','')
        db_address = db_config.get('mongo_host','')
        db_name = 'sid%s' % self.id
        mongo_con = None
        uri = "mongodb://{0}:{1}".format(db_address,db_port)
        try:
            if db_user and db_password:
                uri = "mongodb://{0}:{1}@{2}:{3}/the_database?authMechanism=MONGODB-CR".format(db_user,db_password,db_address,db_port)
            mongo_con = MongoClient(uri)
        except:
            traceback.print_exc()
        return (db_name,mongo_con)

    @CacheAttribute
    def master_server(self):
        master_id = self.master_id
        if master_id != self.id:
            try:
                return self.__class__.objects.using(self.__class__.objects.db).get(id=master_id)
            except:
                pass
        return self

    def master_id(self):
        return self.get_master_id()

    def get_master_id(self):
        result = self.id
        try:
            if self.json_data != '':
                json_data = '{%s}' % self.json_data
                cfg = json.loads(json_data)
                result = cfg.get('master_server_id', self.get_log_db_config().get('master_server_id',self.id))
        except Exception, ex:
            print 'get_master_id error %s(%s) :%s'% (self.name,self.id,str(ex))
        return result

    def __unicode__(self):
        return '%s(%s)' % (self.name,self.id)

    def create_time_str(self):
        return datetime_to_str(self.create_time) if self.create_time else ''

    def write_domain_ip(self):
        import socket
        parse_domain = socket.gethostbyname(self.game_addr)
        get_ip = self.get_domain_ip()
        is_change = True
        if get_ip:
            if get_ip != parse_domain:
                self.remark = self.remark.replace("域名IP:%s" % get_ip, "域名IP:%s" % parse_domain)
            else:
                is_change = False
        else:
            self.remark += "(域名IP:%s)" % parse_domain

        if is_change:
            self.save()

    def get_domain_ip(self):
        import re
        s_ip = re.compile("\(域名IP:(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})\)")
        re_result = s_ip.findall(self.remark)
        if re_result:
            return re_result[0]
        else:
            return False

    @classmethod
    def get_server_list(cls):
        return cls.objects.filter(~models.Q(status=cls.Status.DELETED)).order_by('-status')

    class Meta:
        db_table = u'kuafu_servers'
        ordering = ('order',)
        app_label = get_app_label()



Resource.register('server',Server)
Resource.register('server_group',Group)
Resource.register('server_grouplist',GroupList)

