# -*- coding: utf-8 -*-
#日志类模型
#
from django.db import models
from django.db import connection,connections
import datetime, time, json, calendar
from util import datetime_to_str,trace_msg
from django.utils.datastructures import SortedDict 
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)

try:
    import cPickle as pickle
except ImportError:
    import pickle
import uuid, json, hashlib
from settings import get_app_label,STATIC_ROOT,PROJECT_ROOT
import traceback
import os,glob



class Log(models.Model,BaseModelMixin):
    '''日志基本模型
    '含有空值的列很难进行查询优化，因为它们使得索引、索引的统计信息以及比较运算更加复杂。你应该用0、一个特殊的值或者一个空串代替空值。
    '''
    log_time = models.DateTimeField('记录时间',auto_now_add=True,db_index=True)
    log_type = models.IntegerField('类型',default=0)
    log_tag = models.IntegerField('标记',default=0,null=True)
    log_user = models.IntegerField('角色ID',default=0,null=True,db_index=True)
    log_name = models.CharField('角色名',max_length=100,default='123', null=True,blank=False)
    log_server = models.IntegerField('服务器ID',default=0, null=True)
    log_level = models.IntegerField('等级',null=True,default=0)
    log_previous = models.CharField('之前值',max_length=200, default='',null=True, blank=True)
    log_now = models.CharField('现在值',max_length=200, default='',null=True, blank=True)
    log_relate = models.CharField('流水标识',max_length=32,default='',null=True,db_index=True)
    f1 = models.CharField(max_length=100, default='',null=True, blank=True)
    f2 = models.CharField(max_length=100, default='',null=True, blank=True)
    f3 = models.CharField(max_length=100, default='',null=True, blank=True)
    f4 = models.CharField(max_length=100, default='',null=True, blank=True)
    f5 = models.CharField(max_length=100, default='',null=True, blank=True)
    f6 = models.TextField(default='',null=True, blank=True)
    f7 = models.CharField(max_length=100, default='',null=True, blank=True)
    f8 = models.TextField(default='',null=True, blank=True)
    log_channel = models.IntegerField('渠道ID',default=0, null=True,blank=True)
    log_data = models.IntegerField('数据',null=True,default=0)
    log_result = models.IntegerField('结果',null=True,default=0)
    
    def __unicode__(self):
        return '%d_%d_%s' % (self.log_type, self.log_user, self.log_time.strftime('%Y-%m-%d'))

    def log_time_str(self):
        return datetime_to_str(self.log_time) 
    
    @classmethod
    def get_create_table_sql(cls,table_name):
        sql = 'CREATE TABLE IF NOT EXISTS  %s LIKE %s;' % (table_name,cls._Meta.db_table)
        return sql
    
    class _Meta: # 防止使用log表时失去元表名
        db_table = u'log_0_new'
        app_label = get_app_label()

    Meta = _Meta

class LogDefineMixin(object):
    
    @classmethod
    def get_truncate_table_sqls(cls):
        sqls = []
        log_defs = cls.objects.filter(status=cls.Status.NORMAL)
        for ld in log_defs:
            if ld.key == 'statistic_date':
                continue 
            sqls.append('truncate table %s;' % ld.table_name)
        return sqls
        
    def get_create_table_sql(self):
        return Log.get_create_table_sql(self.table_name)
    
    def get_create_index_sqls(self):
        sqls = []
        for f in self.get_index_fields():
            
            index_name = '%s_%s_index' % (self.table_name,f['filed_name'])
            sql = "CREATE INDEX `%s` ON `%s` (%s);" % (index_name,self.table_name,f['filed_name'])
            sqls.append(sql)
        return sqls
    
    def get_index_fields(self):
        index_fields = []
        for k,v in self.config.iteritems():
            if v.get('db_index','') and v.get('verbose_name','').strip() :
                v['filed_name'] = k
                index_fields.append(v)
        return index_fields
    
    @classmethod
    def get_create_table_sqls(cls,is_center=False):
        '''获取需要创建表的sql
        '''
        status = cls.Status.CENTER if is_center else cls.Status.NORMAL
        sqls = []
        for t in cls.objects.filter(status=status):
            sqls.append(t.get_create_table_sql())
        return sqls
    
    def get_field_name_by_verbose_name(self,verbose_name):
        for field_name,config in self.config:
            if verbose_name == config['verbose_name'] :
                return field_name
            
            
