# coding:utf-8
# 自动封禁IP

from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option, OptionParser

from models.server import Server
from models.game import Activity
from views.game.base import GMProtocolBase
from django.db.models.base import ModelBase
import sys
import os
import datetime
import time
import json
import threading
import traceback

from util import convert_to_datetime
from util.threadpoll import ThreadPool
from django.db import transaction
from django.db.models import Q
from Queue import Queue
from models.center import BanIpList, User

import settings
settings.DEBUG = False
from views.game.activity import activity_action

from django.db import connections


class Command(BaseCommand):
    '''公告自动生成进程
    '''
    help = '自动封禁IP(单服单个ip创建了超过N个角色后)'

    def handle(self, *args, **kwargs):
        while True:
            print u'现在时间是:%s'%(datetime.datetime.now())
            control = int(BanIpList.objects.filter(id=1)[0].f1) or 0
            if control:
                self.add_users_ip()
                self.add_servers_ip()
            time.sleep(3600)

    def add_users_ip(self):
        # 先写入users表，现有的封禁IP和白名单IP
        ban_usersip_list = User.objects.filter(status__in=[-3,4])
        for m in ban_usersip_list:
            if not m.last_ip:
                continue
            _bm = BanIpList.objects.filter(ip=m.last_ip)
            if not _bm:
                model = BanIpList()
                model.username = m.username
                model.ip = m.last_ip
                model.last_time = datetime.datetime.now()
                model.status = m.status
                model.f1 = 0
                model.f2 = 0 
                model.save(using="write")
            # ip是唯一的,已封禁就不管了
            continue

    def add_servers_ip(self):
        # 超过N个角色后封禁账号IP，这个N是从banip_list的f2来的
        server_list = Server.get_server_list()
        count = int(BanIpList.objects.filter(id=1)[0].f2) or 0
        if not count:
            print u'没有设定超过数'
            return
        for s in server_list:
            player_ip_list = self.get_player_list(s.id, count)
            if not player_ip_list:
                continue
            for i in player_ip_list:
                _bm = BanIpList.objects.filter(ip=i[0])
                if not _bm:
                    model = BanIpList()
                    model.username = i[2]
                    model.ip = i[0]
                    model.last_time = datetime.datetime.now()
                    model.f1 = 0
                    model.f2 = i[1]
                    model.status = 0
                    model.save(using="write")
                    continue
                _bm = _bm[0]
                _ip = _bm.ip
                _bm.f2 = i[1]
                _bm.last_time = datetime.datetime.now()
                _bm.save(using="write")

                #封掉那些号  2017-12-21 不自动封禁
                # usersip_list = User.objects.filter(last_ip = i[0])
                # if not usersip_list:
                #     continue
                # for u in usersip_list:
                #     u.status = -3
                #     u.last_time = datetime.datetime.now()
                #     u.save(using="write")

    def get_player_list(self, server_id, count):
        # 获取分服玩家列表信息
        if not server_id or not count:
            return
        try:
            conn = Server.get_conn(server_id)
            sql = '''
            select last_ip,c,link_key from(select last_ip,count(0) c ,link_key from player_%d group by last_ip) a where c >= %d and last_ip != ""
            ''' % (server_id, count)
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            print result
            return result
        except BaseException as e:
            print "%s 链接数据库时发生错误！%s"%(server_id,e)
            return []
