# -*- coding: utf-8 -*-
#
#统计管理类
#
#django 常用导入
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================


from django.db import models
from django.db import connection,connections
from models.channel import Channel
from models.server import Server
import datetime, time, json, calendar
from util import datetime_to_str,trace_msg,convert_to_datetime
from django.utils.datastructures import SortedDict 
from models.query import SqlAnalysis
from models.log import LogDefine
from settings import get_app_label
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)



class Statistic(models.Model,BaseModelMixin):
    STATUS_CHOICES = ((0, '结果数量数'), (1, '值求和'), (2, '求平均值'), (3, '求最大值'), (4, '求最小值'),)
    
    log_type = models.IntegerField()
    count_type = models.IntegerField(default=0, choices=STATUS_CHOICES) #统计类型：求和，求差，求平均
    name = models.CharField(max_length=200)
    field_name = models.CharField(max_length=50)    #统计字段
    where = models.CharField(max_length=50)
    sql = models.CharField(max_length=5000)
    exec_interval = models.IntegerField(default=0) #执行间隔，单位秒
    last_exec_time = models.DateTimeField(null=True, blank=True)
    is_auto_execute = models.IntegerField(default=1)
    auto_exec_interval = models.IntegerField(default=0) #执行间隔，单位秒
    remark = models.CharField(max_length=1000, blank=True)
    result_data = models.CharField(max_length=200, blank=True)
    
    @CacheAttribute
    def log_def(self):
        return LogDefine.objects.get(id=self.log_type)
    
    def is_center(self):
        return self.log_def.status == LogDefine.Status.CENTER
    
    def __unicode__(self):
        return '%s' % self.name

    def last_exec_time_str(self):
        return datetime_to_str(self.last_exec_time)
        
        
    def get_result_json(self):
        if self.result_data != '' and self.result_data != None:
            the_json = json.loads(self.result_data)
            the_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            if the_date == the_json['date']:
                return the_json
        
        #处理,昨天,前天,本周,上月同一天
        today = datetime.date.today()
        last_day = today.day
        
        #当前月份天数
        current_month_days = calendar.monthrange(today.year, today.month)[1]
        if current_month_days < last_day:
            last_day = current_month_days
        
        now_date = datetime.datetime.now()
        
        list_date = [(now_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                     (now_date - datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                     (now_date - datetime.timedelta(weeks=1)).strftime('%Y-%m-%d'),
                     (now_date - datetime.timedelta(days=current_month_days)).strftime('%Y-%m-%d')]
        
        query_sql = 'select result_time,sum(result) from result where statistic_id=%d and result_time in("%s") group by result_time desc limit 10' % (self.id, '","'.join(list_date))
        cursor = connection.cursor()
        cursor.execute(query_sql) 
        list_record = cursor.fetchall() 
        #cursor.close()
        #list_record = Result.objects.filter(statistic__id=self.id,create_time__in=list_date).order_by('-create_time')
        new_json = {}
        new_json['date'] = list_date[0]
        
        
        the_value = 0.0
       
        for item_record in list_record:
            print item_record
            item_date = item_record[0].strftime('%Y-%m-%d')
            tmp = 0
            if float(item_record[1]) != 0:
                tmp = (the_value / float(item_record[1]) - 1)
                
            if item_date == list_date[0]: 
                the_value = int(item_record[1])
                new_json['default'] = '%d' % the_value
            elif item_date == list_date[1]: 
                new_json['day'] = '%.2f' % (tmp * 100)
            elif item_date == list_date[2]: 
                new_json['week'] = '%.2f' % (tmp * 100)
            elif item_date == list_date[3]: 
                new_json['month'] = '%.2f' % (tmp * 100)
                
        self.result_data = str(new_json).replace('\'', '"')
        self.save(using='write') 
        return new_json

    class Meta: 
        db_table = u'statistic_new'
        app_label = get_app_label()
        ordering = ('-last_exec_time',)

StatisticNew = Statistic
#class Result(models.Model):
#    statistic = models.ForeignKey(Statistic)
#    server = models.ForeignKey(Server)
#    channel = models.ForeignKey(Channel)
#    result = models.FloatField()
#    create_time = models.DateTimeField()
#    result_time = models.DateTimeField()


class Result(models.Model):
    statistic_id = models.IntegerField('统计ID')
    server_id = models.IntegerField('服务ID')
    channel_id = models.IntegerField('渠道ID')
    tag = models.IntegerField('标签')
    result = models.FloatField('结果值')
    create_time = models.DateTimeField('创建时间')
    result_time = models.DateTimeField('结果时间')
    
    def result_time_int(self):
        return int(time.mktime(self.result_time.timetuple()) * 1000)

    def result_time_str(self):
        return datetime_to_str(self.result_time)
    
    def __unicode__(self):
        return '%s' % self.statistic.name

    def cmp_time(self,days):
        time_slot = 86400000
        if days >= 8*24:
            time_slot = 30 * 86400000
        elif days >= 4*24:
            time_slot = 14 * 86400000
        elif days >= 2*24:
            time_slot = 7 * 86400000
        elif days >= 24:
            time_slot = 2 * 86400000
        return time_slot

    def get_month(self,sdate,edate):
        month_list = []
        sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m')
        edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m')
        month_list.append(sdate)
        print sdate,edate
        diff = (int(datetime.datetime.strptime(edate, '%Y-%m').strftime('%Y')) - int(datetime.datetime.strptime(sdate, '%Y-%m').strftime('%Y'))) *12 + (int(datetime.datetime.strptime(edate, '%Y-%m').strftime('%m')) - int(datetime.datetime.strptime(sdate, '%Y-%m').strftime('%m')))
        print diff
        temp_date = sdate.split("-")
        print temp_date
        for i in range(1,diff):
            month_list.append(self.datetime_offset_by_month(datetime.date(int(temp_date[0]),int(temp_date[1]),1), i))
        month_list.append(edate)
        return month_list
    
    def get_year(self,sdate,edate):
        year_list = []
        sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y')
        edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y')
        diff = int(edate) - int(sdate)
        for i in range(1,diff):
            year_list.append(int(sdate)+int(i))
        year_list.append(sdate)
        return year_list

    def datetime_offset_by_month(self,datetime1, n = 1):
        one_day = datetime.timedelta(days = 1)
    
        q,r = divmod(datetime1.month + n, 12)
    
        datetime2 = datetime.datetime(datetime1.year + q, r + 1, 1) - one_day

        if datetime1.month != (datetime1 + one_day).month:
            return datetime2

        if datetime1.day >= datetime2.day:
            return datetime2
        
        return datetime2.replace(day = datetime1.day).strftime("%Y-%m")
          
    class Meta: 
        db_table = u'result'
        ordering = ('-id',)
        app_label = get_app_label()
    
    
class QueryResult(models.Model):
    name = models.CharField(u'查询名称', max_length=100)
    remark = models.CharField(u'查询说明', max_length=200)
    statistic = models.ManyToManyField(Statistic)
    
    class Meta: 
        db_table = u'query_result'
        app_label = get_app_label()
    
