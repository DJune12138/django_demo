# coding:utf-8
# 自动统计服务器战力，等级等数据

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
from views.game.base import GMProtocol

import settings
settings.DEBUG = False
from views.game.activity import activity_action
from decimal import *

from django.db import connections


def keep_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:c.connection.connection.ping()
        except:c.close()

class Command(BaseCommand):
    '''公告自动生成进程
    '''
    help = '自动插入服务器游戏数据(最高战力,前十战力,前50战力,前50等级)'

    def get_base_sql(self):
        top_power_sql = "select f6 from log_battle_rank where f1 = 1 order by log_time desc limit 1"
        avg_power_sql = "select avg(f6+0) from (select f6 from (select id,f6 from log_battle_rank order by log_time desc limit 100) a order by id limit 50) b"
        ten_power_sql = "select avg(f6+0) from (select f6 from (select id,f6 from log_battle_rank order by log_time desc limit 100) a order by id limit 10) b"
        avg_level_sql = "select avg(f5+0) from (select f5 from (select id,f5 from log_battle_rank order by log_time desc limit 100) a order by id limit 50) b"
        avg_login_sql = 'select avg(users) from (select date_format(log_time,"%Y-%m-%d") dd,count(DISTINCT log_user) users from log_check_user group by dd order by dd desc limit 3) a'
        return {"top_power":top_power_sql,"avg_power":avg_power_sql,"ten_power":ten_power_sql,"avg_level":avg_level_sql,"avg_login":avg_login_sql}

    def get_base_info(self):
        base_info = {}
        base_info["sub_server"] = []
        return base_info

    def handle(self, *args, **kwargs):
        while True:
            keep_connections()
            base_sql = self.get_base_sql()
            servers = Server.objects.all()
            base_info = self.get_base_info()
            for s in servers:
                try:
                    game_data = {}
                    if not s.json_data:
                        conn = Server.get_conn(s.id)
                        for logName,logSql in base_sql.iteritems():
                            print '-'*40
                            print s.id,logSql
                            print '-'*40
                            cursor = conn.cursor()
                            cursor.execute(logSql)
                            result = cursor.fetchone()
                            game_data[logName] = float(result[0]) if result[0] else ""
                            cursor.close()
                            s.game_data = json.dumps(game_data)
                            s.save(using="write")
                    else:
                        master_id = json.loads('{%s}' % s.json_data)["master_server_id"]
                        server = Server.objects.get(id=master_id)
                        game_data = json.loads(server.game_data)
                        for field,value in base_info.iteritems():
                            if game_data.has_key(field):
                                if s.id not in game_data[field]:
                                    _ = game_data[field]
                                    _.append(unicode(s.id))
                                    game_data[field] = _
                            else:
                                game_data[field] = [str(s.id)]
                        server.game_data = json.dumps(game_data)
                        server.save(using="write")
                except BaseException as e:
                    print s.id,e
                    s.game_data = json.dumps({"top_power":"","avg_power":"","ten_power":"","avg_level":"","sub_server":[]})
                    s.save(using="write")
                    continue
            print u"现在时间:",datetime.datetime.now()
            time.sleep(6400)