class LogDefine(models.Model,BaseModelMixin,LogDefineMixin):
    '''日志类定义
    '''
    
    class Status:
            NORMAL = 0
            CENTER = 1
            
    TYPE_CHOICES  = ((Status.NORMAL,'分服'),(Status.CENTER,'中央服'))
    
    key = models.CharField('日志表名',max_length=20,db_index=True)
    name = models.CharField('日志名',max_length=50)
    remark = models.CharField('备注',max_length=1000)
    status = models.IntegerField(default=0,choices=TYPE_CHOICES)
    _config = models.TextField('配置')
    trigger =  models.TextField('触发器sql',default="",null=False)
    
    #  这里未来兼容sql文件导入和mysqldb执行的sql 处理有点乱, 到时再改
    def get_other_sqls(self,is_sql_file=False):
        '''获取其他sql
        @is_sql_file:是否sql文件用的
        '''
        sqls = []
        sp = ';'
        the_cut_sp = '\\'
        if '//' in self.trigger:
            sp = '//'
        for sql in self.trigger.split(sp):
            if the_cut_sp in sql :
                if  is_sql_file:
                    sql = sql.replace(the_cut_sp,'')
                else:
                    sql = ''
            elif not is_sql_file:
                    sql = sql.replace('$$','')
            if sql:
                sqls.append('%s' % sql)
        return sqls
    
    @property
    def config(self):
        _r = {}
        field_config = self.default_config()
        try:
            _r = json.loads(self._config)
            field_config.update(_r)
        except:
            pass
        _r = field_config
        sort_dict = SortedDict(_r)
        sort_dict.keyOrder = sorted(_r.keys(),reverse=True)
        return sort_dict
    
    @config.setter
    def config(self,obj_value):
        if isinstance(obj_value,dict):
            obj_value = json.dumps(obj_value)
        self._config = obj_value
    
    @CacheAttribute
    def json_config(self):
        return json.dumps(self.config, ensure_ascii=True)
    
    @property
    def table_name(self):
        return 'log_%s' % self.key.strip()
    
    def default_config(self):
        '''默认的日志类配置
        '''
        _d = {}
        for f in Log._meta.fields:
            if f.name.lower() == 'id':
                continue

            _d[f.name] = {"db_index":f.db_index,"verbose_name":f.verbose_name}
        return _d
     
        
    def save(self,*args,**kwargs):
        return super(LogDefine,self).save(*args,**kwargs)
    
    def __unicode__(self):
        return '%s' % self.key

    class Meta: 
        db_table = u'def_log'
        app_label = get_app_label()
        
        
    
        
class DictBaseType(object):
    '''基本字典类型
    '''
    NAME = '字典'
    DEFAULT_JSON = '{}'
    def __init__(self,dict_config):
        self.dict = dict_config
    def get_dict(self):
        return self.dict


class DBDictType(DictBaseType):
    '''数据表
    '''
    NAME = '数据表'
    DEFAULT_JSON = '{"table_name":"","key_name":"","value_name":""}'
    def get_dict(self):
        _r = {}
        sql = 'SELECT DISTINCT `{key_name}` a,`{value_name}` b FROM {table_name} LIMIT 2000;'
        sql = sql.format(**self.dict)
        cur = connections['read'].cursor()
        cur.execute(sql)
        for row in cur.fetchall():
            _r[str(row[0])] = row[1]
        return _r

ROOT_PATH = os.path.dirname(PROJECT_ROOT)
class FileDicType(DictBaseType):
    '''从文件内拿json
    '''
    NAME = '文件'
    DEFAULT_JSON = '{"file_path":"","key_name":"","value_name":""}'
    def get_dict(self):
        _r = {}
        the_file_path  = os.path.join(ROOT_PATH,self.dict['file_path'])
        try:
            with open(the_file_path,'rb') as fp:
                _r = the_dict_data = json.loads(fp.read() )
        except:
            pass
        return _r
    
    
