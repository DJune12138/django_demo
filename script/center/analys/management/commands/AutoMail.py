#coding=utf-8

from django.core.management import BaseCommand
from models.channel import Channel
from models.pay import PayAction
import datetime,time
from django.db import connections
from views.log.statistic_module import get_center_conn
from django.db import connections
import requests,json
from django.shortcuts import HttpResponse
from models.server import Server
from models.log import DictValue
from models.game import Mail
from views.game.base import GMProtocol
import math
from util import trace_msg, str_to_datetime

# def conference_send(id):
#     audit_id = id
#     result_msg = ""
#
#     try:
#         eran_all = 0
#         for model in Mail.objects.filter(id=int(audit_id)):
#             playerIds = []
#             if model.player_id:
#                 playerIds = json.loads(model.player_id)
#             if model.status == 1:
#                 result_status = False
#                 continue
#             msg = {}
#             if model.bonus_content:
#                 msg["rw"] = [{"act": json.loads(model.bonus_content), "gn": "xx"}]
#                 dic = eval(DictValue.objects.get(dict_id=88).json_dict)  ####### 变成字典
#                 for i in msg["rw"][0]["act"]:
#                     single_earn =0
#                     if i["aID"] == 4:
#                         single_earn = i["v"] * int(dic[str(i["id"])].encode('gbk'))
#                     if  i["aID"] == 3:
#                         single_earn = round(math.ceil(i["v"]/1000))
#                     if  i["aID"] == 2 or i["aID"] == 1 :
#                         single_earn = i["v"]
#                     eran_all += single_earn
#                     # if eran_all * playerIds.__len__() > chanel_earn:
#                         # return HttpResponse('操作不成功，你的发送余额不足')
#
#             msg["m"] = model.content
#             msg["t"] = model.title
#             msg["ty"] = model.type
#             if model.type == 0:
#                 msg["arg"] = playerIds
#             elif model.type == 2:
#                 msg["arg"] = []
#                 msg["svr"] = [-1]
#             elif model.type == 3:
#                 msg["arg"] = model.channel_id
#                 msg["svr"] = [-1]
#             server_id = model.server_ids
#
#             print '==> msg: ', msg
#             gmp = GMProtocol(server_id)
#             result = gmp.send_mail(msg)
#             if result == 0:
#                 model.status = 1
#             else:
#                 model.status = 2
#
#             result_status = True if result == 0 else False
#             model.Auditor = str(model.Applicant)
#
            # if model.time_status == 1:   # 定时的邮件
            #     model.time_status = 2    #  定时已审
            #     model.order_time = datetime.datetime.now()
#             model.save()
#
#             # 获取当前渠道,然后减值
#             if result_status:  #############获取当前渠道,然后减值
#                 player_id = playerIds[0]
#                 sql = "select channel_id from player_%s where player_id =%s" % (
#                 server_id, player_id)  #############分服获取当前渠道
#                 con = Server.get_conn(server_id)  #######连接分服的数据库
#                 cur = con.cursor()
#                 cur.execute(sql)
#                 res = cur.fetchone()
#                 if res[0]:
#                     oo = Channel.objects.filter(id=list(res)[0]).first()
#                     oo.allow_earn = oo.allow_earn - eran_all * playerIds.__len__()
#                     oo.save()
#                 else:
#                     model.time_status = 3
#                 cur.close()
#                 con.commit()
#                 con.close()
#
#             # 记录日志
#             remark2 = str(msg['arg'])
#             if model.type == 2:
#                 remark2 = '全服角色'
#             elif model.type == 3:
#                 remark2 = '联远商ID'
#
#             # player_ids是个列表
#             if playerIds:
#                 for i in playerIds:
#                     gmp.save_log(model.Applicant, gmp.req_type, result,
#                                  remark1=model.content, remark2=remark2, player_id=i)
#             else:
#                 gmp.save_log(model.Applicant, gmp.req_type, result,
#                              remark1=model.content, remark2=remark2)
#
#         result_msg += "发送成功" if result_status else "发送失败或已经发送过"
#
#
#     except Exception,e:
#         result_msg = trace_msg()
#
#     return HttpResponse(result_msg)

def send_mail(id):
    '''发送邮件
    '''
    audit_id = id
    result_msg = ""
    try:
        for model in Mail.objects.filter(id=int(audit_id)):
            playerIds = []
            if model.player_id:
                playerIds = json.loads(model.player_id)

            if model.status == 1:
                result_status = False
                continue

            # msg = {}
            # if model.bonus_content:
            #     msg["rw"] = [{"act": json.loads(model.bonus_content), "gn": "xx"}]
            # msg["m"] = model.content
            # msg["t"] = model.title
            # msg["ty"] = model.type
            # if model.type == 0:
            #     msg["arg"] = playerIds
            # elif model.type == 2:
            #     msg["arg"] = []
            #     msg["svr"] = [-1]
            # elif model.type == 3:
            #     msg["arg"] = model.channel_id
            #     msg["svr"] = [-1]

            # 组织GM命令
            GM_str = '#gmMail '
            if model.type == 2:
                GM_str += '-1 '
            else:
                player_list = eval(model.player_id)
                for player in player_list:
                    GM_str += str(player) + ','
                GM_str = GM_str.rstrip(',') + ' '
            GM_str += model.title + ' ' + model.content + ' '
            if model.bonus_content:
                for award in json.loads(model.bonus_content):
                    GM_str += str(award['aID']) + ',' + str(award['id']) + ',' + str(award['v']) + ';'
                GM_str = GM_str.rstrip(';')
            else:
                GM_str = GM_str.rstrip()

            server_id = model.server_ids

            print '==> msg: ', GM_str
            gmp = GMProtocol(int(server_id))
            result = gmp.send_mail(GM_str)
            if result == 0:
                model.status = 1
            else:
                model.status = 2

            result_status = True if result == 0 else False

            model.Auditor = str(model.Applicant)
            if result_status:   # 定时的邮件
                model.time_status = 2    #  定时已审

            else:
                model.time_status = 3

            model.save()

            # 记录日志
            # remark2 = str(msg['arg'])
            if model.type == 2:
                remark2 = '全服角色'
            elif model.type == 3:
                remark2 = '联远商ID'
            else:
                remark2 = playerIds

            # player_ids是个列表
            if playerIds:
                for i in playerIds:
                    gmp.save_log(model.Applicant, gmp.req_type, result,
                                 remark1=model.content, remark2=remark2, player_id=i)
            else:
                gmp.save_log(model.Applicant, gmp.req_type, result,
                             remark1=model.content, remark2=remark2)

        result_msg += "发送成功" if result_status else "发送失败或已经发送过"

    except Exception, e:
        result_msg = trace_msg()

    return HttpResponse(result_msg)


class Command(BaseCommand):
    '''定时审核定时邮件
    '''

    def handle(self, *args, **options):

        while True:
            try:

                con = get_center_conn()  #######连接中央服的数据库
                cur = con.cursor()
                sql= "SELECT id,server_ids  from mail_list WHERE time_status = 1 AND NOW() > order_time"
                print sql
                cur.execute(sql)
                res = cur.fetchall()
                if res:
                    for r in res:
                        # url = "http://127.0.0.1:8002/game/mail_list/conference_send_mail?server_id=%s&id=%s" % (r[1], r[0])
                        # res = requests.get(url)
                        result= send_mail(r[0])
                        print result
                cur.close()
                con.close()

            except Exception as e:
                print e

            time.sleep(600)
