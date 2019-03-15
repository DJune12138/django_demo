#!/usr/bin/env python
#coding: utf-8
#游爱数据定时备份计划
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import codecs
import os
import shutil
_op = os.path.dirname


cwdir = _op(os.path.abspath(__file__))
project_path =  _op(_op(_op(os.path.abspath(__file__))))
app_path = _op(project_path)

sys.path.insert(0, project_path)
sys.path.insert(0, app_path)

os.chdir(project_path)
print os.getcwd()

try:
    os.environ['DJANGO_SETTINGS_MODULE'] ='settings'
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)
except:
    os.environ['DJANGO_SETTINGS_MODULE'] ='settings'
    import settings

import gc
import MySQLdb
import datetime
import time
import traceback
try:
    from models.center import Server,Channel,Player
    from logging_config import TimedRotatingLogger
except:
    from models.server import Server
    from models.channel import Channel
    from models.player import Player
    from util.logging_config import TimedRotatingLogger
    
from util import trace_msg
from util.post_message import post_msg
from util.threadpoll import ThreadPool
from django.db import connection,connections
from django.core.management.color import no_style
import traceback
import json
import pickle

import threading
connection_list = [connections['default'],connections['read'],connections['write']]

def close_connections():
    for c in connection_list:
        try:
            c.close()
        except:
            pass

THREAD_POLL_NUMS = 5

_log = TimedRotatingLogger(os.path.split(__file__)[1])
PREFIX = settings.PREFIX
exec 'from %s import Query_Types,PREFIX,update_dicts,SQL,BaseQuery,SAVE_DIR' % PREFIX


IgnoreServerIdList = []
class ServerManager(object):
    '''服务器管理者
    '''
    def __init__(self):
        self.done_server_map = {}
        self.done_file_name = 'done_server.list'
        self.update_server_config()
        self.load_done_server()
    def ignore_server(self,o):
        ignore_key_word = ['test','跨服','审核','審核','跨服']
        return  o.id in IgnoreServerIdList or  o.status ==-1  or \
            filter(lambda x:x in o.name.lower(),ignore_key_word).__len__()>0
              
        
    def update_server_config(self):
        '''更新服务器配置'''
        self.normal_servers = {}

        self.ignore_servers = {}
        self.err_servers = {}

        for o in Server.objects.all():
            try:
                o.err_msg = ''
                o.mysql_cf = self._get_server_mysql_address(o)
                o.master_id = o.get_master_id()
                if self.ignore_server(o):

                    self.ignore_servers[int(o.id)] = o
                else:
                    self.normal_servers[int(o.id)] = o
            except Exception,e:
                #traceback.print_exc()
                o.err_msg = str(e)
                self.err_servers[int(o.id)] = o
                
    def _get_server_mysql_address(self,o):
        '''获取mysql地址配置'''
        log_db_config = json.loads(o.log_db_config)
        _cf = {'host':log_db_config['host'],
               'user':log_db_config['user'],
               'port':int(log_db_config.get('port',3306)),
               'db':log_db_config['db'],
               'charset':'utf8',
               'passwd':log_db_config['password'],
               'connect_timeout':10,
               'use_unicode':False
            }
        return _cf
    
    def get_server(self,sid):
        sid = int(sid)
        try:
            return self.servers[int(sid)]
        except:
            traceback.print_exc()
            
    def get_conn(self,sid):
        conn = None
        try:
            if int(sid)>0:
                conn = MySQLdb.connect(**self.normal_servers[int(sid)].mysql_cf)
            else:
                conn = connections['read']
        except Exception,e:
            print '%s 连接 mysql 失败:%s' % (self.normal_servers[int(sid)].name, e)
            #traceback.print_exc()
        return conn

    def load_done_server(self):
        self.done_server_map = pickle.load(open(self.done_file_name,'rb')) if os.path.exists(self.done_file_name) else {}
        return self.done_server_map
    
    def append_done_server(self,query_type_name,sid):
        self.done_server_map.setdefault(query_type_name,[])
        self.done_server_map[query_type_name].append(int(sid))
        
    def save_done_server(self):
        pickle.dump(self.done_server_map, open(self.done_file_name,'wb'))



