#coding:utf-8
#定时发送礼包资源的后台进程

from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser

from models.server import Server
from models.statistic import Statistic
from models.card import CardLog
from views.game.base import GMProtocol
import datetime
import time
import thread,traceback
from util import convert_to_datetime
import json
import settings
import sys
from util.threadpoll import ThreadPool
from django.db import transaction,connections,connection
from django.db.models import Q

settings.DEBUG = False

post_card_list_list = [0]

def send_resource_to_gm(card_log_model):
    msg = ''
    if card_log_model.status != 1:
        card_log_model.status = 3
        try:
            msg = json.loads(card_log_model.prize)
            #线程内mysql连接不同享,每个线程的内连接必须先ping下,防止mysql超时断开
            try:connections['write'].connection.ping()
            except:connections['write'].close()
            try:connections['card'].connection.ping() 
            except:connections['card'].close()
            server_model = Server.objects.using('write').get(id=card_log_model.server_id)
            gmp = GMProtocol(card_log_model.server_id,'card',server_model=server_model)
            gmp.time_out = 7
            result = gmp.send_card_resouces(card_log_model.player_id,card_log_model.card_name,msg)
            card_log_model.status = 3
            if result == 0:
                card_log_model.status = 1
            msg = '成功!'
        except Exception,e:
            msg = '失败[%s]!' % str(e)
            traceback.print_exc()
        
    try:
        card_log_model.save(using='card')
        print '[%s] send_card_resource: %s %s(%s) %s(%s) %s %s %s' % (datetime.datetime.now(),card_log_model.id,card_log_model.card_name,card_log_model.number,card_log_model.player_id,card_log_model.server_id,card_log_model.prize,card_log_model.status,msg)
    except:
        traceback.print_exc()
    if card_log_model.id in post_card_list_list:
        post_card_list_list.remove(card_log_model.id)
    


class Command(BaseCommand):
    '''统计相关命令行
    '''
    help = '定时发送礼包资源的后台进程!'
        
    def handle(self, *args, **options):
        
        tp = ThreadPool(5) #这里暂时只开一个工作线程,gm那边并发会返回空.
        while True:
            try :   
                try:connections['card'].connection.ping() 
                except:connections['card'].close()
                query = Q(status=0) & ~Q(id__in=post_card_list_list)
                card_model_list = CardLog.objects.using('card').filter(query)[:100]
                for card_log in card_model_list :
                    try:
                        if card_log.id not in post_card_list_list:
                            post_card_list_list.append(card_log.id)
                            card_log.status = 2
                            card_log.save(using='card')
                            tp.append(send_resource_to_gm,(card_log,))
                            
                    except:
                        traceback.print_exc()
            except:
                traceback.print_exc()
            time.sleep(5)
        tp.close()
        tp.join()
        
        
        