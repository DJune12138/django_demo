# -*- coding: utf-8 -*-
'''
游戏充值相关
'''

from util import trace_msg
from .base import GMProtocol
import datetime,time
import threading
import functools
from models.pay import PayAction,PayChannel
from models.server import Server
from django.db import connections
import MySQLdb 


DEBUG = False
mysql_space = 'write'
def async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        my_thread.setDaemon(True)
        my_thread.start()
    return wrapper


def game_pay(pay_action,pay_channel=None,extra="",time_out=10):
    '''游戏充值
    '''

    err_msg = ''
    
    if not pay_channel and pay_action.pay_type:
        try:
            pay_channel = PayChannel.objects.using(mysql_space).get(id=pay_action.pay_type)
        except:
            msg = trace_msg()
            print 'get pay_channel _error %s' % msg

    if pay_action.is_sure_pay() and pay_action.server_id and pay_action.pay_user and pay_action.pay_amount and pay_action.pay_gold:
        try: 
            try:

                server_model = Server.objects.using(mysql_space).get(id=pay_action.server_id)

                gmp = GMProtocol(pay_action.server_id,server_model=server_model,logger_name='pay')
                gmp.time_out = time_out or 10
                #这个充值通道是月卡的而且 金币相等才是月卡
                # is_month_card = 1 if pay_channel.is_month_card(pay_action) else 0
                
                pay_action.pay_status = 3#已转发,未回复
                pay_action.save(using='write')
                result = gmp.player_pay(
                               pay_action.pay_user,
                               pay_action.query_id,
                               int(pay_action.pay_gold),
                               int(pay_action.extra),
                               int(pay_action.charge_type),
                               int(pay_action.charge_id),
                               extra
                               )
                if result == 0 :
                    pay_action.pay_status = 4  #充值成功,金币已发放
                else:
                    pay_action.pay_status = -4 #充值失败
                    pay_action.remark += gmp.rsp_map.get(result,'')
            except Exception,e:
                err_msg = str(e)
                pay_action.pay_status = -2    #连接失败
            pay_action.last_time = datetime.datetime.now()
            pay_action.save(using=mysql_space)
            if pay_action.pay_status == 4:
                log_sql = '''insert into log_pay(log_type,log_user,log_server,log_channel,log_data,log_result,log_time,
                                                    log_relate,log_now,log_previous,log_tag,f1,f2,f3,f4,f6) 
                                          select pay_type,pay_user,server_id,channel_id,pay_amount,pay_gold,last_time,
                  query_id qa,query_id qb,order_id,count,open_id,post_amount,extra,pay_ip,remark from pay_action where id=%d ''' % pay_action.id
                
                cur = connections[mysql_space].cursor()
                cur.execute(log_sql)
            ##充值累计240000开启vip界面
            if pay_action.pay_status == 4:
                sql = '''select * from (select sum(pay_amount) as sum_amount,pay_user from pay_action where pay_status = 4 group by pay_user) pa where sum_amount >=240000 and pay_user=%d''' % pay_action.pay_user
                cur = connections['read'].cursor()
                n = cur.execute(sql)
                print "###",n,pay_action.pay_user
                if n:
                    sql = '''insert into viplist(player_id,server_id,privilege_type,everyday_type) value(%d,%d,0,1)'''% (pay_action.pay_user,pay_action.server_id)
                    cur = connections[mysql_space].cursor()
                    cur.execute(sql)

        # except MySQLdb.Warning, w:
        #     sqlWarning =  "Warning:%s" % str(w) 
        except Exception,e:
            err_msg = trace_msg()
        finally:
            connections[mysql_space].close()
        if DEBUG:
            print 'game_pay','-' * 40
            print 'query_id: %s' % pay_action.query_id
            print 'order_id: %s' % pay_action.order_id
            print 'pay_status: %s' % pay_action.pay_status
            print 'server_id: %s' % pay_action.server_id 
            print 'pay_use: %s ' % pay_action.pay_user 
            print 'pay_amount: %s' % pay_action.pay_amount 
            print 'pay_gold: %s,extra: %s' % (pay_action.pay_gold,pay_action.extra)
        
        if err_msg:
            print 'err_msg %s' % err_msg
    return err_msg

@async
def async_game_pay(*args,**kwargs):
    return game_pay(*args,**kwargs)
            
            