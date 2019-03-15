#!/usr/bin/env python
# coding: utf-8

# from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
# from optparse import make_option,OptionParser

from models.pay import PayAction
from models.channel import Channel
from views import getConn
import time
from settings import APP_LABEL
import os
BASE_LOG_PATH = os.path.join(APP_LABEL,'logs/fix_sql/').replace('\\','/')

def Log(Type,msg):
    now = time.strftime("%Y%m%d")
    path =  BASE_LOG_PATH + '%s.log'%(now)

    #没有文件夹就创建
    check_dir = os.path.dirname(path)
    isExists = os.path.exists(check_dir)
    if not isExists:
        os.makedirs(check_dir)

    now_time = time.strftime("%Y-%m-%d %H:%M:%S")
    msg =  now_time + ' [%s] '%(Type) + '%s'%msg
    msg += '\n'
    with open(path,'a') as L:
        L.write(msg)

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            models = PayAction.objects.all()
            for model in models:
                player_id = model.pay_user
                channel_id = model.channel_id
                get_channel_id = int(self.get_channel_id(player_id))

                if channel_id !=get_channel_id and get_channel_id!=0:
                    model.channel_id = get_channel_id
                    try:
                        channel = Channel.objects.get(id=get_channel_id)
                        get_channel_key = channel.channel_key
                        model.channel_key = get_channel_key
                        model.save()
                        print "excute success query_id=%s"%model.query_id
                        Log("info","excute success query_id=%s"%model.query_id)
                    except Exception as e:
                        print e
        except Exception as e:
            print "handle has error ",e
            Log("error","handle has error %s"%e)
    def get_channel_id(self,player_id):
        channel_id = 0
        conn = getConn()
        try:
            query_sql = "select channel_id from player_all where player_id=%d" % (player_id)
            print(query_sql)
            cursor = conn.cursor()
            cursor.execute(query_sql)
            pay_user_record = cursor.fetchone()
            if pay_user_record != None:
                channel_id = int(pay_user_record[0])
        except Exception, e:
            print('get player_channel_id has error', e)
        return channel_id


