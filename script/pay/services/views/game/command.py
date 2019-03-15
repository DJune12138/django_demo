#! /usr/bin/python
# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Q
from models.center import User, SafeQuestion,RebateUser,BanIpList
from models.center import Channel
from views.base import md5, getConn
from cache import center_cache
from django.db import connection
import json
import datetime
from urls.AutoUrl import Route
from views.log.query import query_view
from views.widgets import get_group_servers_dict,get_agent_channels_dict
from models.channel import Channel,Agent,ChannelOther
from views.game.base import GMProtocol

@Route()
def banip_list(request):
    request.control = control = int(BanIpList.objects.filter(id=1)[0].f1) or 0
    request.limit_count = limit_count = int(BanIpList.objects.filter(id=1)[0].f2) or 0
    return query_view(request,query_name='自动封禁IP管理')


@Route()
def modify_banip_status(request):
    status = int(request.REQUEST.get("status",2))
    if status not in [0,1]:
        return HttpResponse("状态有误！")
    try:
        model = BanIpList.objects.filter(id=1)[0]
        model.f1 = status
        model.last_time = datetime.datetime.now()
        model.save(using="write")
    except BaseException as e:
        print e
        return HttpResponse("%s"%e)
    return HttpResponse("状态更改成功,当前状态:%s"%("已开启" if status == 1 else "已关闭"))

@Route()
def addWhite(request):
    item_id = int(request.REQUEST.get('item_id',0))
    if item_id <= 1:
        return HttpResponse("id有误！")
    try:
        model = BanIpList.objects.filter(id=item_id)[0]
        model.status = 4
        model.last_time = datetime.datetime.now()
        model.save(using="write")
        if model.ip:
            users_list = User.objects.filter(last_ip=model.ip)
            for m in users_list:
                m.status = 4
                m.last_time = datetime.datetime.now()
                m.save(using="write")
    except BaseException as e:
        print e
        return HttpResponse("%s"%e)
    return HttpResponse("添加白名单成功")

@Route()
def removeWhite(request):
    item_id = int(request.REQUEST.get('item_id',0))
    if item_id <= 1:
        return HttpResponse("id有误！")
    try:
        model = BanIpList.objects.filter(id=item_id)[0]
        model.status = -3
        model.last_time = datetime.datetime.now()
        model.save(using="write")
        if model.ip:
            users_list = User.objects.filter(last_ip=model.ip)
            for m in users_list:
                m.status = -3
                m.last_time = datetime.datetime.now()
                m.save(using="write")
    except BaseException as e:
        print e
        return HttpResponse("%s"%e)
    return HttpResponse("移除白名单成功")

@Route()
def addNormal(request):
    item_id = int(request.REQUEST.get('item_id',0))
    if item_id <= 1:
        return HttpResponse("id有误！")
    try:
        model = BanIpList.objects.filter(id=item_id)[0]
        model.status = 0
        model.last_time = datetime.datetime.now()
        model.save(using="write")
        if model.ip:
            users_list = User.objects.filter(last_ip=model.ip)
            for m in users_list:
                m.status = 0
                m.last_time = datetime.datetime.now()
                m.save(using="write")
    except BaseException as e:
        print e
        return HttpResponse("%s"%e)
    return HttpResponse("解禁IP成功")

@Route()
def removeNormal(request):
    item_id = int(request.REQUEST.get('item_id',0))
    if item_id <= 1:
        return HttpResponse("id有误！")
    try:
        model = BanIpList.objects.filter(id=item_id)[0]
        model.status = 0
        model.last_time = datetime.datetime.now()
        model.save(using="write")
        if model.ip:
            users_list = User.objects.filter(last_ip=model.ip)
            for m in users_list:
                m.status = 0
                m.last_time = datetime.datetime.now()
                m.save(using="write")
    except BaseException as e:
        print e
        return HttpResponse("%s"%e)
    return HttpResponse("移出白名单成功")





@Route()
def modify_limit_num(request):
    limit_count = int(request.REQUEST.get('limit_count',0))
    if limit_count:
        try:
            model = BanIpList.objects.filter(id=1)[0]
            model.f2 = limit_count
            model.last_time = datetime.datetime.now()
            model.save(using="write")
        except BaseException as e:
            print e
            return HttpResponse("%s"%e)
        return HttpResponse("最大创角数修改为:%s 成功"%limit_count)
    return HttpResponse("无数值！") 