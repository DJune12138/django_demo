#! /usr/bin/python
# -*- coding: utf-8 -*-

from models.admin import Admin
from models.center import Channel
from models.log import Log
from models.center import Server

from settings import TEMPLATE_DIRS, DATABASES
import hashlib, datetime, json, MySQLdb, urllib, os
from django.core.urlresolvers import reverse
from django.db import connections
from django.utils.html import conditional_escape
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import redirect, render_to_response, HttpResponseRedirect
import functools
from django.views.generic import ListView, View
import logging
from util import trace_msg
from models.log import DictDefine, DictValue
from urls.AutoUrl import Route
from views.widgets import get_group_servers_dict
from settings import PROJECT_ROOT, MEDIA_ROOT

_logger = logging.getLogger('root.dict')


@Route('^log/dict/list')
def dict_list(request):
    list_record = DictDefine.objects.using('read').all()

    group_servers_dict = get_group_servers_dict(request)
    return render_to_response('log/dict_list.html', locals())


@Route('^log/dict/edit/([\d]+)?')
def edit(request, id):
    id = int(id or request.GET.get('id', '') or 0)
    dict_key = request.REQUEST.get('key', '')
    if id:
        m = DictDefine.objects.using('read').get(id=id)
        if DictValue.objects.using("read").filter(dict_id=id):  # 目前只能写这么low的语句了，有空再改
            ea = DictValue.objects.using("read").get(dict_id=id)
            return render_to_response('log/dict_edit2.html', locals())
    elif dict_key:
        m = DictDefine.objects.using('read').get(key=dict_key)
    else:
        m = DictDefine()
        ea = DictValue()
        m.id = 0

    return render_to_response('log/dict_edit.html', locals())


@Route('^log/dict/save/([\d]+)?')
def save(request, id=""):
    _p = lambda x, y='': request.REQUEST.get(x, y)
    id = int(id or request.REQUEST.get('id', '') or 0)
    err_msg = ''
    print _p('earn', "")
    try:
        if id:
            m = DictDefine.objects.using('read').get(id=id)
        else:
            m = DictDefine()
        m.key = _p('key', '')
        m.name = _p('name', '')
        m.group = _p('group', '')
        m.json_dict = _p('dict', '')
        m.type = _p('type', '0')
        m.remark = _p('remark', '')
        m.save(using='write')
        if _p('earn', ""):
            ea = DictValue.objects.using("read").get(dict_id=id)
            ea.json_dict = _p('earn', "")
            ea.dict_name = _p('name', '')
            ea.save(using='write')
    except Exception, e:
        err_msg = trace_msg()
    return render_to_response('feedback.html', locals())


@Route('^log/dict/del/([\d]+)?')
def delete(request, id=""):
    id = id or request.GET.get('id', '')
    err_msg = ""
    if id:
        DictDefine.objects.filter(id=id).delete()
    else:
        err_msg = 'delete error !'
    return render_to_response('feedback.html', locals())


@Route('^log/dict/interface')
def interface(request):
    '''获取字典的接口
    '''
    _p = lambda x, y='': request.GET.get(x, request.POST.get(x, y))
    key = _p('key', '')
    _r = "{}"

    if key:
        o = DictDefine.objects.filter(key=key)
        _r = o[0].get_json_data()

    return HttpResponse(_r)


def sync_dict_to_game_server(server_id):
    '''同步字典到游戏服务表
    '''
    err_msg = ''
    values = []
    the_delete_sql = 'truncate table log_dict'
    the_insert_sql = '''INSERT INTO log_dict(`log_type`,`log_time`,`log_name`,`log_previous`,`log_now`)values(0,NOW(),%s,%s,%s)'''
    for d in DictDefine.objects.filter(type=0):
        try:
            dict_key = d.key
            for k, v in d.dict.iteritems():
                values.append((dict_key, k, v))
        except:
            err_msg = trace_msg()
    if values:
        try:
            conn = Server.get_conn(server_id)
            conn.autocommit(0)
            cur = conn.cursor()
            cur.execute(the_delete_sql)
            cur.executemany(the_insert_sql, values)
            conn.commit()
            conn.close()
        except:
            err_msg = trace_msg()
    return err_msg


@Route('^log/dict/sync_game_server')
def sync_dict_to_game_server_view(request):
    _r = {"code": -1, "msg": ""}
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    if server_id:
        _r['msg'] = sync_dict_to_game_server(server_id)
        if not _r['msg']:
            _r['code'] = 0
    return HttpResponse(json.dumps(_r))
