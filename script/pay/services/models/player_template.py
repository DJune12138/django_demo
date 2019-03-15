# -*- coding: utf-8 -*-


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
from .log import Log




class PlayerTemplate(models.Model,BaseModelMixin):
    '''角色模版
    '''
    name = models.CharField('模版名',max_length=50,blank=True,null=True,default='')
    remark = models.CharField('备注',max_length=500,blank=True,null=True,default='')
    json_data = JSONField('模版数据',default='{}')
    
    
    class Meta: 
        db_table = u'player_template'
        app_label = get_app_label()
        ordering = ('-id',)