class MysqlUtil(object):
    @classmethod
    def excute_sql(cls,conn,sql):
        try:
            cur = conn.cursor()
            cur.execute(sql)
        except Exception as e:
            print e
        return cls.get_mysql_result(cur) 
    @classmethod
    def get_mysql_result(cls,cursor,size=10000):
        '''每次获取10000条记录
        '''
        while True:
                result = cursor.fetchmany(size)
                if not result:
                    break
                for line in result:
                    yield line


sm = ServerManager()

class AutoBackup(object):
    DAY_FORMAT = '%Y%m%d'
    DATE_FORMAT = '%Y-%m-%d 00:00:00'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    def __init__(self,query_type,plan_name,sdate,edate,file_edate=''):
        '''自动备份
        @query_type 备份类型
        @plan_name 计划类型
        @sdate 开始时间
        @edate 结束时间
        @file_edate 传入这个参数 则内容都写到这个时间的文件
        '''
        self.query_type = query_type
        self.plan_name = plan_name
        self.sdate = sdate or datetime.datetime.now()
        self.edate = edate or datetime.datetime.now()
        self.sdate_str = self.sdate.strftime(self.DATE_FORMAT)
        self.edate_str = self.edate.strftime(self.DATE_FORMAT)
        self.is_append = file_edate
        if plan_name == 'daily':#日备份：数据备份文件名中的数据日期以数据产生的日期为准，如：备份2012-05-01日的数据，文件名为：mixed___S1___20120501___orders___daily.txt；
            file_edate = self.sdate.strftime(self.DAY_FORMAT)
        self.file_edate = file_edate
        self.prepare_save_dir()
        
    def prepare_save_dir(self):
        '''准备目录
        '''
        self.save_dir = self.query_type.save_dir.replace('{{edate}}',self.file_edate or self.edate.strftime(self.DAY_FORMAT))  
        #创建保存的目录   
        if not os.path.exists(self.save_dir):
             os.makedirs(self.save_dir)
            
    def run(self,sid=0):
            if self.query_type.is_query_server:
                try:
                    if sid:#单个服运行
                        server_list = [(sid,sm.normal_servers[int(sid)])]
                    else:
                        server_list = sm.normal_servers.iteritems()
                    self.excute_servers(server_list)
                except:
                    pass
            else:
                self.excute_single()
    start = run
    
    def excute_single(self):
        for i in xrange(5):
            try:
                sql = self.query_type.sql.replace('{{sdate}}',self.sdate_str)\
                                         .replace('{{edate}}',self.edate_str)        
                
                conn = sm.get_conn(0)
                file_name = self.query_type.file_format.replace('{{edate}}',self.file_edate or self.edate.strftime(self.DAY_FORMAT))\
                                                       .replace('{{plan_name}}',self.plan_name)\
                                                       .replace('{{prefix}}',PREFIX)  
                _log.debug( '%s %s %s - %s: querying...' % (self.query_type.name,self.plan_name,self.sdate_str,self.edate_str))                                                                 
                self.query_and_write(file_name,conn,sql)
                _log.info('%s %s %s - %s: done!' % (self.query_type.name,self.plan_name,self.sdate_str,self.edate_str))
                break
            except Exception,e:
                    traceback.print_exc()
                    time.sleep(1)
                    if i>=4:
                        _msg = '%s %s %s - %s error count(%s): %s' % (self.query_type.name, self.plan_name,self.sdate_str,self.edate_str,i,trace_msg())
                        _log.warning(_msg)
                        post_msg('qq','%s 游爱自动备份错误 %s %s'%(PREFIX,self.query_type.name, self.plan_name),_msg,merge=True)
                                                
    def excute_servers(self,server_list):
        T = ThreadPool(THREAD_POLL_NUMS)

        for sid,s_obj in server_list:
                    if self.plan_name == 'first' and sid in sm.done_server_map.get(self.query_type.name,[]):
                            _log.info('%s %s :%s(%s) in done_server_list break'%(self.query_type.name,self.plan_name,sid,s_obj.name))
                            break   
                    #self._excute_server(s_obj)
                    T.append(self._excute_server,(s_obj,))
        T.close()
        T.join() 

        print '-' * 40
        print 'END'
        #del T
    
    def delete_file(self,file_name):
        try:
            if os.path.isfile(file_name):
                os.remove(file_name)
        except:
            pass
    def _excute_server_log_str(self,s_obj):
        return '%s %s: %s(%s) %s - %s ' % (self.query_type.name,self.plan_name,s_obj.name,s_obj.id,self.sdate_str,self.edate_str)

    def _excute_server(self, s_obj):

        for i in xrange(10):
            try:
                sql = self.query_type.sql.replace('{{server_id}}', str(s_obj.id)) \
                    .replace('{{server_name}}', str(s_obj.name)) \
                    .replace('{{master_id}}', str(s_obj.master_id)) \
                    .replace('{{sdate}}', self.sdate_str) \
                    .replace('{{edate}}', self.edate_str) \
                    .replace('{{prefix}}', PREFIX)
                if self.query_type.is_center:  # 是否在中央服查询，连接的是MYSQL
                    conn = sm.get_conn(0)
                else:                # 优化查询
                    conn = sm.get_conn(s_obj.id)
                file_name = self.query_type.file_format.replace('{{server_id}}', str(s_obj.id)) \
                    .replace('{{edate}}', self.file_edate or self.edate.strftime(self.DAY_FORMAT)) \
                    .replace('{{plan_name}}', self.plan_name) \
                    .replace('{{prefix}}', PREFIX)
                _log.debug('%s querying...' % self._excute_server_log_str(s_obj))

                self.query_type.create_tmp_table(conn, s_obj, self)  # 创建金币临时表
                self.query_and_write(file_name, conn, sql)

                _log.info('%s done!' % self._excute_server_log_str(s_obj))
                break
            except Exception, e:
                print trace_msg()
                time.sleep(3)
                if i >= 9:
                    _msg = '%s %s %s(%s) %s - %s error count(%s): %s' % (
                    self.query_type.name, self.plan_name, s_obj.name, s_obj.id, self.sdate_str, self.edate_str, i,trace_msg())
                    _log.warning(_msg)
                    post_msg('qq', '%s 游爱自动备份错误 %s %s %s(%s)' % (PREFIX, self.query_type.name, self.plan_name, s_obj.name, s_obj.id), _msg, merge=True)
                    
    def query_and_write(self,file_name,conn,sql):
        self.save_path = os.path.join(self.save_dir,file_name)  
        if self.is_append:        
            fp = open(self.save_path,'ab')
        else:                           
            fp = open(self.save_path,'wb') 
        try:
            rows  = 500000
            offset = 0
            while 1:
                sp = offset * rows
                tmp_sql = '%s LIMIT %d,%d;' % (sql.rstrip().rstrip(';'),sp,rows)
                result = MysqlUtil.excute_sql(conn,tmp_sql)
                write_nums = self.write_file(fp,result,line_handler = self.query_type.line_handler)
                if write_nums<rows:
                    break
                offset += 1
        except:
            traceback.print_exc()
        finally:
           conn.close()
           fp.close()
            
        
    def write_file(self,fp,result,line_handler=lambda x:x):
        i = 0
        for line in result:
            i += 1
            line_str = line_handler(line)
            #print line_str
            if line_str:
                fp.write(line_str)
                fp.write('\n')
        #fp.flush()
        return i
       
                    
    def __del__(self):
        gc.collect()
        #super(AutoBackup,self).__del__()
   


