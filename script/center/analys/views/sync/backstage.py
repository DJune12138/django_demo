# -*- coding: utf-8 -*-
#
#同步模型相关
#
#django 常用导入
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect,render
from django.views.generic import ListView,View
from django.template import loader, RequestContext
#==========================================

from util import trace_msg
import cPickle as pickle
import urllib
import json
from hashlib import md5
from views.base import getConn
from models.log import  LogDefine, Log, DictDefine
from models.gm import GMDefine
from models.query import Query
from models.statistic import StatisticNew  
from models.menu import Menu
from util.http import http_post
from util import filter_sql
from django.core.serializers import serialize,deserialize
import MySQLdb
from views.base import notauth

_MODULES = {'1': LogDefine, '2': Query,'3':DictDefine,'4':Menu,'5':StatisticNew,'6':GMDefine}
_AUTHKEY = '122333444455555$'

@notauth
def backstage_list(request):
    form_operation = request.method
    operation_info = getattr(request, form_operation, None)
    model_id = None
    backs_id = None
    if operation_info:
        error_msg = ''
        model_id = operation_info.get('Modelid', '')
        backs_id = operation_info.get('Servid', '')     #接收到字符串形式的若干id值
        is_remote = int(operation_info.get('is_remote', 0))     #远程获取其他后台数据标识
        db_list = None
        if is_remote:
            backsData = get_backstage_data(bid=backs_id)
            back_url = backsData['url'] + 'sync/backstage/'
            try:
                response = http_post(back_url, urllib.urlencode({"Modelid":model_id, "Servid":backs_id}), timeout_param=60)
                return HttpResponse(response)
            except:
                error_msg = "请求失败."
        else:
            model = _MODULES.get(model_id)
            if model_id:
                db_list = model.objects.using('read').all().order_by('-id')
            else:
                error_msg = "请求失败."

        return render_to_response('log/sync_backstage_push.html', {'db_list':db_list, 'error':error_msg})

    serv_list = get_backstage_data()

    model_list = {}
    for k, v in _MODULES.iteritems():
        model_list[k] = v._meta.db_table

    results = {}
    results['model_id'] = model_id
    results['backs_id'] = backs_id
    results['serv_list'] = serv_list
    results['model_list'] = model_list

    return render_to_response("log/sync_backstage_list.html", results)

def backstage_edit(request):
    sync_id = int(request.GET.get('sync_id', '') or 0)

    edit_db = None
    #是否通过编辑按钮进入
    if sync_id:
        edit_db = get_backstage_data(bid=sync_id)

    is_post = True if request.POST else False   #是否提交了数据
    if is_post:
        conn = getConn()
        cursor = conn.cursor()

        backstage_name = request.POST.get('bs_name', '')
        backstage_url = request.POST.get('url', '')
        backstage_key = request.POST.get('key', '')

        if edit_db:
            sql = "UPDATE log_backstage SET f1='%s',f2='%s',f3='%s' WHERE id='%s'" % (backstage_name, backstage_url, backstage_key, sync_id)
        else:
            sql = filter_sql("INSERT INTO log_backstage(log_user,log_type,f1,f2,f3,log_time) VALUES (1,1,'%s', '%s', '%s', NOW())" % (backstage_name, backstage_url, backstage_key))

        try:
            cursor.execute(sql)
            if not edit_db:
                sync_id = conn.insert_id()  #添加操作时，获取新增ID
        except MySQLdb.Warning,e:
            pass
        finally:
            cursor.close()
            conn.close()      

    params = {}
    if sync_id:
        params['id'] = sync_id if edit_db or is_post else None
        params['name'] = edit_db['name'] if not is_post else backstage_name
        params['url'] = edit_db['url'] if not is_post else backstage_url
        params['key'] = edit_db['key'] if not is_post else backstage_key


    return render_to_response("log/sync_backstage_edit.html", {'data': params})

