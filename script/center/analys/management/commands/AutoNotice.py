#coding:utf-8
# 自动更新公告进程

# from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand
from optparse import make_option

# from models.server import Server
# from views.game.base import GMProtocolBase
# from django.db.models.base import ModelBase
import sys,os,datetime,time,json
import traceback


import settings
settings.DEBUG = False

from views.server.notice import create_server_notice
from django.db import connections

def keep_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:c.connection.connection.ping()
        except:c.close()

class Command(BaseCommand):
    '''公告自动生成进程
    '''
    help = '公告自动生成进程'
    option_list = BaseCommand.option_list + (
                   make_option('-c','--cron',action='store_true',
                                dest='cron', default=False,
                                help='定时任务'
                                ),

                                )
    def handle(self, *args, **options):
        print '公告自动生成进程 开启:%s ' % datetime.datetime.now()
        if options.get('cron'):
            while 1:
                try:
                    keep_connections()
                    create_server_notice()
                except:
                    traceback.print_exc()
                keep_connections()
                time.sleep(60)
            
        else:
            create_server_notice()
        