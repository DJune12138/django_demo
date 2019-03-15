# -*- coding: utf-8 -*-
#
# 发送邮件操作相关
#
import os
import hashlib
import zipfile
import time

from PIL import Image
# django 常用导入
#=========================================
from django.core.urlresolvers import reverse
from django.db import connection, connections
from django.db.models import Q
from django.utils.html import conditional_escape
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render_to_response, HttpResponseRedirect
from django.views.generic import ListView, View
from django.template import loader, RequestContext

#==========================================
from settings import STATIC_ROOT
from util import trace_msg, str_to_datetime
from models.log import Log
from models.center import Server, Notice, Group
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


@Route()
def mail_list(request):
    '''邮件列表
    '''
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    query_name = '审核待发送邮件'

    return query_view(request, query_name=query_name)


@Route()
def send_mail(request):
    '''发送邮件
    '''
    audit_ids = [int(request.REQUEST.get("id", '') or 0)]
    server_id = int(request.REQUEST.get("server_id", "") or 0)

    result_msg = ""
    if request.method == 'POST':
        #批量发送
        audit_ids = request.REQUEST.get("ids","")
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

                msg = {}
                if model.bonus_content:
                    msg["rw"] = [{"act": json.loads(model.bonus_content), "gn": "xx"}]
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
                model.save()

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


@Route()
def del_mail(request):
    del_ids = [int(request.REQUEST.get("id", '') or 0)]

    result_msg = ""

    if request.method == "POST":
        # 批量删除
        del_ids = request.REQUEST.get("ids","")
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
