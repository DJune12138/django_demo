# -*- coding: utf-8 -*-
#服务器相关
#=========================================
from django.core.urlresolvers import reverse
from django.db import connection,connections
from django.db.models import Q
from django.utils.html import conditional_escape
from django.http import HttpResponse
from django.template.context import RequestContext
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================


from models.center import Notice
from models.server import Server,Group
from models.server import KuaFuServer
from models.game import BattleList
from models.channel import Channel,Agent
from views.base import  OperateLogManager
from views.widgets import get_agent_channels_dict,get_group_servers_dict
from settings import STATIC_ROOT,APP_LABEL
from urls.AutoUrl import Route
from util import trace_msg

from models.log import Log
from models.admin import Admin
import os, json, copy, datetime,re
from models.log import DictDefine
from views.game.base import GMProtocol
from django.db.models import Q
import threading
import functools,time


def save_log(path,Type,msg):
    BASE_LOG_PATH = os.path.join(APP_LABEL,path).replace('\\','/')
    now = time.strftime("%Y%m%d")
    # 本机测试
    # pwd = os.path.join(os.getcwd(),"/").replace('\\','/')
    # pwd = os.getcwd() + "/"
    # path = pwd + BASE_LOG_PATH + '%s.log'%(now)
    # 上传
    path =  BASE_LOG_PATH + '%s.log'%(now)

    now_time = time.strftime("%Y-%m-%d %H:%M:%S")
    msg =  now_time + ' [%s] '%(Type) + '%s'%msg
    msg += '\n'
    try:
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path,'a') as L:
            L.write(msg)
    except BaseException as e:
        print 'server > battle_server > insert save_log error,%s'%e

@Route()
def battle_server_list(request, group_id=0):
    '''跨服列表
    '''
    group_id = int (request.REQUEST.get('group_id','') or 0)
    list_record = BattleList.objects.all().order_by('create_time')
    SERVER_NAME = DictDefine.get_dict_for_key("server_name")
    server_name = {}
    for k,v in SERVER_NAME.iteritems():
        server_name[int(k)] = v

    STATUS_CHOICES = KuaFuServer.STATUS_CHOICES
    for item in list_record:
        item.score = int(item.f1 or 0) + int(item.f2 or 0) + int(item.f3 or 0)
    return render_to_response('server/battle_server_list.html', locals())


