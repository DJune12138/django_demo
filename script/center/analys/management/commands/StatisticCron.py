#coding:utf-8
#统计的定时任务


from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser
from django.db import connection,connections
from models.server import Server
from models.statistic import Statistic
from views.log.statistic_module import StatisticManager
import datetime
import time
import traceback
from util import convert_to_datetime
from django.db import connection,connections
import calendar
connection_list = [connection,connections['read'],connections['write']]

def add_months(dt,months):
    month = dt.month - 1 + months
    year = dt.year + month / 12
    month = month % 12 + 1
    day = min(dt.day,calendar.monthrange(year,month)[1])
    return dt.replace(year=year, month=month, day=day)

def close_connections():
    for c in connection_list:
        try:
            c.close()
        except:
            pass

def keep_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:c.connection.connection.ping()
        except:c.close()

class Command(BaseCommand):
    '''统计相关命令行
    '''
    help = '运行定时统计任务!'

    option_list = BaseCommand.option_list + (
                  make_option('-s','--sdate',
                                dest='sdate', default='',
                                help='开始时间'
                                ),
                   make_option('-e','--edate',
                                dest='edate', default='',
                                help='结束时间'
                                ),
                   make_option('-S','--server_ids',
                                dest='server_ids', default='',
                                help='服务器ID'
                                ),
                   make_option('-t','--statistic_ids',
                                dest='statistic_ids', default='',
                                help='需要统计的ID列表,逗号隔开'
                                ),
                   make_option('-c','--cron',action='store_true',
                                dest='cron', default=False,
                                help='定时任务'
                                ),
                   make_option('-p','--print',action='store_true',
                                dest='print', default=False,
                                help='打印统计项目'
                                )
                                            )
    
    def __init__(self):
        self.sdate = self.edate = None
        self.server_ids = self.statistic_ids = []
        super(Command, self).__init__()
        
    def get_date_list_from_month(self,sdate,edate):
        date_list = []
        if (edate-sdate).days>28:
            while sdate<edate:
                tmp_edate = add_months(sdate,1)
                if tmp_edate > edate:
                    tmp_edate = edate
                date_list.append((sdate,tmp_edate + datetime.timedelta(seconds=-1)))
                sdate = tmp_edate
        else:
            date_list.append((sdate,edate))
            
        return date_list
        
    def handle(self, *args, **options):
        keep_connections()
        try:
            print options
            self.sdate = options.get('sdate','')
            self.edate = options.get('edate','') or self.sdate
            self.server_ids = [s for s in options.get('server_ids','').split(',') if s ]
            self.statistic_ids = [s for s in options.get('statistic_ids','').split(',') if s]
            
            
            if options.get('print',''):
                print '-'*3,'统计列表','-'*3
                for s in Statistic.objects.all().order_by('log_type'):
                    print '%2s :%s' % (s.id,s.name)
                print 
                return 
            
            if options.get('cron'):
                self.cron_run()
                return
            
            if self.sdate :
                
                sdate = convert_to_datetime(self.sdate)
                edate = convert_to_datetime(self.edate)      
                
                date_list = self.get_date_list_from_month(sdate, edate)
                for i,(s,e) in enumerate(date_list):
                    print '[%s] 第  %s 次执行 统计 时间  %s -%s ' % (datetime.datetime.now(),i+1,s,e)
                    sm = StatisticManager(s,e,self.statistic_ids,self.server_ids)
                    sm.start_update()
                    print '[%s] 第  %s 次执行 统计 时间  %s -%s 完成!' % (datetime.datetime.now(),i+1,s,e)
        except:
            traceback.print_exc()
            
    def cron_run(self):
        print 'Start Cron'

        while True:
            keep_connections()
            now = datetime.datetime.now()
            if now.hour == 1 and now.minute == 1:#01:01 start
                try:
                    if now.day == 1:      
                        print '[%s] % running  previous month data' % now
                        sdate = add_months(now,-1)                                                      # 如果是1号的话再次运行下上个月的数据
                        sdate = datetime.datetime(sdate.year,sdate.month,1,0,0,0,0)                     #上月第1天
                        the_month_last_day = calendar.monthrange(sdate.year, sdate.month)[1]
                        edate = datetime.datetime(sdate.year,sdate.month,the_month_last_day,23,59,59,0) #上月最后一天
                        statistic_ids = Statistic.objects.filter(auto_exec_interval=0).values_list('id', flat=True)
                        sm = StatisticManager(sdate, edate, statistic_ids, [], use_auto_exec_interval=True)
                    else:

                        sdate =  edate = now + datetime.timedelta(days=-1)
                        sm = StatisticManager(sdate,edate,[],[],use_auto_exec_interval=True)

                    sm.start_update()
                    del sm

                except:
                    traceback.print_exc() 
                    
            elif now.hour % 1 == 0 and now.minute == 1:#每x小时更新 一次当天数据
                try:
                    sdate = edate = now
                    statistic_ids = Statistic.objects.filter(auto_exec_interval=0).values_list('id', flat=True)
                    sm = StatisticManager(sdate,edate,statistic_ids,[],use_auto_exec_interval=False)
                    sm.start_update()
                    del sm
                except:
                    traceback.print_exc()  
                print '[%s] I am working !' % now

            elif now.hour % 1 == 0 and now.minute == 30:#每X小时更新 一次当天数据
                try:
                    sdate =  edate = now
                    statistic_ids = Statistic.objects.filter(auto_exec_interval=0).values_list('id', flat=True)
                    sm = StatisticManager(sdate,edate,statistic_ids,[],use_auto_exec_interval=False)
                    sm.start_update()
                    del sm
                except:
                    traceback.print_exc()
                print '[%s] I am working !' % now
            
            time.sleep(40)
            
            