class LTVDateMaker(object):
    '''LTV 数据生成 只能当月
    '''
    _INSERT_LOCK = threading.Lock()
    save_folder =  os.path.join( cwdir,'ltv')
    def __init__(self,sdate,sid=0):
        
        self.sid = int(sid)
        self.sdate = sdate or datetime.datetime.now()
        self.sdate_str = self.sdate.strftime('%Y-%m-01 00:00:00') #当月1号
        self.server_pay_user_map = {}
        self.makedir_save_foler()
        
    def makedir_save_foler(self):
        try:

            os.mkdir(self.save_folder)
        except:
            pass
    def get_pay_file_name(self):
        return os.path.join(self.save_folder, '%s_pay.csv' % (self.sdate.strftime('%Y-%m')) )
        
    def get_login_file_name(self):
        return  os.path.join(self.save_folder, '%s_login.csv' % (self.sdate.strftime('%Y-%m')) )
        
        
    def get_server_pay_user_ids(self,server_id):
        '''获取当月创建并且有充值的用户
        '''
        pay_user_ids = self.server_pay_user_map.get(server_id,[0])
        return [str(x) for x in pay_user_ids]
    
    def add_pay_user(self,server_id,player_id):
        self.server_pay_user_map.setdefault(server_id,set())
        self.server_pay_user_map[server_id].add(player_id)
        
    def make_pay_user_data(self):
        #user id,  user name,   充值日期，  充值游戏币
        sql = '''
        SELECT p.pay_user,pl.player_name,date_format(p.last_time,'%%Y-%%m-%%d %%H:%%i:%%S'),p.pay_gold,pl.server_id
FROM player_all pl
JOIN pay_action p ON pl.player_id=p.pay_user
WHERE pl.create_time>='{sdate}' AND pl.create_time< date_add('{sdate}',interval 1 month)
AND p.pay_status=4 and p.pay_gold>0
        '''.format(sdate=self.sdate_str)
        
        sql = '''
        SELECT p.pay_user,pl.player_name,date_format(p.last_time,'%%Y-%%m') dd,Sum(p.pay_gold),pl.server_id
FROM player_all pl
JOIN pay_action p ON pl.player_id=p.pay_user
WHERE pl.create_time>='{sdate}' AND pl.create_time< date_add('{sdate}',interval 1 month)
AND p.pay_status=4 and p.pay_gold>0 
        '''.format(sdate=self.sdate_str)

        
        if self.sid:
           sql +=' AND pl.server_id=%d AND p.server_id=%d' % (self.sid,self.sid) 

        sql += '  GROUP BY dd,p.pay_user order by p.pay_user,dd'
        #sql += ' ORDER BY pl.server_id,p.pay_user'
        
        conn = sm.get_conn(0)
        print sql
        result = MysqlUtil.excute_sql(conn,sql)
        
        pay_file = self.get_pay_file_name()
        line_num = 0

        with codecs.open(pay_file,'wb','utf-8') as fp:
            fp.write(codecs.BOM_UTF8)
            fp.write('角色ID,角色名,充值日期,充值金币,服务器ID\n')
            for lines in result:
                line_num += 1
                if lines:
                    player_id = lines[0]
                    server_id = lines[-1]
                    self.add_pay_user(server_id,player_id)
                    fp.write(','.join([ str(x) for x in lines]))
                    fp.write('\n')
            _log.warning('充值数据写入了 %s 条' % line_num)
        

    def _make_pay_user_login_data_generators(self):
        login_file_name = self.get_login_file_name()
        try:
            with  codecs.open(login_file_name,'wb','utf-8') as fp:
                fp.write(codecs.BOM_UTF8)
                fp.write('角色ID,角色名,登录日期,登录次数,服务器ID\n')
                while 1 : 
                    lines = yield
                    if isinstance(lines,(tuple,list)):
                        for line in lines:
                            fp.write(','.join([ str(x) for x in line]))
                            fp.write('\n')
                    else:
                        break
        except:
            _log.warning(trace_msg())
            
    
    def get_server_pay_user_login_data(self,s_obj,insert_generators):
        '''获取 充值用户 登录数据
        '''
        
        pay_user_ids = self.get_server_pay_user_ids(s_obj.id)
        pay_user_ids_str = ','.join(pay_user_ids)
        #登录表： user id,  user name,   登录日期
        sql = '''
SELECT c.log_user,c1.player_name,date_format(c.log_time,'%Y-%m-%d %H:%i:%S'),c.log_data,c.log_server 
FROM log_check_user c 
JOIN player_{sever_id}_tmp c1 
ON c.log_user=c1.player_id 
WHERE c1.create_time >='{sdate}' and c1.create_time<date_add('{sdate}',interval 1 month) 
AND c.log_user in ({pay_user_ids_str}) order by c.log_user,c.log_data
        '''.format(pay_user_ids_str=pay_user_ids_str,sdate=self.sdate_str,sever_id=s_obj.id)
                
        sql = '''
SELECT c.log_user,c1.player_name,date_format(c.log_time,'%Y-%m') dd,count(0),c.log_server 
FROM log_check_user c 
JOIN player_{sever_id}_tmp c1 
ON c.log_user=c1.player_id 
WHERE c1.create_time >='{sdate}' and c1.create_time<date_add('{sdate}',interval 1 month) 
AND c.log_user in ({pay_user_ids_str}) GROUP BY dd,c.log_user order by c.log_user,dd
        '''.format(pay_user_ids_str=pay_user_ids_str,sdate=self.sdate_str,sever_id=s_obj.id)
        
        pay_user_ids_count = len(pay_user_ids)
        if int(pay_user_ids[0]) == 0:
            return
        _log.info('%s(%s) %s 生成 %s个充值用户登录日志' % (s_obj.name,s_obj.id,self.sdate_str,pay_user_ids_count))
        
        conn = sm.get_conn(s_obj.id)
        cur = conn.cursor()
        try:
            cur.execute(sql)
            insert_size = 0
            self._INSERT_LOCK.acquire()
            while 1:
                result = cur.fetchmany(50000)
                if result:
                    try:
                        _log.info('%s(%s) %s 写入  %s 行充值用户登录日志' % (s_obj.name,s_obj.id,self.sdate_str,len(result)))
                        insert_generators.send(result)
                    except Exception,e:
                        _log.warning(trace_msg())
                else:
                    break
            
        except Exception,e:
            _log.warning(trace_msg())
        finally:
            self._INSERT_LOCK.release()
            conn.close()

        
    def make_pay_user_login_data(self):
        '''生成 充值用户 登录文件
        '''
        _generators = self._make_pay_user_login_data_generators()
        _generators.next()
        if self.sid:
            server_list  = [(self.sid,sm.normal_servers[int(self.sid)])]
        else:
            server_list = sm.normal_servers.iteritems()
        T = ThreadPool(THREAD_POLL_NUMS)
        i = 0
        for k,s_obj in server_list:
                i += 1
                if i>5000:break
                T.append(self.get_server_pay_user_login_data,(s_obj,_generators))   
        T.close()
        T.join()
        del T
        _generators.close()
    

    def start(self):
        try:
            self.make_pay_user_data()
            self.make_pay_user_login_data()
        except:
            _log.warning(trace_msg())
    
    
