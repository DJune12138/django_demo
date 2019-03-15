# -*- coding: utf-8 -*-
#查询类模型
#
from django.db import models
from django.db import connection,connections
import datetime, time, json, calendar
from util import datetime_to_str,trace_msg
from django.utils.datastructures import SortedDict 
import re
from .log import LogDefine,DictDefine
from .menu import Menu
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)
from settings import get_app_label


class SqlAnalysis(object):
    '''sql解析
    @param TAG_FORMAT: 默认的标签外围
    @param params:  字典 一键一列表 例如reuqest.POST
    '''
    TAG_FORMAT = '{{%s}}'

    
    
    mark_map =     {"server_id":  {"name":"server_id","multiple":False},                  #服务器ID替换
                    "server_ids": {"name":"server_id","multiple":True},                   #多个服务器ID替换
                    "server_name":{"name":"server_name","multiple":False},                #服务器名
                    "master_id":  {"name":"master_id","multiple":False},                  #母服ID
                    "master_db":  {"name":"master_db","multiple":False},                  #母服db名
                    "sdate":      {"name":"sdate"},                                       #开始时间
                    "edate":      {"name":"edate"},                                       #结束时间
                    "sd":         {"name":"sd"},                                       #开始时间
                    "ed":         {"name":"ed"},                                       #结束时间
                    "channel_id": {"name":"channel_id","multiple":False},                 #渠道id
                    "channel_ids":{"name":"channel_id","multiple":True},                  #渠道id
                    "agent_name": {"name":"agent_name"},                                  #平台名
                    "neibuhao"  : {"name":"neibuhao","multiple":True},
                    'platform_id':{"name":"platform_id","multiple":False},                #游戏平台
                    'platform_ids':{"name":"platform_id","multiple":True}
                     }
    
    
    def __init__(self,source_sql,params):
        '''初始化
        @param source_sql 原SQL
        '''
        self.sql = source_sql
        self.query_sql = source_sql.strip()
        self.params = params
        self.order_str = ''
        self.limit_str = ''
        
    def query_sql_handle(self,sql=''):
        '''查询sql转换
        '''
        values_list = []
        for mark_name,config in self.mark_map.iteritems():
            if self.has_mark(mark_name):#sql存在这个标签
                param_name = config['name']
                value = self.get_param_value(param_name,config)

                if value: #先把没值的标记替换
                    values_list.append((mark_name,value))
                else:
                    self.empty_param_handle(mark_name)
        if values_list:
            for mark_name,value in values_list:
                self.replace_mark_to_value(mark_name,value)

    
    def get_param_value(self,param_name,config):
        '''获取参数值
        '''
        values = self.params.get(param_name,[]) or ['']
        the_value = str(values[0])
        if the_value != '':                      #参数不为空   
            if not config.get('multiple',False): #不是多选
                values = values[0]
            else:
                the_sp =  r',|\s'
                if  re.search(the_sp,the_value):
                    values = re.split(the_sp,the_value)
            dict_key = config.get('dict','')     #输入值转换,支持中文转成id
            if dict_key:
                if not config.get('fixed',False):
                    value_def = DictDefine.get_dict_for_key(dict_key,reverse=True) 
                    values = self.convert_input_value(values,value_def)
                else:#固定值
                    values = dict_key
            else:
                values = self.convert_input_value(values,{})
            return values 
        
    
    def convert_input_value(self,values,value_def):
        '''转换输入
        '''
        if isinstance(values,(list,tuple,set)):
            _r = []
            for v in values:
                value = str(value_def.get(v,value_def.get(str(v),v)))
                if not value.isdigit():
                    value= "'%s'" % value
                _r.append(value)
            return ','.join(_r)
        else:
            return  value_def.get(values,values)
    

    def empty_param_handle(self,mark_name):
        '''传入参数为空时,把 SQL的条件 例如:log_user={{player_id}} 换换成 0=0
        '''
        the_mark = self.make_mark(mark_name)
        #pattern = re.compile(r'''[\w\.`(+=*]*[\W`]?(not[\s]+)?(like|in|=|=>|<=|>|<|!=)[\W]*%s[^\s]*[\s$]*''' % the_mark,flags=re.I)
        pattern = re.compile(r'''[\S]*[\W`]?([\s]+not[\s]+)?(like|in|=|=>|<=|>|<|!=)[\W]*%s[^\s]*[\s$]*''' % the_mark,flags=re.I)
        _s = int(time.time())
        self.query_sql = re.sub(pattern,' 0=0 ',self.query_sql)

        
    def set_limit(self,page_size,page_num):
        '''设置sql limit
        '''
        page_num,page_size = int(page_num),int(page_size)
        self.limit_str = 'limit %s,%s' % ((page_num - 1) * page_size, page_size)
    
    def set_order(self,sort_key,sort_type='ASC'):
        if sort_key and sort_type.lower() in ('asc','desc'):
            if 'order' in self.query_sql.strip()[-30:].lower():   
                self.order_str = ' ,%s %s' % (sort_key,sort_type)
            else:
                self.order_str = ' ORDER BY %s %s' % (sort_key,sort_type)
                
    def replace_mark_to_value(self,mark_name,value):
        self.query_sql = self.query_sql.replace(self.make_mark(mark_name),str(value))
            
    def make_mark(self,mark_name):
        return self.TAG_FORMAT % mark_name
    
    def get_query_sql(self):
        return '%s %s %s' % (Query.filter_sql(self.query_sql),self.order_str,self.limit_str)
    
    def get_count_sql(self):
        return 'select count(0) from (%s) newTable' % Query.filter_sql(self.query_sql)
    
    def has_mark(self,mark_name):
        return self.make_mark(mark_name) in self.query_sql
    
    def set_neibuhao(self,neibuhao_player_list=[]):   #设置内部号参数
        from .player import Player
        if self.has_mark('neibuhao'):
            self.params.update({"neibuhao":Player.get_inside_player_list()}) #传内部号的角色ID
    
    
    
