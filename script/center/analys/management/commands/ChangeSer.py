#coding:utf-8
# 开服时间自动改状态进程&清白名单

from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser

from models.server import Server
from views.game.base import GMProtocol
from views.server.server import server_make
from django.db.models.base import ModelBase
import sys,os,datetime,time,json
import threading,traceback
from django.db.models import Q
from Queue import Queue
import datetime

import settings
settings.DEBUG = False



from django.db import connections

def keep_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:c.connection.connection.ping()
        except:c.close()


class Command(BaseCommand):
    '''检测服务器已删除状态,到开服时间自动改状态进程&清白名单
    '''

    help = '检测服务器已删除状态,开服时间自动改状态进程&清白名单'

    def handle(self, *args, **options):
        keep_connections()
        print u'检测服务器已删除状态,开服时间自动改状态进程&清白名单 开启:%s ' % datetime.datetime.now()

        while 1:
            keep_connections()
            
            try:
                now = datetime.datetime.now()
                ser_l = Server.objects.using('write').filter(status=-1)
                print u'>>>>>>>检测服务器状态'
                print u'>>>>>>>当前时间:%s'%now
                print u'>>>>>>>当前已删除状态服务器:%s'%ser_l
                if ser_l:
                    for s in ser_l:
                        create_time = s.create_time
                        dt = now - create_time
                        if dt.days == 0 and dt.seconds/60 > 0 and dt.seconds/60 < 3:
                            sid = int(s.id)
                            # gmp = GMProtocol(sid)
                            # result = gmp.modify_white_list([])
                            # if result == 0:
                            s.status = 4
                            s.commend = 1
                            s.last_time = datetime.datetime.now()
                            s.save()
                            if s.status == 4:
                                print u'%s-----%s服务器状态修改成爆满' %(now,sid)
                                server_make({})

                                print u'%s-----%s服务器白名单清空并生成服务器列表' %(now,sid)

								
            except Exception,e:
                traceback.print_exc()

            time.sleep(60)