class RollPlayer(object):
    '''生成滚服角色表数据
    0 创建分服滚服表
    1 获取还没生成滚服数据的角色列表
    2 用link_key 对比中央角色表 获取其他服角色信息
    3 将中央角色信息写入到分服 滚服表
    4 更新中央角色表的 roll_num
    '''
    def __init__(self,sid=0):
        self.sid = sid
        self.create_roll_player_sql         = SQL['create_roll_player']
        self.get_roll_player_sql            = SQL['get_roll_player']
        self.get_center_roll_player_sql     = SQL['get_center_roll_player']
        self.update_center_roll_num_sql     = SQL['update_center_roll_num']
        self.insert_player_roll_sql         = SQL['insert_player_roll']
        
        
    def __create_server_player_roll_table(self,conn):
        try:
            conn.cursor().execute(self.create_roll_player_sql)
        except:
            pass
    
    def __get_roll_player(self,conn,s_obj):
        sql = self.get_roll_player_sql.replace('{{server_id}}',str(s_obj.id))
        return MysqlUtil.excute_sql(conn, sql)
        
    def __get_center_roll_player(self,conn,link_key,user_type,create_time):
        sql = self.get_center_roll_player_sql % (link_key,user_type,create_time)
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()
        return len(result),result
    
    def __insert_player_roll(self,conn,roll_num,player_infos):
        sql = self.insert_player_roll_sql
        values = []
        for row in player_infos:
            ll = row + (roll_num,)
            values.append(ll)

        conn.cursor().executemany(sql,values)
        conn.commit()
        
    def __update_center_roll_num(self,conn,roll_num,player_id):
        #print self.update_center_roll_num_sql  % (roll_num,player_id)
        conn.cursor().execute(self.update_center_roll_num_sql, (roll_num,player_id))
        
    def run(self,s_obj):
        '''
        '''
        try:
            center_conn = connections['write']
            server_conn = sm.get_conn(s_obj.id)
            insert_server_conn  = sm.get_conn(s_obj.id)
            insert_server_conn.autocommit(False)
            
            self.__create_server_player_roll_table(server_conn)
            self.__create_server_player_roll_table(server_conn)
            insert_num = 0
            for pid,link_key,user_type,create_time in self.__get_roll_player(server_conn,s_obj):
                roll_num,player_infos = self.__get_center_roll_player(center_conn,link_key,user_type,create_time)

                if roll_num>0:
                    roll_num -= 1 if roll_num>=1 else 0
                    self.__insert_player_roll(insert_server_conn,roll_num,player_infos)
                    if roll_num > 0:
                        self.__update_center_roll_num(center_conn,roll_num,pid)
                insert_num += 1
            print '[%s] %s(%s) 更新  %s 条滚服数据' % (datetime.datetime.now(),s_obj.name,s_obj.id,insert_num)
            server_conn.close()
            center_conn.close()
        except Exception,e:
            _log.warning(trace_msg())

    def start(self):
        if self.sid:
            server_list  = [(self.sid,sm.normal_servers[int(self.sid)])]
        else:
            server_list = sm.normal_servers.iteritems()
        T = ThreadPool(THREAD_POLL_NUMS)
        i = 0
        for k,s_obj in server_list:
                i += 1
                if i>5000:break
                T.append(self.run,(s_obj,))   
        T.close()
        T.join()
        del T
        
    @staticmethod
    def delelte_roll_player_table():
        for sid,s_obj in sm.normal_servers.iteritems():
            sql = 'drop table if exists player_roll;'
            try:
                conn = sm.get_conn(s_obj.id)
                conn.cursor().execute(sql)
            except:
                pass
