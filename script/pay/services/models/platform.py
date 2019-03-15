# -*- coding: utf-8 -*-

from django.db import models
from django.db import connection,connections
from django.core.management.color import no_style

from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)

from util import datetime_to_str,trace_msg

import datetime
import json
import traceback
from models.resource import Resource
import json
from settings import DATABASES
from settings import get_app_label



class PlatForm(models.Model,BaseModelMixin):
    '''平台模型
    '''

    client_ver = models.CharField(u'针对客户端版本',max_length=500,default='')
    name = models.CharField(u'平台名',max_length=20)
    key = models.CharField(u'平台名标识',max_length=20)
    app_key = models.CharField(u'平台钥匙',max_length=50)
    address = models.CharField(u'平台地址',max_length=200)
    channel_address = models.CharField(u'获取平台渠道地址',max_length=200,default='')
    server_address = models.CharField(u'获取平台服务器地址',max_length=200,default='')
    remark =  models.CharField(u'备注',max_length=500)
    time_zone = models.IntegerField('时区',default=8,null=False)
    
    class Meta: 
        db_table = u'game_platform'
        ordering = ('key',)
        app_label = get_app_label()


Resource.register('platform',PlatForm)