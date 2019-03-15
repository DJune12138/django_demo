# -*- coding: utf-8 -*-
#
# 发送邮件操作相关
#
import os
import hashlib
import zipfile
import time
import math

from PIL import Image
# django 常用导入
# =========================================
from django.core.urlresolvers import reverse
from django.db import connection, connections
from django.db.models import Q
from django.utils.html import conditional_escape
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response, HttpResponseRedirect
from django.views.generic import ListView, View
from django.template import loader, RequestContext

# ==========================================
from settings import STATIC_ROOT
from util import trace_msg, str_to_datetime
from models.log import Log, DictValue
# from models.center import Server, Notice, Group
from cache import center_cache
from views.base import getConn, json_response
from util.http import http_post
import json
import datetime
import time
from urls.AutoUrl import Route
from views.widgets import get_group_servers_dict, get_agent_channels_dict
from .base import GMProtocol, GMActionType
from util.threadpoll import ThreadPool
from views.log.query import query_view
from views.game.base import GMProtocol
from models.game import Mail
from models.calevents import Calevents
from views.base import notauth
from models.channel import Channel
from views.log.statistic_module import get_center_conn
from models.server import Server


@Route()
def mail_list(request):
    '''邮件列表
    '''
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    query_name = '审核待发送邮件'

    return query_view(request, query_name=query_name)


@Route()
def conference_mail_list(request):
    '''邮件列表
    '''
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    query_name = '审核待发送邮件-copy'

    return query_view(request, query_name=query_name)


# @Route()
# def conference_mail_list(request):
#     '''邮件列表
#     '''
#     server_id = int(request.REQUEST.get('server_id', '') or 0)
#     query_name = '审核待发送邮件-copy'
#
#     return query_view(request, query_name=query_name)


@Route()
def send_mail(request):
    '''发送邮件审核
    '''
    audit_ids = [int(request.REQUEST.get("id", '') or 0)]
    server_id = int(request.REQUEST.get("server_id", "") or 0)

    result_msg = ""
    if request.method == 'POST':
        # 批量发送
        audit_ids = request.REQUEST.get("ids", "")
        if audit_ids:
            audit_ids = json.loads(audit_ids)
            result_msg = "批量"

    if not audit_ids:
        result_msg = "无此ID或已发送"
        return HttpResponse(result_msg)

    try:
        for audit_id in audit_ids:
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

                model.Auditor = str(request.admin.id)
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
                        gmp.save_log(request.admin.id, gmp.req_type, result,
                                     remark1=model.content, remark2=remark2, player_id=i)
                else:
                    gmp.save_log(request.admin.id, gmp.req_type, result,
                                 remark1=model.content, remark2=remark2)

        result_msg += "发送成功" if result_status else "发送失败或已经发送过"

    except Exception, e:
        result_msg = trace_msg()

    return HttpResponse(result_msg)


@Route()
def check_player_channel(request):
    '''检查用户拥有的渠道是否和发送的玩家一致'''

    cha_list = list(request.admin.role.first().resource_ids.get('channel', ''))  # 用户拥有的渠道
    player = request.REQUEST.get("player", '')
    player_ids = eval(player)
    print player_ids
    if isinstance(player_ids, int):
        player_ids = [player_ids]
    try:
        vv = []

        for i in player_ids:
            server_id = i >> 20
            print i, server_id
            sql = "select channel_id from player_%s where player_id =%s" % (server_id, i)  #############分服获取当前渠道
            con = Server.get_conn(server_id)  #######连接分服的数据库
            cur = con.cursor()
            cur.execute(sql)
            res = cur.fetchall()
            print 'oooooooooooooo', cha_list, player, res[0][0], server_id, vv.__len__()
            if res[0][0] and int(res[0][0]) in cha_list:

                if vv.__len__() == 0:
                    vv.append(int(res[0][0]))
                else:
                    if int(res[0][0]) == vv[0]:
                        pass
                    else:
                        return HttpResponse(i)
            else:
                return HttpResponse(i)
            cur.close()
            con.close()
        return HttpResponse(0)

    except Exception, e:
        print e
        return HttpResponse(33)