class CenterPlayer(object):
    _INSERT_LOCK = threading.Lock()
    def __init__(self,sdate,edate,sid=0):
        '''
        @自动拉取当天创建的角色
        '''
        self.sid = sid
        self.sdate = sdate or datetime.datetime.now()
        self.edate = edate or datetime.datetime.now()
        self.edate = self.edate + datetime.timedelta(days=1)
        self.sdate_str = self.sdate.strftime(AutoBackup.DATE_FORMAT)
        self.edate_str = self.edate.strftime(AutoBackup.DATE_FORMAT)
    
    def _Async_insert_result(self):
        '''异步插入数据
        '''
        sql = SQL['insert_center_player']
        insert_nums = 0
        try:
            conn = connections['write']
            cur = conn.cursor()
            print '-' * 40
            
            #conn.autocommit(True)
            while 1 : 
                lines = (yield)
                #print sql
                if isinstance(lines,(tuple,list)):
                    try:#尝试插入
                        insert_nums += len(lines)
                        #print sql % lines[0]
                       
                        cur.executemany(sql,lines)
                    except Exception,e:
                        _log.info(trace_msg())
                        traceback.print_exc()
                else:
                    break
        except Exception,e:
            print '-'*400
            _log.warning(trace_msg())
        finally:
            _log.info( 'insert (%s) result to player_all done !' % insert_nums)
            conn.close()
        
    def create_center_player_table(self):
        '''创建全服的player表
        '''
        try:
            cur = connections['write'].cursor()
            sql = SQL['create_center_player']
            cur.execute(sql)
        except Exception,e:
            _log.warning(trace_msg())
        

    def update_player_all(self,s_obj,insert_generators):
        '''拉取全服的player表
        '''
        sql = SQL['get_player'].replace('{{server_id}}',str(s_obj.id))\
                               .replace('{{sdate}}',self.sdate_str)\
                               .replace('{{edate}}',self.edate_str)     
                                          

        try:
            conn = sm.get_conn(s_obj.id)
            cur = conn.cursor()
        
            BaseQuery.create_tmp_table(conn, s_obj)#先创建一下player_xx_tmp表
            #print sql
            cur.execute(sql)
            insert_size = 0
            while 1:
                result = cur.fetchmany(50000)
                if result:
                    insert_size += len(result)
                    _log.debug('%s player_%s has %s inserting....' % (s_obj.name,s_obj.id,insert_size))
                    try:
                        self._INSERT_LOCK.acquire()
                        insert_generators.send(result)
                    except Exception,e:
                        _log.warning(trace_msg())
                    finally:
                        self._INSERT_LOCK.release()
                else:
                    break
        except Exception,e:
            _log.warning('%s(%s):%s' % (s_obj.id, s_obj.name,trace_msg() ))
        finally:
            try:conn.close()
            except:pass
            
    def start(self):
        self.create_center_player_table()
        _generators = self._Async_insert_result()
        _generators.next()
        if self.sid:
            server_list  = [(self.sid,sm.normal_servers[int(self.sid)])]
        else:
            server_list = sm.normal_servers.iteritems()
        T = ThreadPool(THREAD_POLL_NUMS)
        i = 0
        for k,s_obj in server_list:
                i += 1
                if i>5000:break
                T.append(self.update_player_all,(s_obj,_generators))   
        T.close()
        T.join()
        del T
        
