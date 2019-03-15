#coding:utf-8
# 自动开启活动的守护进程

from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser

from models.server import Server
from models.game import Activity
from views.game.base import GMProtocolBase
from django.db.models.base import ModelBase
import sys,os,datetime,time,json
import threading,traceback

from util import convert_to_datetime
from util.threadpoll import ThreadPool
from django.db import transaction
from django.db.models import Q
from Queue import Queue

import settings
settings.DEBUG = False
from views.game.activity import activity_action

from django.db import connections




def keep_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:c.connection.connection.ping()
        except:c.close()
        
class ActivityExcute(threading.Thread):
    def __init__(self):
        self.work_queue = Queue()
        super(ActivityExcute,self).__init__()
        self.setDaemon(True)
        
    def run(self):
        while 1:
            activity_action_tup = self.work_queue.get()
            now = datetime.datetime.now()
            try:connections['default'].connection.ping()
            except:connections['default'].close()
            keep_connections()
            if len(activity_action_tup) == 2:
                activity_model,action = activity_action_tup
                for s in activity_model.server.all():
                    result = activity_action(activity_model,action,s.id,activity_model.msg,-999,force_log=True)
                    print '[%s] - %s %s(%s) - %s' % (now,activity_model.name,s.name,s.id,result['msg'])

class Command(BaseCommand):
    '''游戏活动自动开启
    '''
    help = '游戏活动开启守护进程'
        
    def handle(self, *args, **options):
        activity_excute = ActivityExcute()
        activity_excute.start()

        activity_auto_on_list = Activity.AUTO_ON_LIST
        activity_auto_off_list =  Activity.AUTO_OFF_LIST
        print u'自动开启的活动列表:'
        for activity_name in activity_auto_on_list:
            print activity_name
        print u'自动关闭的活动列表:'    
        for activity_name in activity_auto_off_list:
            print activity_name
        while True:
            now = datetime.datetime.now()
            sdate = datetime.datetime(now.year,now.month,now.day,now.hour,now.minute,0)
            edate = datetime.datetime(now.year,now.month,now.day,now.hour,now.minute,59)
            base_query = Q(is_auto=1)
            qeury_on = base_query & Q(sdate__range=[sdate,edate]) & Q(type__in=activity_auto_on_list) & Q(status=0)

            query_off = Q(is_auto_off=1) & Q(edate__range=[sdate,edate]) & Q(type__in=activity_auto_off_list) 
            keep_connections()
            try:
                activity_on_list = Activity.objects.prefetch_related('server').filter(qeury_on)

                activity_off_list = Activity.objects.prefetch_related('server').filter(query_off)
                for a in activity_on_list:
                    print u"开始开启:",a.name
                    activity_excute.work_queue.put((a,'on'))
                    print u"开启结束"
                for a in activity_off_list:
                    print u"开始关闭:",a.name
                    activity_excute.work_queue.put((a,'off'))
                    print u'关闭结束'
                
            except:
                traceback.print_exc()
            try:
                change_status_query = Q(status__in=[0,2,3]) & Q(edate__lt=sdate)
                activity_change_status_list = Activity.objects.filter(change_status_query)
                for a in activity_change_status_list:
                    print "*"*50
                    print u'当前时间为:%s'%sdate
                    print u'%s 正在更改状态:活动结束时间为:%s'%(a.name,a.edate)
                    print '*'*50
                    a.status = 1
                    a.save(using="write")
            except BaseException as e:
                print "error:%s"%e

            if now.hour % 12 == 0 and now.minute==1:
                print '[%s] 工作中 sleep 60' % now ,'-' * 40
            
            time.sleep(60)
            
        
        
