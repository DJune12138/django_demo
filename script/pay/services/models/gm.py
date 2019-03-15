# coding=utf-8

from django.db import models
import json
from settings import get_app_label

class GMDefine(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField('GM协议描述',max_length=200)
    url = models.CharField(max_length=50)
    params = models.CharField('GM参数定义',max_length=6000,default='{}')
    result_type = models.CharField(max_length=20)
    result_define = models.CharField('返回定义',max_length=6000,default='{}')
    flag = models.CharField(max_length=100)
    
    def get_req_type(self):
        '''获取gm协议号
        '''
        return  int(self.def_params.get('req_type','') or self.id)
    
    @property
    def def_params(self):
        def_params = {} 
        try:
            def_params = json.loads(self.params)
            for k,v in def_params:
                value_map = v.get('value_map','')
                if value_map:
                    value_map = json.loads(value_map)
                    def_params[v]['value_map'] = value_map
        except:
            pass
        return def_params
    
    @property
    def def_result(self):
        def_result = {} 
        try:
            def_result = json.loads(self.result_define)
        except:
            pass
        return def_result
        
        
    class Meta:
        db_table = u'def_gm'
        app_label = get_app_label()