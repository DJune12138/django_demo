#coding:utf-8
#定时获取服务端跨服对战数据及写入
# 1:log_chat,2:log_battle_rank


from django.core.management.base import AppCommand
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option,OptionParser
from django.db import connection,connections
from models.center import Server
from models.game import BattleList
import datetime
import time
import traceback
from util import convert_to_datetime,datetime_to_str
from util.threadpoll import ThreadPool
import threading,json
from views.game.base import GMProtocol
from django.db.models import Q


def keep_connections():
    connection_list = [connections['default'],connections['read'],connections['write']]
    for c in connection_list:
        try:c.connection.connection.ping()
        except:c.close()


class Command(BaseCommand):
    '''定时获取服务端跨服对战数据及写入
    '''
    help = '写入未在表里的服务器,自动获取服务端数据'

    def handle(self,*args,**kwargs):
        print u'正在查询是否有新服务器'
        self.add_new_server()
        print u'结束查询'

        # print u'正在剔除关闭的服务器'
        # self.del_old_server()
        # print u'结束剔除'
        
        while True:
            try:
                now = datetime.datetime.now()
                keep_connections()

                self.send_battleList()
                if now.minute < 1:
                    print u'当前时间:',now
                    print u'正在查询是否有新服务器'
                    self.add_new_server()
                    print u'结束查询'

                    # print u'正在剔除关闭的服务器'
                    # self.del_old_server()
                    # print u'结束剔除'

                if now.hour == 0 and now.minute < 1:
                    print u'开始获取积分'
                    self.get_score()
                    print u'结束获取积分'

                time.sleep(60)
                     
            except BaseException as e:
                print e
                continue

    def add_new_server(self):
        '''
        添加没加到表里的服务器'''
        model = None
        server_list = Server.objects.filter(status__in = [2,3,4])
        for server in server_list:
            try:
                if server.master_id == server.id:
                    model = BattleList.objects.filter(server = server.id)
                    if not model:
                        print u"正在添加%s 服务器"%server.id
                        model = BattleList()
                        model.server = server.id
                        model.create_time = server.create_time
                        model.last_time = datetime.datetime.now()
                        model.status = 0
                    else:
                        model = model[0]
                        model.create_time = server.create_time
                        model.last_time = datetime.datetime.now()
                    game_data = json.loads(server.game_data)
                    model.f4 = game_data["avg_power"]
                    model.f7 = game_data["ten_power"]
                    model.save(using='write')
                else:

                    model = BattleList.objects.filter(server = server.master_id)
                    if model:
                        model = model[0]
                        sub_server = json.loads(model.sub_server) if model.sub_server else []
                        sub_server.append(server.id) if server.id not in sub_server else None
                        model.sub_server = json.dumps(sub_server)
                        model.last_time = datetime.datetime.now()
                        model.save(using='write')
            except BaseException as e:
                print e

    def del_old_server(self):
        '''
        删除状态为非234的服务器'''
        model = None
        battlelist = BattleList.objects.all()
        for s in battlelist:
            try:
                model = Server.objects.filter(id=s.server)
                model = model[0]
                if (model and model.status not in [2,3,4]) or model.master_id != model.id:
                    #剔除
                    print u"正在剔除 %s 服务器"%model.id
                    s.delete()
            except BaseException as e :
                print e

    def send_battleList(self):
        servers = BattleList.objects.filter(~Q(run_time = None))
        for s in servers:
            now = datetime.datetime.now()

            if s.run_time.year != now.year:
                continue
            if s.run_time.month != now.month:
                continue   
            if s.run_time.day != now.day:
                continue   
            if s.run_time.hour != now.hour:
                continue   
            if s.run_time.minute != now.minute:
                continue
            if not s.group or not s.sort:
                continue

            print u"正在发送跨服服务器:%s 服"%(s.id)
            base_query = Q(group=s.group) & Q(sort=s.sort)
            other_server = BattleList.objects.filter(base_query)
            server_list = []
            master_server = 0
            for _s in other_server:
                if _s.sub_group == 1:
                    master_server = _s.server
                server_list.append(_s.server)

            if not master_server:
                print u'没有主服'
                continue

            gmp = GMProtocol(int(s.server))
            result = gmp.send_battle_server(master_server,server_list,[19,20,21,24])
            if result == 0:
                s.f8 = "success"
                s.last_time = datetime.datetime.now()
                s.save()
                print u'%s 已发送'%s.server

    def get_score(self,server_id=0):
        servers = BattleList.objects.all()
        Arena_score = {1:10,2:5,3:1}
        Star_score = {1:3,2:2,3:1}
        for s in servers:
            gmp = GMProtocol(int(s.server))
            result = gmp.get_battle_score(21)
            if result:
                for l in result:
                    try:
                        server = BattleList.objects.filter(server=l[1])[0]
                        server.f3 = Arena_score[l[2]] if l[2] in Arena_score else 0
                        server.last_time = datetime.datetime.now()
                        server.save()
                        print u'%s 服 战场排名为:%s,保存成功'%(l[1],l[2])
                    except BaseException as e:
                        print u'%s 服 战场排名为:%s,保存失败.%s'%(l[1],l[2],e)

            result = gmp.get_battle_score(20)
            if result:
                for l in result:
                    try:
                        server = BattleList.objects.filter(server=l[1])[0]
                        server.f2 = l[2]
                        server.last_time = datetime.datetime.now()
                        server.save()
                        print u'%s 服 荒兽数量为:%s,保存成功'%(l[1],l[2])
                    except BaseException as e:
                        print u'%s 服 荒兽数量为：%s,保存失败.%s'%(l[1],l[2],e)

            result = gmp.get_battle_score(19)
            if result:
                del result[0]
                _s = set()
                for l in result:
                    try:
                        server = BattleList.objects.filter(server=l[1])[0]
                        #算积分
                        old_score = server.f1 if server.f1 else 0
                        new_score = Star_score[int(l[1])] * int(l[2])
                        server.f1 = int(old_score) + new_score
                        server.last_time = datetime.datetime.now()
                        server.save()
                        print u'%s 服 魔星数量为:%s,保存成功'%(l[1],l[2])
                    except BaseException as e:
                        print u'%s 服 魔星数量为：%s,保存失败.%s'%(l[1],l[2],e)


            # gmp.get_battle_score(24) 炎黄
            






