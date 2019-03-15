#coding=utf-8


import sys, csv, traceback
from django.core.management import BaseCommand
from models.channel import Agent,Channel
from models.pay import PayAction
from views.game.pay import game_pay
import random,datetime,time
from django.db import transaction,connections
from django.db.models import Q

class Command(BaseCommand):
    '''充值后台进程,查找当前失败(支付状态为-2,-4)的订单进行补发
    '''
    help = '充值后台进程,查找当前失败(支付状态为-2,-4)的订单进行补发'
        
    def handle(self, *args, **options):
        while 1:
            try :   
                try:connections['write'].connection.ping()
                except:connections['write'].close()
                now = datetime.datetime.now()
                print now
                ago_time = now + datetime.timedelta(minutes=-90)
                query = Q(Q(post_time__lte=ago_time)|Q(last_time__lte=ago_time)) & Q(pay_status=-2)|Q(Q(post_time__lte=ago_time)|Q(last_time__lte=ago_time)) & Q(pay_status=-4)
                pay_action_models = PayAction.objects.using('write').filter(query)

                if pay_action_models:
                    print u'发现充值失败的订单: ',pay_action_models
                for pay_action in pay_action_models :
                    game_pay(pay_action)
            except:
                traceback.print_exc()
            finally:
                connections['write'].close()
            time.sleep(60)

        
        



