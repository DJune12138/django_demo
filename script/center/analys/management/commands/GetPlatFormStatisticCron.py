#coding:utf-8
#获取各个游戏平台的统计数据定时进程
#
#流程
#    清空临时表 -> 获取数据 -> 写入临时表 -> 转移临时表数据
#
from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser
from django.db import connection,connections
from models.server import Server
import datetime,time
import traceback,os,sys
from util import convert_to_datetime,datetime_to_str,md5
from django.db import connection,connections
from models.server import Server
from models.base import close_connections
from models.platform import PlatForm
from models.statistic import Statistic
import urllib,urllib2,json
import MySQLdb
from views.base import get_static_root
from views.server.platform import update_channel_server_data
import calendar

def print_info(msg):
    print '[%s] %s' % (datetime.datetime.now(),msg)

class PlatFormStatisticExecute(object):
    
    LIMIT_NUM = 50000
    def __init__(self,sdate,edate,platform_model,pm):
        self.sdate_str = datetime_to_str(sdate)
        self.edate_str = datetime_to_str(edate)
        self.pm = pm
        self.platform_model = platform_model
        

    def make_post_params(self,offset=0):
        #限制时间范围
        post_params = {'sdate':self.sdate_str,
                       'edate':self.edate_str,
                       '_t':int(time.time())
                       }
        
        #限制统计类型
        if self.pm.statistics:
            post_params['type'] = ','.join(self.pm.statistics)
        if self.pm.is_create_time:
            
            post_params['is_create_time'] = 1
            
        #限制条目数
        post_params['offset'] = offset 
        post_params['limit'] = self.LIMIT_NUM 
        
        #设置签名
        post_params_str =  urllib.urlencode(post_params)
        app_key =self.platform_model.app_key
        sign = md5('%s%s' % (post_params_str,app_key)) 
        post_params_str = '%s&sign=%s' % (post_params_str,sign)
        return post_params_str
    
    def execute(self):
        address = self.platform_model.address
        start_num = 0
        i = 1
        finish_num = 0
        while 1:
            try:
                post_params = self.make_post_params(start_num)
                print_info( '%s?%s' %  (address,post_params))
                response = urllib2.urlopen(address, post_params, timeout=60)
                r_str = response.read()

                json_data = json.loads(r_str)
                tol_num = json_data.get('tol_num')
                finish_num += tol_num
                data_list = json_data.get('data')
                print_info( '%s 第  %s 次 插入 %s条数据' % (self.platform_model.name,i,tol_num))
                self.pm.insert_data_to_tmp_table(self,data_list)
                start_num += self.LIMIT_NUM
                if tol_num < self.LIMIT_NUM:break  #获取的数据小于限制的条目就表示获取完了
                i += 1
                
            except:
                traceback.print_exc()
                break
        
        return finish_num
    
