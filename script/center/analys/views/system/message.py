# encoding=utf-8

import json
import datetime
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Q
from urls.AutoUrl import Route
from models.message import Message, MessageStatus

@Route()
def message_list(request):
    user = request.admin

    req_type = int(request.GET.get("type", "0")) or 0     # 0获取消息数量，1获取消息列表
    msg_type = int(request.GET.get("msg_type", "0")) or 0
    show_all = int(request.GET.get("show_all", "0")) or 0
    sdate = request.GET.get("sdate")
    edate = request.GET.get("edate")

    td = datetime.date.today()
    if not sdate:
        sdate = td - datetime.timedelta(days=7)
    if not edate:
        edate = td + datetime.timedelta(days=1)

    if show_all:
        msg_list = Message.objects.all()
    else:
        msg_list = Message.objects.filter(Q(time__gte=sdate) & Q(time__lte=edate))

    msg_category = {}
    unread_total = 0   # 消息总计
    for msg in msg_list:
        msg.formattime = msg.time.strftime('%Y-%m-%d %H:%M:%S')
        if not msg.messagestatus_set.filter(admin_id=user.id):
            msg.is_read = 0
            unread_total += 1
        else:
            msg.is_read = 1
        msg_category.setdefault(int(msg.type), []).append(msg)

    cate_count = []
    for k,v in msg_category.items():
        unread_cate_count = 0
        for i in v:
            if i.is_read == 0:
                unread_cate_count += 1
        cate_count.append({
            "type" : int(k),
            "name" : Message.get_display_name("type", int(k)),
            "unread_count" : unread_cate_count,
        })

    argus = {}
    argus["total"] = unread_total
    argus["record"] = msg_category
    argus["msg_type"] = msg_type
    argus["show_all"] = show_all
    argus["cate_count"] = cate_count

    if req_type == 0:
        load_template = "system/message.html"
    else:
        load_template = "system/message_list.html"
    return render_to_response(load_template, argus)


@Route()
def upgrade_message(request, status=1):
    msg_id = request.GET.get("msg_id")
    user = request.admin

    if not msg_id:
        return HttpResponse(status=500)

    is_exist = MessageStatus.objects.filter(Q(msg_id=msg_id) & Q(admin_id=user.id))
    if len(is_exist):
        return HttpResponse(1)

    ms = MessageStatus(msg_id=msg_id, admin_id=user.id, read_time=datetime.datetime.now())
    ms.save()

    return HttpResponse(0)