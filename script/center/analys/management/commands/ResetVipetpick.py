#coding:utf-8
# 自动重置VIP每日礼包进程

from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser

from models.server import Server
from views.game.base import GMProtocolBase
from django.db.models.base import ModelBase
import sys,os,datetime,time,json
import threading,traceback
from django.db.models import Q
from Queue import Queue

import settings
settings.DEBUG = False

from models.center import VipList
from django.db import connections

def keep_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:c.connection.connection.ping()
        except:c.close()


def waitToTomorrow():
    """Wait to tommorow 05:00 am"""
    tomorrow = datetime.datetime.replace(datetime.datetime.now() + datetime.timedelta(days=1),hour=5, minute=0, second=0)
    delta = tomorrow - datetime.datetime.now()
    print "距离明天5点还有" + str(delta.seconds) +'秒'
    return delta.seconds

class Command(BaseCommand):
    '''自动重置VIP每日礼包进程
    '''
    help = '自动重置VIP每日礼包进程'

    def handle(self, *args, **options):
        keep_connections()
        print '自动重置VIP每日礼包进程 开启:%s ' % datetime.datetime.now()
        tomorrow_seconds = waitToTomorrow()
        while 1:
            keep_connections()
            res = tomorrow_seconds - 3600
            if res > 0:
                time.sleep(3600)
                print "距离明天5点还有" + str(res) +'秒'
                tomorrow_seconds = res
                try:
                    cursor = connections['read'].cursor()
                    raw = cursor.execute("SELECT * FROM viplist WHERE everyday_type  = 2")
                    print '=============================',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if int(raw) == 0:
                        print '没有领取每日礼包记录.'

                    else:
                        print '已经领取每日礼包总数:' + str(raw)

                except Exception,e:
                    print traceback.print_exc()

                finally:
                    cursor.close()

            else:
                time.sleep(tomorrow_seconds)

                try:
                    cursor = connections['write'].cursor()
                    raw = cursor.execute("UPDATE viplist SET everyday_type  = 1 WHERE everyday_type  = 2 ")
                    print '=============================',datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if int(raw) == 0:
                        print '没有要重置的礼包'
                    else:
                        print 'ok,一共重置' + str(raw)

                    tomorrow_seconds = waitToTomorrow()

                except Exception,e:
                    print traceback.print_exc()

                finally:
                    cursor.close()