class PlatFormStatisticManager(object):
    def __init__(self,sdate,edate,statistics,platform_keys=[],is_create_time=False):
        self.platforms = PlatForm.objects.filter(key__in=platform_keys) if platform_keys else  PlatForm.objects.all()
        self.statistics = [ str(x) for x in statistics]
        self.statistics_models_list = Statistic.objects.filter(id__in=[int(x) for x in self.statistics])
        self.sdate = sdate
        self.edate = edate
        self.center_con = Server.get_conn(0,connect_timeout=10)
        self.center_con.autocommit(False)
        
        self.is_create_time = is_create_time
        if self.is_create_time : #如果是按生成时间获取的 话,限制在开始时间内
            self.sdate = datetime.datetime(self.sdate.year,self.sdate.month,self.sdate.day,0,0,0,0)
            #self.edate = self.sdate + datetime.timedelta(days=1)
            

        
    def update_channel_server_data(self):
        '''获取各个平台的 渠道和服务器 json列表!
        '''
        for p in self.platforms:
            print_info('开始 获取 %s 的 渠道和服务器文件!' % (p.name))
            update_channel_server_data(p)


                
    def start(self):
        for p in self.platforms:
            self.truncate_tmp_table()
            pe = PlatFormStatisticExecute(self.sdate,self.edate,p,self)
            msg =  '开始 拉取 %s [%s] - [%s] (%s)的数据:' % (p.name,pe.sdate_str,pe.edate_str,self.statistics)
            print_info( msg)
            finish_num = pe.execute()
            delete_num = 0
            if not self.is_create_time: #按创建时间获取,不删就数据
                delete_num = self.delete_old_statistic_data(pe)
                print_info( '已经删除  %s 的 %s条 旧数据!' % (delete_num,p.name)  )
            print_info( '开始 转移 临时数据!')
            self.transfer_tmp_data()
            print_info( '%s 已拉取  %s 条数据' % (p.name,finish_num) )
            self.save_get_platform_result_log(pe,finish_num,delete_num)
            
    def save_get_platform_result_log(self,pe,finish_num,delete_num):
        insert_sql = ''' INSERT INTO {platfrom_result_log_table_name}(`log_type`,`log_time`,`log_name`,`log_now`,`log_previous`,`f1`,`f2`,`f6`)
        VALUES(0,now(),%s,%s,%s,%s,%s,%s)'''.format(platfrom_result_log_table_name=self.platfrom_result_log_table_name)
        statastic_names = ','.join([s.name for s in self.statistics_models_list])
        insert_list = [pe.platform_model.name,finish_num,delete_num,pe.sdate_str,pe.edate_str,statastic_names]
        cur = self.center_con.cursor()
        cur.execute(insert_sql,insert_list)
        self.center_con.commit()
    
    
    def __del__(self):
        try:self.center_con.close()
        except:pass
        
        
    def insert_data_to_tmp_table(self,pe,data_list):
        if data_list:
            sql = ''' INSERT INTO `{platfrom_result_tmp_table_name}`(`log_user`,`log_time`,`log_type`,`log_server`,`log_channel`,`log_tag`,`log_now`,`log_previous`,`log_data`,`log_result`,`f1`) 
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'{platfrom}')
                    '''.format(platfrom=pe.platform_model.key,platfrom_result_tmp_table_name=self.platfrom_result_tmp_table_name)
            
            cur = self.center_con.cursor()
            cur.executemany(sql,data_list)
            self.center_con.commit()
        
    def truncate_tmp_table(self):
        '''删除临时表的数据
        '''
        cur = self.center_con.cursor()
        print_info( '开始 清除 临时表!' )
        truncate_table_sql = 'Truncate table `%s`;'  % self.platfrom_result_tmp_table_name
        cur.execute(truncate_table_sql)
        self.center_con.commit()
    
    def delete_old_statistic_data(self,pe):
        '''删除旧的数据
        '''
        cur = self.center_con.cursor()

        delete_sql = '''DELETE FROM `%s` 
        WHERE log_time BETWEEN '{sdate}' AND '{edate}' AND f1='{platfrom}' 
        ''' % self.result_table_name
        
        delete_sql = delete_sql.format(sdate=pe.sdate_str, edate=pe.edate_str,platfrom=pe.platform_model.key) 
        if self.statistics:
            delete_sql = '%s AND log_type in (%s)' % (delete_sql,','.join(self.statistics)) 

        delete_num =  cur.execute(delete_sql)
        self.center_con.commit()
        return delete_num
    
    def transfer_tmp_data(self):
        '''转移插入的临时数据
        '''
        sql = ''' INSERT INTO `%s`(`log_type`,`log_user`,`log_name`,`log_server`,`log_channel`,`log_data`,`log_result`,`log_level`,`log_time`,`log_previous`,`log_now`,`log_tag`,`f1`) 
        SELECT * FROM %s ''' % (self.result_table_name,self.platfrom_result_tmp_table_name)
        
        cur = self.center_con.cursor()
        cur.execute(sql)
        self.center_con.commit()
      
    result_table_name = 'log_platform_result'
    platfrom_result_tmp_table_name = 'log_platform_result_tmp'
    platfrom_result_log_table_name = 'log_get_platform_result'
      
        
    @classmethod
    def create_center_platform_statistic_table(cls):
        
        #保存结果表
        platfrom_result_table_sql = '''CREATE TABLE IF NOT EXISTS `%s` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `log_type` int(11) NOT NULL,
  `log_user` int(11) DEFAULT NULL,
  `log_name` varchar(100) DEFAULT NULL,
  `log_server` int(11) DEFAULT NULL,
  `log_channel` int(11) DEFAULT NULL,
  `log_data` int(11) DEFAULT NULL,
  `log_result` int(11) DEFAULT NULL,
  `log_level` int(11) DEFAULT NULL,
  `log_time` datetime NOT NULL,
  `log_previous` varchar(200) DEFAULT NULL,
  `log_now` varchar(200) DEFAULT NULL,
  `log_tag` int(11) DEFAULT NULL,
  `f1` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`,`log_time`),
  KEY `log_platform_result_log_type` (`log_type`),
  KEY `log_platform_result_log_time` (`log_time`),
  KEY `log_platform_result_log_server` (`log_server`),
  KEY `log_platform_result_log_channel` (`log_channel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 
 PARTITION BY RANGE (year(log_time)) 
 (
 PARTITION p201x VALUES LESS THAN (2010),
 PARTITION p2010 VALUES LESS THAN (2011),
 PARTITION p2011 VALUES LESS THAN (2012),
 PARTITION p2012 VALUES LESS THAN (2013),
 PARTITION p2013 VALUES LESS THAN (2014),
 PARTITION p2014 VALUES LESS THAN (2015),
 PARTITION p2015 VALUES LESS THAN (2016),
 PARTITION p2016 VALUES LESS THAN (2017),
 PARTITION p2017 VALUES LESS THAN (2018),
 PARTITION p2018 VALUES LESS THAN (2019),
 PARTITION p2019 VALUES LESS THAN (2020),
 PARTITION p202x VALUES LESS THAN (MAXVALUE)
 ) ''' % cls.result_table_name
        #保存结果临时表
        platfrom_result_tmp_table_sql = '''
CREATE TABLE IF NOT EXISTS `%s` (
  `log_type` int(11) NOT NULL,
  `log_user` int(11) DEFAULT NULL,
  `log_name` varchar(100) DEFAULT NULL,
  `log_server` int(11) DEFAULT NULL,
  `log_channel` int(11) DEFAULT NULL,
  `log_data` int(11) DEFAULT NULL,
  `log_result` int(11) DEFAULT NULL,
  `log_level` int(11) DEFAULT NULL,
  `log_time` datetime NOT NULL,
  `log_previous` varchar(200) DEFAULT NULL,
  `log_now` varchar(200) DEFAULT NULL,
  `log_tag` int(11) DEFAULT NULL,
  `f1` varchar(100) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8   
''' % cls.platfrom_result_tmp_table_name
        #获取记录日志表
        platfrom_result_log_table_sql = '''
CREATE TABLE IF NOT EXISTS `%s`  like log_0_new
    ''' % cls.platfrom_result_log_table_name
    
        #创建保存数据的表和临时表
        
        conn  = Server.get_conn(0)
        cur = conn.cursor()
        try:cur.execute(platfrom_result_table_sql)
        except MySQLdb.Warning: pass
        try:cur.execute(platfrom_result_tmp_table_sql)
        except MySQLdb.Warning: pass
        try:cur.execute(platfrom_result_log_table_sql)
        except MySQLdb.Warning: pass
        conn.commit()
        conn.close()
     
