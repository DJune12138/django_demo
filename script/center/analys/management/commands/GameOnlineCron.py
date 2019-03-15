#coding:utf-8
#获取游戏定时在线数据


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


from django.db import connection,connections

connection_list = [connections['default'],connections['read'],connections['write']]

def close_connections():
    for c in connection_list:
        try:
            c.close()
        except:
            pass
        
THREAD_POLL_NUMS = 5
        
_META_LOG_TABLE_NAME = 'log_0_new'
_CENTER_ONLIE_TABLE_NAME = 'log_all_online'
_SERVER_ONLIE_TABLE_NAME = 'log_playing'
_INTERVAL_SEC = 600

class InsertOnlineData(object):
    '''插入中央在线数据
    '''
    
    delete_sql_format = '''DELETE FROM {tablename} WHERE log_server={server_id} AND log_time BETWEEN '{sdate}' AND '{edate}' '''
    insert_sql_format = '''INSERT INTO {tablename}(`log_type`,`log_time`,`log_server`,`log_result`) VALUES(0,%s,%s,%s) '''
    select_sql_format = '''SELECT log_time,{server_id},CONVERT(log_now,signed)  FROM {tablename} where log_time BETWEEN '{sdate}' AND '{edate}' '''
    
    def __init__(self,sdate_str,edate_str,sid,manager):
        self.manager = manager
        self.sid = int(sid)
        self.server = Server.objects.get(id=sid)
        self.server_conn = self.server.mysql_conn()
        self.sdate_str = sdate_str
        self.edate_str = edate_str
        self.delete_sql = self.delete_sql_format.format(tablename=_CENTER_ONLIE_TABLE_NAME,
                                                        server_id=self.sid,
                                                        sdate=self.sdate_str,
                                                        edate=self.edate_str
                                                        )
        self.select_sql = self.select_sql_format.format(tablename=_SERVER_ONLIE_TABLE_NAME,
                                                        server_id=self.sid,
                                                        sdate=self.sdate_str,
                                                        edate=self.edate_str
                                                        )
        

    def insert_online_data(self,server_onlie_data):
        cur = self.manager.center_conn.cursor()
        cur.execute(self.delete_sql)
        insert_sql_format = self.insert_sql_format.format(tablename=_CENTER_ONLIE_TABLE_NAME)
        cur.executemany(insert_sql_format,server_onlie_data)

        
    def get_server_online_data(self):
        cur = self.server_conn.cursor()
        cur.execute(self.select_sql)
        record = cur.fetchall()
        self.server_conn.close()
        return record
        
    def start(self):
        record = self.get_server_online_data()
        print '[%s] %s(%s) query...(%s)' % (datetime.datetime.now(),self.server.name,self.server.id,len(record))
        if record:
            try:
                self.manager.INSERT_LOCK.acquire()
                self.insert_online_data(record)
                print '[%s] %s(%s) done!' % (datetime.datetime.now(),self.server.name,self.server.id)
            except:
                traceback.print_exc()
            finally:
                self.manager.INSERT_LOCK.release()

class InsertOnlineDateManager(object):
    
    def __init__(self,sdate=None,edate=None,sids=[]):
        if sdate == edate:
            now = datetime.datetime.now()
            edate = edate or now
            the_5min_ago = edate - datetime.timedelta(seconds=_INTERVAL_SEC)
            sdate = the_5min_ago
        self.INSERT_LOCK = threading.Lock()     
        self.sdate = datetime_to_str(sdate)
        self.edate = datetime_to_str(edate)
        
        self.servers = Server.objects.all() if not sids else  Server.objects.filter(id__in=sids)
        print '[%s] - [%s]' % (self.sdate,self.edate)
        self.center_conn = Server.get_conn(0)
        
        
    @classmethod
    def create_center_table(cls):
        sql = 'create table IF NOT EXISTS `{tablename}` like {meta_log_tablename}'.format(tablename=_CENTER_ONLIE_TABLE_NAME,meta_log_tablename=_META_LOG_TABLE_NAME)
        try:
            con = Server.get_conn(0)
            cur = con.cursor()
            cur.execute(sql)
            con.close()
        except:
            pass
        
    def run(self):

        T = ThreadPool(THREAD_POLL_NUMS)
        for s in self.servers:
            try:
                insert_online_data = InsertOnlineData(self.sdate,self.edate,s.id,self)
                T.append(insert_online_data.start,())   
                
            except:
                traceback.print_exc()
        T.close()
        T.join()
        del T
        
    def __del__(self):
        try:
            self.center_conn.close()
        except:
            pass
        
InsertOnlineDateManager.create_center_table()      

class Command(BaseCommand):
    '''统计相关命令行
    '''
    help = '定时拉取全服在线数据!'

    option_list = BaseCommand.option_list + (
                  make_option('-s','--sdate',
                                dest='sdate', default='',
                                help='补在线数据的开始时间'
                                ),
                   make_option('-e','--edate',
                                dest='edate', default='',
                                help='补在线数据的结束时间'
                                ),
                   make_option('-S','--server_ids',
                                dest='server_ids', default='',
                                help='服务器ID'
                                ),
                   make_option('-c','--cron',action='store_true',
                                dest='cron', default=False,
                                help='定时任务'
                                )
                                             )
    
    def __init__(self):
        self.sdate = self.edate = None
        self.server_ids = self.statistic_ids = []
        super(Command, self).__init__()
        
    def handle(self, *args, **options):
        try:
            self.edate = options.get('edate','') or datetime_to_str(datetime.datetime.now())
            self.sdate = options.get('sdate','') or self.edate

            self.server_ids = [s for s in options.get('server_ids','').split(',') if s ]

            
            if options.get('cron'):
                self.cron_run()
                return
            
            if self.edate :
                sdate = convert_to_datetime(self.sdate)
                edate = convert_to_datetime(self.edate)                
                im = InsertOnlineDateManager(sdate,edate,self.server_ids)
                im.run()
                close_connections()
            else:
                print '没有提供参数！'
        except:
            traceback.print_exc()
            
    def cron_run(self):
        print 'Start Cron'
        while 1:
            now = datetime.datetime.now()
            try:
                if now.hour == 1 and now.minute<=10 : #每天1点补充昨天全部数据
                    sdate = now - datetime.timedelta(days=1)
                    edate = now
                    im = InsertOnlineDateManager(sdate,edate)
                else:
                    im = InsertOnlineDateManager()
                im.run()
                del im
                close_connections()   #执行完必须关闭mysql连接,以免超时
            except:
                pass 

            time.sleep(_INTERVAL_SEC)
            