def backstage_remove(request):
    sync_id = int(request.GET.get("sync_id", 0))
    is_del = True if sync_id else False

    #删除操作
    if is_del:
        conn = getConn()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM log_backstage WHERE id='%s'" % sync_id)
            conn.commit()
        except:
            err_msg = trace_msg()
        conn.close()
    return render_to_response('feedback.html',locals())

def backstage_push(request):
    model_id = request.GET.get('Modelid', 0)
    serv_id = int(request.GET.get('Servid', 0))
    push_id = int(request.GET.get('Pushid', 0))
    is_local = int(request.GET.get('is_local', 0))  #本地同步标识

    syncMod = _MODULES.get(str(model_id))   #根据传入的model_id获取数据模型

    if not syncMod or not serv_id or not push_id:
        return HttpResponse('{"code": 1, "msg": "缺少请求所需参数"}')

    serv_info = get_backstage_data(bid=serv_id)

    serv_url = serv_info['url']
    if not serv_url:
        return HttpResponse('{"code": 1, "msg": "访问地址不存在"}')

    if is_local:
        #从指定后台获取数据同步至本地
        post_datas = http_post(serv_url + 'sync/backstage/remotedb', urllib.urlencode({"Modelid":model_id, "Pushid": push_id}))
        sync_mods = deserialize('json',post_datas)
        for m in sync_mods:
            m.save()
        result = '{"code": 0}'
    else:
        #本地数据推送至其他后台
        push_db = syncMod.objects.get(id=push_id)  #获取推送数据
        post_datas = pickle.dumps(push_db)

        hashObj = md5()
        hashObj.update(post_datas + model_id + _AUTHKEY)

        #pickle序列化模型和数据

        post_params = urllib.urlencode({'model': model_id, 'datas':post_datas, 'sign':hashObj.hexdigest()})

        # serv_url = 'http://127.0.0.1:90/sync/backstage/dosync'  #测试硬编码
        try:
            result = http_post(serv_url + 'sync/backstage/dosync', post_params, timeout_param=60)
        except Exception, e:
            return HttpResponse('{"code": 1, "msg": "http_post: %s"}' % e)

    return HttpResponse(result)

@notauth
def do_backstage_sync(request):
    model_id = request.POST.get('model', None)
    datas = request.POST.get('datas', None)
    recept_auth = request.POST.get('sign', None)
    is_success = True
    error_msg = ''

    hashObj = md5()
    hashObj.update(datas + model_id + _AUTHKEY)

    if str(recept_auth) == str(hashObj.hexdigest()):
        try:
            sync_data = pickle.loads(str(datas))
            sync_data.save()
        except Exception,e:
            error_msg = str(e)
            is_success = False
    else:
        error_msg = "auth key is invalid"
        is_success = False

    responseTxt = {'code': 0 if is_success else 1, 'msg' : error_msg}
    return HttpResponse(json.dumps(responseTxt))

@notauth
def get_remote_push_data(request):
    model_id = int(request.POST.get('Modelid', 0))
    push_id = int(request.POST.get('Pushid', 0))

    syncMod = _MODULES.get(str(model_id))
    
    push_db = syncMod.objects.filter(id=push_id)
    ret_data = serialize('json',push_db)
    
    return HttpResponse(ret_data)


#自定义函数
def get_backstage_data(bid=0):
    conn = getConn()
    cursor = conn.cursor()
    where = "id=%s" % bid if bid else "1"

    cursor.execute("SELECT id,f1,f2,f3,log_time FROM log_backstage where %s ORDER BY id ASC" %  where)
    ret = cursor.fetchall()

    serv_list = []
    for r in ret:
        serv_list.append({"id":r[0], "name":r[1], "url":r[2], "key":r[3], "time":r[4].strftime("%Y-%m-%d %H:%M:%S")})

    cursor.close()
    conn.close()

    return serv_list[0] if bid else serv_list