class QueryAnalysis(SqlAnalysis):
    
    def __init__(self,query_model,params):
        self.query = query_model
        self.already_get_query_sql = False
        the_sql = self.query.sql or self.query.get_default_sql()
        super(QueryAnalysis,self).__init__(the_sql,params)
        self.mark_map.update(self.query.field_config)
        
    def get_tfoot_sql(self):
        '''获取tfoot的汇总sql
        '''
        assert self.already_get_query_sql ,'只能先使用get_query_sql 获取查询SQL'
        tmp_sql = self.query_sql  
        ftoot_sql = self.query.other_sql
        if ftoot_sql:
            self.query_sql = ftoot_sql
            self.query_sql_handle()
            ftoot_sql = self.query_sql
            self.query_sql = tmp_sql
        return ftoot_sql
        
    def get_query_sql(self):
        self.already_get_query_sql = True
        if self.query.order and not self.order_str:#如果没有排序设置默认查询排序
            self.set_order(self.query.order,self.query.order_type_str)
        return super(QueryAnalysis,self).get_query_sql() 
        
    def query_sql_handle(self):
        '''query_sql_handle 增加获取统计id 使用方法 <<统计名>>
        '''
        if re.search(r'<<\S*>>',self.query_sql) : #包含<<统计名>>标签
            statistic_names = DictDefine.get_dict_for_key('statistic_name',reverse=False)
            for k,v in statistic_names.iteritems():
                self.query_sql = self.query_sql.replace('<<%s>>' % v,str(k))
        return super(QueryAnalysis,self).query_sql_handle()    
        
    def has_mark(self,mark_name):
        return super(QueryAnalysis,self).has_mark(mark_name)
    
    def has_conditions(self):
        for k,v in self.query.field_config.iteritems():
            if v.get('search',''):
                return True

