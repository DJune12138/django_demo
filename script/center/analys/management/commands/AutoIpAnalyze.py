#coding:utf-8
#自动将 为游戏log_check_user表的ip地域解析的

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


#def activity_action(activity_model,action,server_id,msg,admin_id,return_json=False):

class ActivityExcute(threading.Thread):
    def __init__(self):
        self.work_queue = Queue()
        super(ActivityExcute,self).__init__()
        self.setDaemon(True)
        
    def run(self):
        while 1:
            activity_action_tup = self.work_queue.get()
            now = datetime.datetime.now()
            print activity_action_tup
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
        while True:
            now = datetime.datetime.now()
            sdate = datetime.datetime(now.year,now.month,now.day,now.hour,now.minute,0)
            edate = datetime.datetime(now.year,now.month,now.day,now.hour,now.minute,59)
            qeury_on = Q(sdate__range=[sdate,edate]) 
            query_off = Q(edate__range=[sdate,edate])
            try:connections['default'].connection.ping()
            except:connections['default'].close()
            try:
                activity_on_list = Activity.objects.prefetch_related('server').filter(qeury_on).filter(is_auto=1)
                #暂时不用自动关
                #activity_off_list = Activity.objects.prefetch_related('server').filter(query_off).filter(is_auto=1)
                for a in activity_on_list:
                    activity_excute.work_queue.put((a,'on'))
#                for a in activity_off_list:
#                    activity_excute.work_queue.put((a,'off'))
            except:
                traceback.print_exc()
            if now.hour % 4 == 0 and now.minute==1:
                print '[%s] 工作中 sleep 60' % now ,'-' * 40
            time.sleep(60 * 30)
            
        
        