@Route()
def battle_server_first(request):
    '''
    第一阶段排序:按开服时间三个服一组，一共3组,多余的不管'''
    server_ids = request.REQUEST.getlist('sid')
    _r = {"code":1,"msg":"没有选择服务器"}
    if not server_ids:
        return HttpResponse(json.dumps(_r))
    group = {"A":[1,2,3],"B":[4,5,6],"C":[7,8,9]}
    server_ids = server_ids[0:server_ids.__len__()//9 * 9]
    count = 0
    _count = 0
    
    for _ in range(server_ids.__len__()):
        try:
            model = BattleList.objects.filter(server = int(server_ids[_]))
            model = model[0]
            if not model:
                continue
            for k,v in group.iteritems():
                if _% 9 + 1 in v:
                    model.sort = _count + 1
                    count += 1
                    _count = count // 9 
                    model.group = k
                    model.sub_group = v[server_ids.index(server_ids[_])%3]
                    model.last_time = datetime.datetime.now()
                    model.save(using='write')
                    _r["code"] = 0
                    _r["msg"] = "保存成功"
        except BaseException as e:
            print e
            _r["code"] = 1
            _r["msg"] = '%s'%e
            continue
    return HttpResponse(json.dumps(_r))

@Route()
def save_battle_single(request):
    sid = request.REQUEST.get("sid")
    new_group = request.REQUEST.get("new_group")
    new_sub_group = request.REQUEST.get("new_sub_group")

    _r = {"code":1,"msg":"没有参数"}
    if not sid or not new_group or not new_sub_group:
        return HttpResponse(json.dumps(_r))

    try:
        model = BattleList.objects.filter(server = int(sid))
        model = model[0]
        model.group = new_group.upper()
        model.sub_group = abs(int(new_sub_group.strip()))
        model.last_time = datetime.datetime.now()
        model.save(using='write')
        return HttpResponse(json.dumps({"code":0,"msg":"保存成功"}))
    except BaseException as e:
        return HttpResponse(json.dumps({"code":1,"msg":"%s"%e}))


@Route()
def delete_battle_single(request):
    sid = request.REQUEST.get("sid")
    _r = {"code":1,"msg":"没有参数"}
    if not sid:
        return HttpResponse(json.dumps(_r))

    try:
        model = BattleList.objects.filter(server = int(sid))
        model = model[0]
        model.delete()
        return HttpResponse(json.dumps({"code":0,"msg":"删除成功"}))
    except BaseException as e:
        return HttpResponse(json.dumps({"code":1,"msg":"%s"%e}))

@Route()
def save_battle_many(request):
    params = request.REQUEST.get("params",{})
    action = request.REQUEST.get("action",False)
    send_to_server = request.REQUEST.get("send_to_server",[])
    params = json.loads(params)
    send_to_server = json.loads(send_to_server)
    msg = ""
    print params,send_to_server,action
    if action == "change_sort":
        sort = int(request.REQUEST.get("sort",0))
    if action == "change_version":
        version = int(request.REQUEST.get("ver",0))
    if action == "send_reward":
        for s in params:
            gmp = GMProtocol(int(s))
            result = gmp.send_battle_reward()
            if result == 0:
                msg = json.dumps({"code":0,"msg":"发送成功"})
                model = BattleList.objects.filter(server=int(s))[0]
                model.status = 2
                model.save(using='write')
            else:
                msg = json.dumps({"code":1,"msg":"发送失败"})
        return  HttpResponse(msg)

    for k,v in params.iteritems():
        try:
            model = BattleList.objects.filter(server = int(k))
            model = model[0]
            if action == "change_sort":
                model.sort = sort
            elif action == "change_version":
                model.version = version
            if v[0] and v[1]:
                model.group = v[0].upper()
                model.sub_group = v[1].strip()
            if send_to_server[-1]["run_time"]:
                model.run_time = send_to_server[-1]["run_time"]
            model.last_time = datetime.datetime.now()
            model.save(using='write')
        except BaseException as e :
            print e
            continue

    #保存完批量发送
    if send_to_server and not send_to_server[-1]["run_time"]:
        print send_to_server.pop()
        msg = send_all_battle(request.admin.id,params=params,send_type=send_to_server)

    if msg:
        print msg
        return HttpResponse(json.dumps({"code":0,"msg":"%s没主服发送失败"%json.dumps(msg)}))
    return HttpResponse(json.dumps({"code":0,"msg":"发送成功"}))

@Route()
def battle_server_edit(request, server_id=0):
    '''服务器编辑
    '''
    server_id = int (request.REQUEST.get('sid','') or request.REQUEST.get('server_id','') or 0)
    is_copy = request.REQUEST.get('copy','')
    if server_id:
        model = KuaFuServer.objects.using('read').get(id=server_id)
        if is_copy :
            model.name = ''
            model.game_addr = ''
            model.model = ''
    else:
        model = KuaFuServer()
        model.id = 0
    list_group = Group.objects.all()
    return render_to_response('server/battle_server_edit.html', locals())

@Route()
def battle_server_remove(request, server_id=0):
    '''服务器删除
    '''
    err_msg = ''
    server_ids = request.REQUEST.getlist('sid')

    try:
        for model in KuaFuServer.objects.filter(id__in=server_ids):
            #model.channel.clear()
            model.delete()
    except Exception, e:
        err_msg = trace_msg()
    return render_to_response('feedback.html',locals())

@Route()
def battle_server_save(request, server_id=0):
    server_id = server_id or int(request.REQUEST.get('sid','') or '0')
    new_server_id = int(request.REQUEST.get('new_server_id', '') or 0 )
    model = None
    source_model = None
    is_add = True

    if server_id :
        model = KuaFuServer.objects.get(id=server_id)
        source_model = copy.copy(model)
        is_add = False

    if not model :
        model = KuaFuServer()
        model.id = new_server_id

    #list_group = Group.objects.all()
    exists = False
    update_id = False
    err_msg = ''

    if server_id != new_server_id:
        exists = KuaFuServer.objects.filter(id = new_server_id).exists()
        if exists:
            err_msg = '保存的服务器ID已存在'
            return render_to_response('feedback.html', locals())
        else:
            update_id = True

    model.client_ver = request.POST.get('client_ver', '')
    model.name = request.POST.get('name', '')
    model.status = int(request.POST.get('status', '2'))
    model.commend = int(request.POST.get('commend', '2'))
    model.require_ver = int(request.POST.get('require_ver', '0'))
    model.game_addr = request.POST.get('game_addr', '')
    model.game_port = int(request.POST.get('game_port', '2008'))
    model.report_url = request.POST.get('report_url', '')
    model.log_db_config = request.POST.get('log_db_config', '')
    model.remark = request.POST.get('remark', '')
    model.order = int(request.POST.get('order', '0'))
    model.json_data = request.POST.get('json_data', '')
    model.alias = request.REQUEST.get('alias','')
    create_time = request.POST.get('create_time', '')
    if create_time == '':
        create_time = datetime.datetime.now()
    else:
        create_time = datetime.datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S')
    model.create_time = create_time

    if not exists:
        if model.name != '' and model.game_addr != '':
            try:
                #修改ID
                old_server = copy.copy(model)
                if update_id:
                    model.id = new_server_id
                model.save()

                #group_ids = request.POST.getlist('group_id')
                #group_ids = [int(x) for x in group_ids]


                #for group_model in list_group:
                #    if group_model.id in group_ids:
                #        group_model.server.add(model)
                #    else:
                #        group_model.server.remove(model)

                #前面保存没有出错
                if update_id:
                    old_server.status = KuaFuServer.Status.DELETED
                    old_server.save()

            except Exception, e:

                err_msg = trace_msg()

        else:
            err_msg = '填写必要数据!'
    return render_to_response('feedback.html', locals())



@Route()
def battle_server_status_edit(request):
    _r = {"code":1}
    action =  request.REQUEST.get('action','')
    server_list = request.POST.getlist('sid')
    if not server_list:
        return HttpResponse('没有选择服务器!')
    try:
        datas = KuaFuServer.objects.filter(id__in=server_list)

        if action == 'change_status': #修改服务器状态
            status = int(request.POST.get('serv_status','') or 0)

            datas.using('write').update(status=status)
            if status > 0:
                post_tip = request.POST.get('weihuTip', '')
                for i in datas:
                    sid, jsondb = i.id, i.json_data
                    try:
                        jsondb = json.loads('{%s}' % jsondb) if jsondb else {}
                    except Exception, e:
                        return HttpResponse("无效的Json数据:%s",e)
                    if status == 1:
                        if post_tip:
                            jsondb.update({"weihuTip" : post_tip})
                    else:
                        if 'weihuTip' in jsondb:
                            jsondb.pop('weihuTip')
                    KuaFuServer.objects.using('write').filter(id=sid).update(json_data=json.dumps(jsondb, ensure_ascii=False)[1:-1])

        elif action == 'change_version': #修改服务器版本
            ver = int(request.POST.get('ver', '-99'))
            datas.using('write').update(require_ver=ver)
        _r["code"] = 0
        _r["msg"] = '修改成功!'
    except:
        _r["msg"] = trace_msg()

    return HttpResponse(json.dumps(_r))

def async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        my_thread.setDaemon(True)
        my_thread.start()
    return wrapper

# @async
def send_all_battle(log_user,params=None,send_type=None):
    servers = BattleList.objects.all()
    kuafu_map = DictDefine.get_dict_for_key("kuafu_type")
    result = []
    save_log('logs/server/battle_server/','params',"%s"%params)
    for s in servers:
        if not s.group or not s.sort:
            continue
        if params:
            if s.server not in [int(x) for x in params.keys()]:
                continue
        base_query = Q(group=s.group) & Q(sort=s.sort)
        other_server = BattleList.objects.filter(base_query)
        server_list = []
        master_server = 0


        for _s in other_server:
            if int(_s.sub_group) == 1:
                master_server = _s.server
            server_list.append(_s.server)

        if not master_server:
            msg = u'%s服 没有主服 配置:大组-%s 分区-%s,分组-%s'%(s.server,s.sort,s.group,s.sub_group)
            save_log('logs/server/battle_server/','error',msg)
            result.append(s.server)
            for t in send_type:
                write_kuafu_log(log_user,t,s.server,s.sort,s.group,s.sub_group,msg,1)
            continue

        gmp = GMProtocol(int(s.server))
        _result = gmp.send_battle_server(master_server,server_list,send_type)
        if _result == 0:
            s.f8 = "success"
            s.last_time = datetime.datetime.now()
            s.status = 1
            s.save()
            msg = u'%s服 已发送 配置:大组-%s 分区-%s,分组-%s'%(s.server,s.sort,s.group,s.sub_group)
            print msg

            save_log('logs/server/battle_server/','success',msg)

            for t in send_type:
                write_kuafu_log(log_user,t,s.server,s.sort,s.group,s.sub_group,msg,0)
    return result



def write_kuafu_log(log_user,log_type,server_id,sort,group,sub_group,msg,log_result):
    try:
        Log._meta.db_table = 'log_kuafu'
        log = Log()
        log.log_user = log_user
        log.f8 = log_type
        log.log_server = server_id
        log.log_time = datetime.datetime.now()
        log.f1 = sort # 大组
        log.f2 = group # 分区
        log.f3 = sub_group # 分组
        log.f6 = msg
        log.log_result = log_result
        log.save(using='write')
    except BaseException as e:
        print "views --> server -->  battle_server --> write_kuafu_log error:%s"%e


