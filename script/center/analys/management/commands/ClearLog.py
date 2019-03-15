#coding:utf-8
#定时清理分服log数据
# 1:log_chat,2:log_battle_rank


from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser
from django.db import connection,connections
from models.center import Server
import datetime
import time
import traceback
from util import convert_to_datetime,datetime_to_str
from util.threadpoll import ThreadPool
import threading

class Command(BaseCommand):
    '''定时清理分服Log数据开启
    '''
    help = '定时清理Log数据进程'

    def handle(self,*args,**options):
        clear_map = {"log_chat":{"period":3},
                     "log_battle_rank":{"period":7}}

        while True:
            try:
                servers = Server.objects.all()
                err_msg = ""
                for server in servers:
                    conn = Server.get_conn(server.id)
                    for logName,logArgs in clear_map.iteritems():
                        sql = "delete from %s where datediff(curdate(),log_time) >= %s"%(logName,logArgs["period"])
                        print '-'*40
                        print sql
                        print '-'*40
                        cursor = conn.cursor()
                        cursor.execute(sql)
                        cursor.close()
                    if not err_msg:
                        print u'%s:%s数据库清理完成!'%(datetime.datetime.now(),server.name)
            except BaseException as e:
                print u'数据库连接错误.%s'%e
            #休半天
            time.sleep(43200)