def get_previous_month_day(sdate):
    year = sdate.year
    month = sdate.month
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1
    return datetime.datetime(year,month,1)
 
def auto_backup_do(plan,sdate,edate,sid=0):
        for q in Query_Types:
            if getattr(q,plan,''):
                b = AutoBackup(q,plan,sdate,edate) 
                b.start(sid)
                del b  
                  
def remove_30ago_dir():  
    '''删除30以前的目录
    '''
    ago_date = datetime.datetime.now() - datetime.timedelta(days=30)
    the_dir = os.path.join(SAVE_DIR,ago_date.strftime(AutoBackup.DAY_FORMAT)) 
    _log.debug('the old dir is %s ' % the_dir )
    if os.path.exists(the_dir) and the_dir!=SAVE_DIR and the_dir!='/':
        _log.info('delete %s' % the_dir )
        shutil.rmtree(the_dir,True)
        
def cron_do():
    '''定时运行

    '''
    print 'start cron job !'
    while True:
        try:
            edate  = datetime.datetime.now()
            sdate  = edate + datetime.timedelta(days=-1)
            
            if edate.hour == 3 and edate.minute == 1:   #03:01 start
                close_connections()
                sm.update_server_config()               #1 更新服务列表
                update_dicts()                          #2 更新渠道列表
                CenterPlayer(sdate,edate).start()       #3 插入中央服player_all
                
                RollPlayer().start()                    #4 更新滚服 数据
                
                auto_backup_do('daily',sdate,edate)     #执行备份
                if edate.day == 1 :#每月1号执行的
                    sdate = get_previous_month_day(edate)
                    edate = edate.replace(day=1)
                    auto_backup_do('monthly',sdate,edate)
                remove_30ago_dir()
                
                post_msg('qq','%s 定时备份完成!' % PREFIX)
        except Exception,e:
            _msg = trace_msg()
            print _msg
            post_msg('qq','%s 定时备份错误!' % PREFIX,_msg)
        
        time.sleep(60)

    