from util import get_files_from_dir
class DirDictType(DictBaseType):
    '''目录里拿字典
    '''
    NAME = '目录'
    DEFAULT_JSON = '{"dir_path":"","key_name":"","value_name":""}'
    def get_dict(self):
        _r = {}
        the_dir_path  = os.path.join(ROOT_PATH,self.dict['dir_path'])

        try:
            if os.path.isdir(the_dir_path):
                for the_json_file in get_files_from_dir(the_dir_path,'.json'):

                    with open(the_json_file,'rb') as fp:
                        json_str = fp.read()
                        json_data = json.loads(json_str)
                        key_name = self.dict.get('key_name','')
                        value_name = self.dict.get('value_name','')
                        if key_name and value_name:
                            key = json_data.get(key_name,'')
                            value = json_data.get(value_name,'')
                            if key:
                                _r[key] =  value
        except:
            print the_dir_path
            traceback.print_exc()
        return _r 
    

class DictDefine(models.Model,BaseModelMixin):   
    '''字典定义
    '''
    TYPE_DICT = {   0:DictBaseType,
                    1:DBDictType,
                    2:FileDicType,
                    3:DirDictType
                    }
  
    SELECT_CHOICES = [ (k,v.NAME,v.DEFAULT_JSON) for k,v in TYPE_DICT.iteritems() ]
    _TYPE_CHOICES = ( (k,v.NAME) for k,v in TYPE_DICT.iteritems() )

    name = models.CharField('字典名',max_length=100,blank=False) 
    key = models.CharField('标识名',max_length=50,unique=True,default=lambda:uuid.uuid4().hex,db_index=True)
    _dict = models.TextField('存键值',default=lambda: pickle.dumps({}))
    group  = models.CharField('组',max_length=50,default="") 
    type = models.IntegerField('字典的类型',default=0, choices=_TYPE_CHOICES)
    remark = models.CharField('备注',max_length=400) 
    
    __cache_dict = {}
    
    @property
    def dict(self):
        return pickle.loads(str(self._dict))
    
    @dict.setter
    def dict(self,obj_value):
        for k,v in obj_value.iteritems():
            obj_value[k] = v.encode('utf-8')
        _data = pickle.dumps(obj_value)
        self._dict = _data
    
    @property    
    def json_dict(self):
        return json.dumps(self.dict,ensure_ascii=False)
    
    @json_dict.setter
    def json_dict(self,j_value):
        j_value = j_value or '{}'
        self.dict = json.loads(j_value)
    
    @classmethod
    def get_dict_for_key(cls,key_name,reverse=False):
        _r = {}
        try:
            if '{' in key_name:
                _r = json.loads(key_name)
            else:
                dict_model = cls.objects.get(key=key_name)
                _r = dict_model.get_dict()
            if reverse:
                _r = cls.reverse_dict(_r)
        except:
            pass
        return _r
        
    @staticmethod
    def reverse_dict(_dict):
        '''反转字典
        '''
        return dict( (v,k) for k, v in _dict.items() )
    
    def get_dict(self):
        '''获取字典
        '''
        _r = {}
        if self.__cache_dict :return self.__cache_dict
        type_class = self.TYPE_DICT.get(self.type)
        try:
            dict_handler_obj = type_class(self.dict)
            _r = dict_handler_obj.get_dict()
        except:
            traceback.print_exc()
        self.__cache_dict =  _r
        return self.__cache_dict
    
    def get_json_data(self):
        return json.dumps(self.get_dict(),ensure_ascii=False)
    
    @classmethod
    def get_group(cls):
        '''获取字典的分组
        '''
        groups = [ g for g in cls.objects.using('read').values_list('group', flat=True).distinct() if g]
        
    def __unicode__(self):
        return '%s' % self.name
    
    class Meta:
        db_table = u'def_dict'
        app_label = get_app_label()
        


#旧的 不要删,有其他会引用 草---------------------------------------------------
        
class FieldDefine(models.Model,BaseModelMixin):
    log_type = models.IntegerField(default=0)
    field_type = models.CharField(max_length=20)
    field_name = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    field_format = models.CharField(max_length=100) 
    create_index = models.BooleanField(default=0)
    
    def __unicode__(self):
        return '%s' % self.field_name
    
    
    class Meta: 
        db_table = u'def_field'
        app_label = get_app_label()
        
class ValueDefine(models.Model,BaseModelMixin):
    field_id = models.IntegerField()
    value_id = models.IntegerField()
    value = models.CharField(max_length=100)
    def __unicode__(self):
        return '%s' % self.value
    
    class Meta: 
        db_table = u'def_value'
        app_label = get_app_label()
 