def add_months(dt,months):
    month = dt.month - 1 + months
    year = dt.year + month / 12
    month = month % 12 + 1
    day = min(dt.day,calendar.monthrange(year,month)[1])
    return dt.replace(year=year, month=month, day=day)
        
class Command(BaseCommand):
    '''统计相关命令行
    '''
    help = '''定时拉取个平台的统计数据! python manage.py GetPlatFormStatisticCron -s '2015-01-01' -e '2015-01-01' '''

    option_list = BaseCommand.option_list + (
                  make_option('-s','--sdate',
                                dest='sdate', default='',
                                help='开始时间'
                                ),
                   make_option('-e','--edate',
                                dest='edate', default='',
                                help='结束时间'
                                ),
                   make_option('-p','--platforms',
                                dest='platforms', default='',
                                help='游戏平台标识'
                                ),
                   make_option('-t','--statistic_type',
                                dest='statistics', default='',
                                help='统计的项目'
                                ),
                   make_option('-c','--cron',action='store_true',
                                dest='cron', default=False,
                                help='定时任务'
                                ),
                   make_option('-g','--get_platform_channel_server_json_file',action='store_true',
                                dest='get_json_file', default=False,
                                help='获取各个平台的 渠道和服务器 json列表'
                                )
                                )
    
    def handle(self, *args, **options):
        try:
            #print options
            self.sdate = options.get('sdate','')
            self.edate = options.get('edate','') or self.sdate
            self.platforms = [s for s in options.get('platforms','').split(',') if s ]
            self.statistics = [int(s) for s in options.get('statistics','').split(',') if s ]
            is_create_time = False #options.get('is_create_time',False)
            is_get_json_file = options.get('get_json_file','')
            
            if options.get('cron'):
                self.cron_run()
                return
            PlatFormStatisticManager.create_center_platform_statistic_table()
            
            
                
            if self.sdate :
                sdate = convert_to_datetime(self.sdate)
                edate = convert_to_datetime(self.edate)                
                pm = PlatFormStatisticManager(sdate,edate,self.statistics,self.platforms)
                if is_get_json_file:
                    pm.update_channel_server_data()
                else:
                    pm.start()
        except:
            traceback.print_exc()
            
    def cron_run(self):
        print 'Start Cron'
        while True:
            now = datetime.datetime.now()
            if now.hour == 8 and now.minute == 1:#10:01 start
                try:
                    yesterday = now - datetime.timedelta(days=1)
                    sdate = datetime.datetime(yesterday.year,yesterday.month,yesterday.day,0,0,0,0)
                    edate =  datetime.datetime(sdate.year,sdate.month,sdate.day,23,59,59,0)
                    
                    if now.day == 1:      
                        print '[%s] 今天是1号 开始拉取 上月[%s] - [%s] 的数据 !' % (now,sdate,edate)
                        sdate = add_months(now,-1)                                                      # 如果是1号的话再次运行下上个月的数据
                        sdate = datetime.datetime(sdate.year,sdate.month,1,0,0,0,0)                     #上月第1天
                        the_month_last_day = calendar.monthrange(sdate.year, sdate.month)[1]
                        edate = datetime.datetime(sdate.year,sdate.month,the_month_last_day,23,59,59,0) #上月最后一天
                    
                    
                    statistic_models_list = Statistic.objects.filter(is_auto_execute=1)
                    
                    #不需要未来时间的数据统计项目
                    not_auto_exec_interval_statistic_models_list = statistic_models_list.filter(auto_exec_interval=0)
                        
                    not_auto_exec_interval_statistic_ids = [ s.id for s in not_auto_exec_interval_statistic_models_list]
                    pm = PlatFormStatisticManager(sdate,edate,not_auto_exec_interval_statistic_ids,[])
                    print_info('开始拉取昨天的数据! %s' % not_auto_exec_interval_statistic_ids)
                    pm.start()
                    #更新下渠道和服务器文件
                    pm.update_channel_server_data()
                    del pm

                    #需要未来时间的数据统计项目
                    has_auto_exec_interval_statistic_models_list = statistic_models_list.filter(auto_exec_interval__gt=0)

                    for s in has_auto_exec_interval_statistic_models_list:
                        
                        diff_days = -s.auto_exec_interval
                        _sdate = sdate + datetime.timedelta(days=diff_days)
                        print_info('开始 拉 %s [%s] - [%s] 的数据! *******************' % (s.name,_sdate,edate))
                        pm = PlatFormStatisticManager(_sdate,edate,[s.id],[])
                        pm.start()
                        del pm
                    close_connections()   #执行完必须关闭mysql连接,以免超时
                    print_info('拉取数据完成!===')
                except:
                    traceback.print_exc() 
                time.sleep(60)
            if now.hour % 2 == 0 and now.minute == 1:
                print '[%s] I am working !' % now
                
            time.sleep(59)