def main():
     #首次(first) 每月(monthly) 每天(daily) 关服(closed)
    from optparse import OptionParser 
    MSG_USAGE = "usage: %prog -d 2014-04-01 -s 2014-01-01 -p [first|daily|monthly|center_player|ltv] -S 10" 
    
    parser = OptionParser(MSG_USAGE)              
    parser.add_option("-s", "--sdate", dest="sdate", default='',
                        help="the sdate",metavar='')                
    parser.add_option("-e", "--edate", dest="edate",
                        help="the edate",metavar='')  
    parser.add_option("-S", "--server", dest="sid",default='0',
                        help="the sid",metavar='') 
    parser.add_option("-p", "--plan", dest="plan", 
                        help="the plan [first,daily,monthly,center_player,roll_player]",metavar='')
    parser.add_option("-q", "--qtype", dest="qt", default = '',
                        help="the plan %s" % ','.join([ q.__name__ for q in Query_Types]),metavar='')                                    
    parser.add_option("-c", "--cron", dest="cron",action = "store_true",
                        help="run cron")
    # 创建 player_roll 表，避免后台查询、联结时报错

    parser.add_option("--table", dest="table_only",action = "store_true",
                        help="just create player_roll & player_xxx_tmp table")

    (o, args) = parser.parse_args()

    if o.table_only:
        create_player_roll_table()
        create_player_xx_tmp_table()
        return 

    if o.cron:
        cron_do()
        return
    if not o.plan or not o.edate:
        parser.print_help()
        return 
    
    edate = datetime.datetime.strptime(o.edate,'%Y-%m-%d')
    sdate = datetime.datetime.strptime(o.sdate,'%Y-%m-%d') if o.sdate else ''
    plan = o.plan
    if ',' in o.sid:
        sids = [ int(x) for x in  o.sid.split(',') if x]
    else:
        sids = [int(o.sid)]
    qt = o.qt
    daterange = 1
    date_list = []
    for sid in sids:
        if plan == 'roll_player':
                r = RollPlayer(sid)
                r.start()
        elif plan == 'center_player':
                sdate = datetime.datetime.strptime(o.sdate,'%Y-%m-%d')
                c_p = CenterPlayer(sdate,edate ,sid)
                c_p.start()
                 
        elif plan == 'ltv':
                edate = datetime.datetime.strptime(o.edate,'%Y-%m-%d')
                ltv_maker = LTVDateMaker(edate,sid)
                ltv_maker.start()
        else:
            if plan == 'first':
                    sdate = datetime.datetime.fromtimestamp(0)
                    #edate = datetime.datetime.now()
                    '''
                    sdate = edate
                    edate = datetime.datetime.strptime(sys.argv[4],'%Y-%m-%d')  
                    file_edate = edate.strftime(AutoBackup.DAY_FORMAT)
                    for q in Query_Types:
                        tmp_sdate = sdate
                        
                        while (edate-tmp_sdate).days>0:
                                tmp_edate = (tmp_sdate + datetime.timedelta(weeks=5)).replace(day=1)
                                #tmp_edate = (tmp_sdate + datetime.timedelta(days=1))
                                print (tmp_sdate,tmp_edate,file_edate)
                                b = AutoBackup(q,plan,tmp_sdate,tmp_edate,file_edate)
                                b.start(sid)
                                del b
                                tmp_sdate = tmp_edate
                    '''
                    date_list = [(sdate,edate)]
            elif plan == 'daily':
                sdate =  sdate or edate - datetime.timedelta(days=1)
                if sdate:
                    while sdate<edate:
                        tmp_edate = sdate + datetime.timedelta(days=1)
                        date_list.append((sdate,tmp_edate))
                        sdate = tmp_edate
            elif plan == 'monthly':
                edate = edate.replace(day=1)  
                sdate = get_previous_month_day(edate)
                date_list = [(sdate,edate)]
            

            if plan and date_list :#and plan!='first':
                update_dicts()
                for sdate,edate in date_list:
                    for q in Query_Types:
                        if not qt or q.__name__ == qt:
                            if getattr(q,plan,''):
                                b = AutoBackup(q,plan,sdate,edate)
                                b.start(sid)
                                del b
                    #remove_30ago_dir()
            sm.save_done_server()  
                   

def create_player_roll_table():
    sm = ServerManager()
    for o in Server.objects.all():
        try:
            config_dict = sm._get_server_mysql_address(o)
            conn = MySQLdb.connect(**config_dict)
            rp = RollPlayer(o.id)
            rp._RollPlayer__create_server_player_roll_table(conn)
        except:
            pass


def create_player_xx_tmp_table():
    sm = ServerManager()
    for o in Server.objects.all():
        try:
            config_dict = sm._get_server_mysql_address(o)
            conn = MySQLdb.connect(**config_dict)
            BaseQuery.create_tmp_table(conn, o)
        except:
            pass

if __name__ == '__main__':
    main()
    #RollPlayer.delelte_roll_player_table()