@Route()
def conference_send_mail(request):
    '''公会邮件审核操作'''
    audit_ids = [int(request.REQUEST.get("id", '') or 0)]
    server_id = int(request.REQUEST.get("server_id", "") or 0)
    result_msg = ""
    if request.method == 'POST':
        # 批量发送
        audit_ids = request.REQUEST.get("ids", "")
        if audit_ids:
            audit_ids = json.loads(audit_ids)
            result_msg = "批量"

    if not audit_ids:
        result_msg = "无此ID或已发送"
        return HttpResponse(result_msg)

    try:
        ##################全部的价值，这里来判断是否可以审核
        # cha_list = list(request.admin.role.first().resource_ids['channel'])
        for audit_id in audit_ids:
            # channel_li = Channel.objects.filter(id__in=cha_list)
            # chanel_earn = 0
            # for v in channel_li:
            #     chanel_earn += v.allow_earn
            ########################用户的运行的全部价值
            eran_all = 0
            for model in Mail.objects.filter(id=int(audit_id)):
                playerIds = []
                if model.player_id:
                    playerIds = json.loads(model.player_id)

                if model.status == 1:
                    result_status = False
                    continue
                msg = {}

                moch = model.channel_id
                channel_si = Channel.objects.filter(id=int(moch))[0]

                print channel_si.allow_earn
                if model.bonus_content:
                    msg["rw"] = [{"act": json.loads(model.bonus_content), "gn": "xx"}]
                    ####################################
                    dic = eval(DictValue.objects.get(dict_id=88).json_dict)  ####### 变成字典
                    for i in msg["rw"][0]["act"]:
                        single_earn = 0
                        if i["aID"] == 4:
                            single_earn = i["v"] * int(dic[str(i["id"])].encode('gbk'))
                        if i["aID"] == 3:
                            single_earn = math.ceil(i["v"] / 1000)
                        if i["aID"] == 2 or i["aID"] == 1:
                            single_earn = i["v"]
                        eran_all += single_earn
                        if eran_all * playerIds.__len__() > channel_si.allow_earn:
                            return HttpResponse('操作不成功，渠道 %s 发送余额不足' % (channel_si.name))
                # print 'pppppp',eran_all * playerIds.__len__(),channel_si.allow_earn
                msg["m"] = model.content
                msg["t"] = model.title
                msg["ty"] = model.type
                if model.type == 0:
                    msg["arg"] = playerIds
                elif model.type == 2:
                    msg["arg"] = []
                    msg["svr"] = [-1]
                elif model.type == 3:
                    msg["arg"] = model.channel_id
                    msg["svr"] = [-1]

                server_id = model.server_ids

                print '==> msg: ', msg
                gmp = GMProtocol(server_id)
                result = gmp.send_mail(msg)
                if result == 0:
                    model.status = 1
                else:
                    model.status = 2

                result_status = True if result == 0 else False

                model.Auditor = str(request.admin.id)
                if model.time_status == 1:
                    model.time_status = 0
                    model.order_time = datetime.datetime.now()
                model.save()

                # 获取当前渠道,然后减值
                if result_status:  #############获取当前渠道,然后减值
                    player_id = playerIds[0]
                    sql = "select channel_id from player_%s where player_id =%s" % (
                    server_id, player_id)  #############分服获取当前渠道
                    con = Server.get_conn(server_id)  #######连接分服的数据库
                    cur = con.cursor()
                    cur.execute(sql)
                    res = cur.fetchone()
                    if res[0]:
                        oo = Channel.objects.filter(id=list(res)[0]).first()
                        oo.allow_earn = oo.allow_earn - eran_all * playerIds.__len__()
                        oo.save()

                    cur.close()
                    con.commit()
                    con.close()

                # 记录日志
                remark2 = str(msg['arg'])
                if model.type == 2:
                    remark2 = '全服角色'
                elif model.type == 3:
                    remark2 = '联远商ID'

                # player_ids是个列表
                if playerIds:
                    for i in playerIds:
                        gmp.save_log(request.admin.id, gmp.req_type, result,
                                     remark1=model.content, remark2=remark2, player_id=i)
                else:
                    gmp.save_log(request.admin.id, gmp.req_type, result,
                                 remark1=model.content, remark2=remark2)

        result_msg += "发送成功" if result_status else "发送失败或已经发送过"


    except Exception, e:
        result_msg = trace_msg()

    return HttpResponse(result_msg)
    # now = datetime.datetime.now()
    # sd = now.strftime("%Y-%m-%d %H:%M:00")
    # st = (now - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:00")  ##########每30分钟更新一次
    #
    # con = get_center_conn()  #######连接中央服的数据库
    # cur = con.cursor()
    # sql = "SELECT channel_id,sum(pay_amount),channel_key from pay_action WHERE pay_status =4 AND post_time BETWEEN '2017-07-01' and '2018-09-09' GROUP BY channel_id"
    # cur.execute(sql)
    # res = cur.fetchall()
    # print 'vvvvvvvvvvv',res
    # for r in res:
    #     try:
    #         if r[0]!=0 and r[0]!=2:
    #             print r[0]
    #             ch = Channel.objects.filter(id=r[0]).first()
    #             print int(r[1])
    #             ch.allow_earn += 10
    #             print "qqqqqqqqq",ch.allow_earn
    #             ch.save()
    #     except Exception as e:
    #         pass
    # cur.close()
    # con.commit()
    # con.close()
    #     # time.sleep(900)
    # print 'dddddddddddddddd'
    # return HttpResponse('okok')


@Route()
def del_mail(request):
    del_ids = [int(request.REQUEST.get("id", '') or 0)]

    result_msg = ""

    if request.method == "POST":
        # 批量删除
        del_ids = request.REQUEST.get("ids", "")
        if del_ids:
            del_ids = json.loads(del_ids)
            result_msg = "批量"

    if not del_ids:
        result_msg = "无此ID或已删除"
        return HttpResponse(result_msg)
    try:
        for del_id in del_ids:
            for model in Mail.objects.filter(id=del_id):
                if model.status == 1:
                    continue
                model.delete()
        result_msg += "成功删除"
    except Exception, e:
        result_msg = trace_msg()

    return HttpResponse(result_msg)
