#! /usr/bin/python
# -*- coding: utf-8 -*-
from views.base import GlobalPathCfg, mkdir
from models.log import LogDefine
from cache.log_cache import get_center_log, get_statistic
import datetime
import os
from settings import STATIC_ROOT,STATIC_URL

def the_log_in_center(log_def):
    '''@log_def 支持int 也可以是一个 log_define '''
    if type(log_def) == int or type(log_def) == long:
        center_log_list = get_center_log()
        if None != center_log_list:
            for item in center_log_list:
                if item.id == log_def:
                    return True
    else:
        if log_def.status == LogDefine.Status.CENTER:
            return True
    return False

def the_statistic_in_center(statistic):
    '''@statistic 支持int 也可以是一个 statistic对象 '''
    if type(statistic) == int or type(statistic) == long:
        statistic = get_statistic(statistic)
    return the_log_in_center(statistic.log_type)

field_types = [u'字符串', u'时间', u'日期', u'小时', u'整数', u'小数', u'百分数']

def format_value(field_def, value):
    field_type = field_def.field_type
    if field_type == u'时间':
        try:
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        except:
            value = float(value)
            value = datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
        
        
    elif field_type == u'日期':
        value = value.strftime('%Y-%m-%d')
    elif field_type == u'小时':
        value = value.strftime('%Y-%m-%d %H')
    elif field_type == u'整数':
        value = int(value)
    elif field_type == u'小数':
        value = float(value)
    elif field_type == u'百分数':
        value = '%s%%' % (value * 100)
    return value


            