class QueryMenuMixin(object):
    
    def set_query_to_menu(self):
        '''设置查询权限
        '''
        query_menu_model,created = Menu.objects.get_or_create(name=self.name)
        if created:#第一次创建的查询创建一个Menu
            query_menu_model.url='/query/view/%s' % self.name
            parent_name = self.log_def.name
            root_model,_ = Menu.objects.get_or_create(name="查询权限")
            parent_model,_ = Menu.objects.get_or_create(name='[%s]' % parent_name,parent_id=root_model.id)
            parent_model.is_show = 1
            parent_model.is_log = 0
            parent_model.save()
            query_menu_model.is_log = query_menu_model.is_log or 0
            query_menu_model.is_show = query_menu_model.is_show or 0
            query_menu_model.parent_id = parent_model.id
            query_menu_model.save(using='write')


        
class Query(models.Model,BaseModelMixin,QueryMenuMixin):
    
    TYPE_CHOICES = ((0,'字典'),(1,'数据表'))
    
    log_key = models.CharField('表名',max_length=30,db_index=True,null=False)
    
    log_type = models.IntegerField(default=0)
    name = models.CharField('查询名称',max_length=100)
    select = models.CharField(max_length=200)
    where = models.CharField(max_length=500)
    group = models.CharField('用途分组',max_length=50)
    order = models.CharField(max_length=20)
    order_type = models.IntegerField(default=0)
    sql = models.TextField()
    other_sql = models.TextField(default='',null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    cache_validate = models.IntegerField(default=0,null=True)
    
    remark =  models.CharField('备注',max_length=1000)
    _field_config = models.TextField('查询字段定义',default="")
    template_name = models.CharField('模版名',max_length=32)
    
    _DEFAULT_FIELD_CONFIG = {"标记名":{"name":"参数名","dict":"","sort":False,"order_num":99,"multiple":False,"search":False,"merge_value":True}}

    __cache_config = None
    
    def save(self,*args,**kwargs):
        super(Query,self).save(*args,**kwargs)
        self.set_query_to_menu()
    
    
    def get_default_sql(self):
        ''' 默认SQL
        '''
        log_def =  self.log_def
        the_sql = '''SELECT %s FROM %s WHERE log_time  BETWEEN '{{sdate}}' AND '{{edate}}' ''' % (self.select,log_def.table_name)
        if self.where:
            the_sql += ' AND %s' % self.where
        if self.order:
            the_sql += ' ORDER BY %s %s' % (self.order,self.order_type_str)
        
        for field_name,config in log_def.config.items():
            verbose_name = config['verbose_name']
            if verbose_name:
                the_sql =  the_sql.replace(verbose_name,field_name)
        return the_sql
    
    @property
    def order_type_str(self):
        return 'DESC' if self.order_type == 1 else 'AESC'
    
    @CacheAttribute
    def log_def(self):
        return LogDefine.objects.get(key=self.log_key)
    
    @property
    def is_center_query(self):
        '''是否中央查询
        '''
        return self.log_def.status == LogDefine.Status.CENTER
    
    @CacheAttribute
    def selects(self):
        return [ f for f in self.select.split(',') if f]
    
    @property
    def field_config(self):
        '''字段定义 
        '''
        try:
            self.__cache_config  = self.__cache_config or json.loads(self._field_config) 
        except:
            print trace_msg()
            self.__cache_config =  self._DEFAULT_FIELD_CONFIG
            
        return self.__cache_config 
    
    @field_config.setter
    def field_config(self,obj_value):
        if isinstance(obj_value,dict):
            obj_value = json.dumps(obj_value,ensure_ascii=False)
        self._field_config = obj_value
    
    
    @classmethod
    def filter_sql(cls,sql):
        p = re.compile( '(update|delete|modify|lock[\s]+|drop|table)', re.I)
        sql = p.sub( '', sql)
        return sql
    
    @CacheAttribute
    def safe_sql(self):
        return self.__class__.filter_sql(self.sql)
    
    def __unicode__(self):
        return '%s' % self.name
    
    class Meta: 
        db_table = u'query_new'
        app_label = get_app_label()
 
filter_sql = Query.filter_sql
