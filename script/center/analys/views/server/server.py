# -*- coding: utf-8 -*-
# 服务器相关
# =========================================
import socket

from django.core.urlresolvers import reverse
from django.db import connection, connections
from django.db.models import Q
from django.utils.html import conditional_escape
from django.http import HttpResponse
from django.template.context import RequestContext
from django.shortcuts import redirect, render_to_response, HttpResponseRedirect
from django.views.generic import ListView, View
from django.contrib.auth.hashers import make_password, check_password
# ==========================================


from models.center import Notice
from models.server import Server, Group, GroupList
from models.channel import Channel, Agent
from util.constant import tab_name_id
from views.base import OperateLogManager, notauth
from views.widgets import get_agent_channels_dict, get_group_servers_dict, groups_servers
from settings import STATIC_ROOT, PROJECT_ROOT, STATIC_PATH
from urls.AutoUrl import Route
from util import trace_msg, constant

from models.log import Log
from models.admin import Admin
import os
import json
import copy
import datetime
import re
import time
from views.game.base import GMProtocol
from views.server.notice import GetFileMd5
from settings import APP_LABEL
from collections import defaultdict
from models.log import DictDefine, DictValue
import requests
import urllib

# python2.6没有Counter
# from collections import Counter


LOG_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), 'analys').replace('\\', '/')
BASE_LOG_PATH = os.path.join(LOG_PATH, 'logs/MD5/').replace('\\', '/')


def LogInfo(Type, msg):
    now = time.strftime("%Y%m%d")
    # 本机测试
    # pwd = os.path.join(os.getcwd(),"/").replace('\\','/')
    # pwd = os.getcwd() + "/"
    # path = pwd + BASE_LOG_PATH + '%s.log'%(now)
    # 上传
    path = BASE_LOG_PATH + '%s.log' % (now)

    now_time = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = now_time + ' [%s] ' % (Type) + '%s' % msg
    msg += '\n'
    with open(path, 'a') as L:
        L.write(msg)


@Route()
def server_list(request, group_id=0):
    '''服务器列表
    '''
    group_id = int(request.REQUEST.get('group_id', '') or 0)
    list_record = request.admin.get_resource(
        'server').all().order_by("id", "-status", "order")

    if group_id:
        list_record = list_record.filter(group__id=group_id)

    list_group = request.admin.get_resource(
        'server_group').all().values('id', 'name')

    STATUS_CHOICES = Server.STATUS_CHOICES
    COMMEND_CHOICES = Server.COMMEND_CHOICES
    return render_to_response('server/server_list.html', locals())


@Route()
def server_msg(request, servi_id=0):
    '''服务器信息
    '''
    server_id = int(request.REQUEST.get('sid', '') or 0)
    if server_id:
        model = Server.objects.using('read').get(id=server_id)
        config = model.log_db_config
        config = json.loads(config)
        name = model.name
        game_addr = model.game_addr
        game_port = model.game_port

    return render_to_response('server/server_msg.html', locals())


@Route()
def server_edit(request, server_id=0):
    '''服务器编辑
    '''
    server_id = int(request.REQUEST.get('sid', '')
                    or request.REQUEST.get('server_id', '') or 0)
    is_copy = request.REQUEST.get('copy', '')
    if server_id:
        model = Server.objects.using('read').get(id=server_id)
        if is_copy:
            model.name = ''
            model.game_addr = ''
            model.model = ''
    else:
        model = Server()
        model.id = 0
    list_group = Group.objects.all()

    # 分组名称
    m = eval(DictValue.objects.using('read').get(dict_id=tab_name_id).json_dict)

    # 所属分组ID
    if server_id:
        tab_id = str(model.tabId)

    return render_to_response('server/server_edit.html', locals())


@Route()
def server_save(request, server_id=0):
    server_id = server_id or int(request.REQUEST.get('sid', '') or '0')
    new_server_id = int(request.REQUEST.get('new_server_id', '') or 0)
    model = None
    source_model = None
    is_add = True

    if server_id:
        model = Server.objects.get(id=server_id)
        source_model = copy.copy(model)
        is_add = False

    if not model:
        model = Server()
        model.id = new_server_id

    list_group = Group.objects.all()
    exists = False
    update_id = False
    err_msg = ''

    if server_id != new_server_id:
        exists = Server.objects.filter(id=new_server_id).exists()
        if exists:
            err_msg = '保存的服务器ID已存在'
            return render_to_response('feedback.html', locals())
        else:
            update_id = True

    if not request.POST.get("tabId"):
        err_msg = '请填入分组ID'
        return render_to_response('feedback.html', locals())

    model.tabId = int(request.POST.get("tabId") or 0)
    # model.client_ver = request.POST.get('client_ver', '') # 客户端版本
    model.name = request.POST.get('name', '')
    model.status = int(request.POST.get('status', '2'))
    model.commend = int(request.POST.get('commend', '2'))
    # model.require_ver = int(request.POST.get('require_ver', '0')) # 要求最低版本
    model.game_addr = request.POST.get('game_addr', '')
    model.game_port = int(request.POST.get('game_port', '2008'))
    model.report_url = request.POST.get('report_url', '')
    model.log_db_config = request.POST.get('log_db_config', '')
    model.remark = request.POST.get('remark', '')
    model.order = new_server_id if server_id == 0 else server_id
    model.json_data = request.POST.get('json_data', '')
    model.alias = request.REQUEST.get('alias', '')
    # model.is_ios = int(request.POST.get('is_ios', '0'))   #ios标识
    create_time = request.POST.get('create_time', '')
    model.last_time = datetime.datetime.now()
    model.game_db_addr_port = request.POST.get('game_db_addr_port', '')
    model.game_db_name = request.POST.get('game_db_name', '')
    model.game_db_user = request.POST.get('game_db_user', '')
    model.game_db_password = request.POST.get('game_db_password', '')
    if create_time == '':
        create_time = datetime.datetime.now()
    else:
        create_time = datetime.datetime.strptime(
            create_time, '%Y-%m-%d %H:%M:%S')
    model.create_time = create_time

    # 保存详细操作日志
    save_server_log(server_id, is_add, request, source_model, model)

    if not exists:
        if model.name != '' and model.game_addr != '':
            try:
                # 修改ID
                old_server = copy.copy(model)
                if update_id:
                    model.id = new_server_id
                model.save()

                group_ids = request.POST.getlist('group_id')
                group_ids = [int(x) for x in group_ids]

                for group_model in list_group:
                    if group_model.id in group_ids:
                        group_model.server.add(model)
                        try:
                            # 添加服务器分区后,在增加到角色资源里面
                            from models.admin import Role, Resource
                            role_exclude = Role.objects.exclude(
                                name__contains="系统管理员")
                            for r in role_exclude:
                                role_group_list = r.get_resource(
                                    'server_group')
                                if group_model in role_group_list:
                                    ser_l = list(
                                        group_model.server.values_list('id'))
                                    extend_l = r.get_resource(
                                        'server').values_list('id')
                                    ser_l.extend(extend_l)
                                    ser_l = list(set([i[0] for i in ser_l]))
                                    r.create_resource('server', ser_l)
                                    r.save()
                        except:

                            print trace_msg()

                    else:
                        group_model.server.remove(model)

                # 前面保存没有出错
                if update_id:
                    old_server.status = Server.Status.TEST
                    old_server.save()

            except Exception, e:

                err_msg = trace_msg()

        else:
            err_msg = '填写必要数据!'
    return render_to_response('feedback.html', locals())


@Route()
def server_remove(request, server_id=0):
    '''服务器删除
    '''
    err_msg = ''
    server_ids = request.REQUEST.getlist('sid')

    try:
        for model in Server.objects.filter(id__in=server_ids):
            # model.channel.clear()
            model.delete()
    except Exception, e:
        err_msg = trace_msg()
    return render_to_response('feedback.html', locals())


def all_json():
    """构建all.json的内容"""

    # 查出所有渠道
    channels = Channel.objects.all()

    # 遍历渠道查询集，并查出对应分区下的服务器
    content = "{"
    for channel in channels:
        servers = channel.group_set.first().server.all()

        # 遍历服务器查询集，并组成数据
        servers_list = list()
        for server in servers:
            server_json = u'{"serverName": "%s", "serverId": %s, "ip": "%s", "port": %s, "openTime": %s, "state": %s}' % (
                server.name, server.id, server.game_addr, server.game_port,
                int(round(time.mktime(time.strptime(str(server.create_time), "%Y-%m-%d %H:%M:%S")) * 1000)),
                server.status)  # 毫秒级时间戳
            servers_list.append(server_json)

        # 拼接字符串
        lis = "[%s]" % ", ".join(servers_list)
        content += '"%s"' % channel.channel_key + ": " + lis + ", "
    content = content.rstrip(", ") + "}"

    # 返回all.json内容
    return content


@Route()
def server_make(request):
    list_group = Group.objects.using('read').all()
    # folderPath = os.path.abspath(os.path.join(STATIC_ROOT, 'server'))
    folderPath = os.path.abspath(os.path.join(STATIC_PATH, 'server'))
    _folderPath = os.path.abspath(os.path.join(STATIC_ROOT, 'client', 'static', 'server'))
    if not os.path.exists(folderPath):
        os.mkdir(folderPath)
    #     # clear old file
    # for file_item in os.listdir(folderPath):
    #     try:
    #         itemsrc = os.path.join(folderPath, file_item)
    #         if os.path.isfile(itemsrc):
    #             os.remove(itemsrc)
    #     except:
    #         pass

    list_server = Server.get_server_list()

    serverList = []
    for item in list_server:
        mongo_port = 27017
        db_address = ''
        if item.log_db_config != '':
            try:
                db_config = json.loads(item.log_db_config)
            except:
                continue
            mongo_port = int(db_config.get('mongo_port', '') or 27017)
            db_address = db_config.get('db_addr', item.game_addr)

        if None != item.report_url and '' != item.report_url:
            item.report_url = item.report_url.replace('http://', '')
            item.report_url = item.report_url.replace('/', '')

        name = item.name
        game_addr = item.game_addr
        game_addr = game_addr.replace('"', '\\"')
        name = name.replace('"', '\\"')
        # item_json = u'{"id":%d,"name":"%s","alias":"%s","address":"%s","db_address": "%s","gate_port":%d,"db_port":%d,"status":%d,"battle_report_url":"%s"}' % (
        #     item.id, name, item.alias, game_addr, db_address, item.game_port, mongo_port, item.status, item.report_url)
        item_json = u'{"id":%d,"name":"%s","alias":"%s","address":"%s","db_address": "%s","gate_port":%d,"db_port":%d,"status":%d}' % (
            item.id, name, item.alias, game_addr, db_address, item.game_port, mongo_port, item.status)
        try:
            json.loads(item_json)
        except Exception, ex:
            print ex, item_json
            return render_to_response('feedback.html', {"err_msg": "服务器ID：%s配置错误" % name})
        serverList.append(item_json)

    # 跨服战的服务器加到GM.json 中.....
    gm_json_server_list = []
    gm_json_server_list.extend(serverList)

    try:
        Log._meta.db_table = 'log_battle_server_list'
        log_list = Log.objects.all()
        for item in log_list:
            name = db_address = report_url = ''
            s_status = mongo_port = 0
            # item_json = u'{"id":%d,"name":"%s","address":"%s","db_address": "%s","gate_port":%d,"db_port":%d,"status":%d,"battle_report_url":"%s"}' % (
            #     item.log_type, name, item.f1, db_address, item.log_data, mongo_port, s_status, report_url)
            item_json = u'{"id":%d,"name":"%s","address":"%s","db_address": "%s","gate_port":%d,"db_port":%d,"status":%d}' % (
                item.log_type, name, item.f1, db_address, item.log_data, mongo_port, s_status)
            try:
                json.loads(item_json)
            except Exception, ex:
                print ex
                continue

            gm_json_server_list.append(item_json)
    except Exception, ex:
        print 'log_battle_server_list GM.json error:', ex

    # # 生成GM LIST
    # filePath = os.path.join(folderPath, 'GM.json')
    # fileContent = '[%s]' % ','.join(gm_json_server_list)
    # file_handler = open(filePath, "w")
    # file_handler.write(fileContent.encode('utf-8'))
    # file_handler.close()

    # 服务器分组
    for item_group in list_group:
        noticeContent = ''
        server_groups = Group.objects.using('read').all()
        sg = []
        sg_d = ''
        for sgitem in server_groups:
            # if sgitem.partion_id != item_group.id:
            #     continue
            sl = []
            list_server = sgitem.server.filter(
                Q(status__gt=0, grouplist__id=sgitem.id)).order_by('-id')
            for item in list_server:
                if item.json_data == None:
                    item.json_data = ''
                remark = item.remark
                create_time = item.create_time.strftime("%Y-%m-%d %H:%M:%S")
                create_time_ts = int(time.mktime(
                    time.strptime(create_time, '%Y-%m-%d %H:%M:%S')))

                if item.client_ver:
                    client_ver = item.client_ver
                    client_ver = str(client_ver).replace(' ', '').split(',')
                else:
                    client_ver = []
                master_id = int(item.get_json_data()["master_server_id"]) if item.get_json_data().has_key(
                    "master_server_id") else 0
                # server_item = u'{"id":%d,"name":"%s","alias":"%s","address":"%s", "port":%d,"state":%d,"create_time":%d,"remark":"%s","brUrl":"%s","rqVer":%d,"commend":%d,"limitVer":%s,"other":{%s},"order":%d}' % (
                #     item.id, item.name, item.alias, item.game_addr,  item.game_port, item.status, create_time_ts, remark, item.report_url, int(item.require_ver), item.commend, client_ver, item.json_data, item.order)
                server_item = u'{"id":%d,"name":"%s","ip":"%s","port":%d,"status":%d,"commend":%d,"tabId":%d,"master_id":%d}' % (
                    item.id, item.name, item.game_addr, item.game_port, item.status, item.commend,
                    item.tabId if item.tabId else 0, master_id)
                # "desc":"%s",item.alias,
                try:
                    json.loads(server_item)
                except Exception, ex:
                    print ex
                    return render_to_response('feedback.html', err_msg="服务器ID：%s配置错误" % name)
                sl.append(server_item.replace("'", '"'))
            # sl.sort(key=lambda i:float(i.id),reverse=True)
            login = u'{}'
            if item_group.login_url:
                login_url = re.split(":", item_group.login_url)
                login = u'{"ip":"%s","port":%d}' % (login_url[0], int(login_url[1]))
            version = item_group.version if item_group.version else 0
            audit_version = item_group.audit_version if item_group.audit_version else 0
            audit_server = item_group.audit_server if item_group.audit_server else 0
            audit_versions = str(item_group.audit_versions) if item_group.audit_versions else ""
            audit_servers = str(item_group.audit_servers) if item_group.audit_servers else ""
            resource_version = item_group.resource_version if item_group.resource_version else 0
            other = item_group.other if item_group.other else "{}"
            sg_d = u'{"other":%s,"version":%d,"resource_version":%d,"audit_versions":"%s","audit_servers":"%s","cdn":"%s","tabName":"%s","login":%s,"card":"%s","custom":"%s","logic":[%s]}' % (
                other, version, resource_version, audit_versions, audit_servers, item_group.cdn_url, item_group.name,
                login, item_group.card_url, item_group.custom_url, ','.join(sl))
            # sg.append(sg_d)
            # "audit_version":%d,audit_version,
            # "audit_server":%d,audit_server,
            # "sdk":"%s",item_group.sdk_url,
        # 当前分区公告
        notices = Notice.objects.using('read').filter(
            id=item_group.notice_select)
        if len(notices) > 0:
            the_notice = notices[0]
            size_str = '0.7,0.8'
            if None != the_notice.size and '' != the_notice.size:
                size_str = the_notice.size
            noticeContent = u",\"notice\":{\"beginDate\":\"%s\",\"endDate\":\"%s\",\"title\":\"%s\",\"size\":[%s],\"positioin\":[-1,-1],\"url\":\"%s\"}" % (
                the_notice.begin_time,
                the_notice.end_time,
                the_notice.title,
                size_str,
                the_notice.link_url)

        other = ''

        if item_group.other != '' and item_group.other != None:
            item_group.other = item_group.other.strip()
            if item_group.other[0] != '{':
                item_group.other = '{%s' % item_group.other
            if item_group.other[-1] != '}':
                item_group.other = '%s}' % item_group.other
            other = u",\"other\":%s" % item_group.other
        # fileContent = u'{"sg":[%s],"remark":"%s","payUrl":"%s","customUrl":"%s","noticeUrl":"%s","upgradeUrl":"%s"%s%s}' % (','.join(
        #     sg), item_group.remark, item_group.pay_url, item_group.custom_url, item_group.notice_url, item_group.upgrade_url, noticeContent, other)
        fileContent = u'{"sg":%s}' % (sg_d if sg_d else {})

        filePath = os.path.join(folderPath, '%s.json' % item_group.group_key)

        # file_handler = open(filePath, "w")
        # file_handler.write(fileContent.encode('utf-8'))
        # file_handler.close()
    #    except Exception, e:
    #        print('write server list has error:%s' % e)
    channels = Channel.objects.all()

    for channel in channels:
        MD5path = os.path.join(STATIC_ROOT, 'md5', '%s.json' % channel.channel_key)
        _MD5path = os.path.join(STATIC_ROOT, 'client', 'static', 'md5', '%s.json' % channel.channel_key)
        filePath = os.path.join(folderPath, '%s.json' % channel.channel_key)
        _filePath = os.path.join(_folderPath, '%s.json' % channel.channel_key)
        print "channel_key:", channel.channel_key
        try:
            # agent_name = Channel.objects.get(channel_key=channel.channel_key).agent_name
            # agent = Agent.objects.get(alias=agent_name)
            # server_group = agent.server_group.all()
            group_name = Channel.objects.get(channel_key=channel.channel_key).group_name
            group = Group.objects.get(name=group_name)
            server_group = group.channel.all()
            fpContent = {}
            count = 1
            last_sg = None
            # "audit_version","audit_server","sdk",
            repeat_keys = ["version", "resource_version", "audit_versions", "audit_servers", "cdn", "login", "card",
                           "custom", "other"]
            for servers in server_group:
                groupPath = os.path.join(folderPath, '%s.json' % servers.group_key)
                if os.path.isfile(groupPath):
                    with open(groupPath, 'rb') as fp:
                        sContent = fp.read()
                        if sContent:
                            sContent = json.loads(sContent)
                            # 校验，去重
                            ssg = sContent["sg"]
                            now_sg = {}
                            for i in repeat_keys:
                                if ssg.has_key(i):
                                    now_sg[i] = ssg[i]
                                    del ssg[i]
                            if not last_sg:
                                last_sg = now_sg
                            print 'ddddddddd', last_sg, now_sg
                            if now_sg != last_sg:
                                return render_to_response('feedback.html', {"err_msg": "分区存在不同配置，请检查并保持一致！"})
                            fpContent[count] = ssg
                            count += 1

            all_logic = []
            _keys = []
            for key in fpContent:
                # get all logic
                _logic = fpContent[key]["logic"]
                all_logic.extend(_logic)
                _keys.append(key)

            for key in _keys:
                del fpContent[key]

            _server_group = {}
            tabName_map = DictDefine.get_dict_for_key('tabName')
            for server in all_logic:
                if server.has_key("tabId") and server["tabId"]:
                    _tabId = server["tabId"]
                    _server_group[_tabId] = _server_group[_tabId] if _server_group.has_key(_tabId) else defaultdict(
                        list)
                    del server["tabId"]
                    tabName = tabName_map[str(_tabId)] if tabName_map and tabName_map.has_key(str(_tabId)) else ""
                    _server_group[_tabId]["tabName"] = tabName
                    _server_group[_tabId]["logic"].append(server)

            count = 1
            __server_group = {}
            s_g_logic = sorted(_server_group.iteritems(), key=lambda i: i, reverse=True)
            for t in s_g_logic:
                __server_group[str(count)] = t[1]
                count += 1

            fpContent.update(__server_group)

            # with open(filePath, 'wb') as Cp:
            #     if last_sg:
            #         fpContent.update(last_sg)
            #     Cp.write(json.dumps(fpContent))

            check_dir(_filePath)

            with open(_filePath, 'wb') as _cp:
                _cp.write(json.dumps(fpContent))
        except Exception, e:
            print('write server list has error:%s' % e)

        check_dir(MD5path)

        content = {}
        fileMd5 = ""
        if os.path.isfile(filePath):
            fileMd5 = GetFileMd5(filePath)
        if os.path.isfile(MD5path):
            with open(MD5path, 'rb') as mp:
                content = mp.read()
                content = json.loads(content) if content else {}
                content["server"] = fileMd5

        with open(MD5path, 'wb') as np:
            np.write(json.dumps(content) if content else '')
            check_dir(_MD5path)
            with open(_MD5path, "wb") as _np:
                _np.write(json.dumps(content) if content else '')
            msg = " [channel key:%s] " % (channel.channel_key)
            msg += json.dumps(content) if content else ''
            try:
                LogInfo("MD5", msg)
            except BaseException as e:
                print 'LogInfo Error %s' % e

    # 生成all.json，即全部的渠道信息
    content = all_json()
    path = os.path.abspath(os.path.join(folderPath, 'all.json'))
    with open(path, 'w') as f:
        f.write(content.encode('utf-8'))

    # 走服务端协议，告知服务端文件名，让服务端来取配置
    gmp = GMProtocol(constant.gateway_id)
    result = gmp.tell_all_json()
    if result != [0]:
        return HttpResponse(u'向游戏服务端发送请求失败！')

    return render_to_response('feedback.html')


def check_dir(path):
    check_dir = os.path.dirname(path)
    isExists = os.path.exists(check_dir)
    if not isExists:
        os.makedirs(check_dir)


@Route()
def server_status_edit(request):
    _r = {"code": 1}
    action = request.REQUEST.get('action', '')
    server_list = request.POST.getlist('sid')
    last_time = datetime.datetime.now()
    if not server_list:
        return HttpResponse('没有选择服务器!')
    try:
        datas = Server.objects.filter(id__in=server_list)

        if action == 'change_status':  # 修改服务器状态
            status = int(request.POST.get('serv_status', '') or 0)

            datas.using('write').update(status=status, last_time=last_time)
            if status == 1:
                post_tip = request.POST.get('weihuTip', '')
                datas.using('write').update(remark=post_tip, last_time=last_time)

        elif action == 'change_version':  # 修改服务器版本
            ver = request.POST.get('ver', '')
            datas.using('write').update(client_ver=ver, last_time=last_time)
        elif action == 'clear_server':  # 清档
            not_maintenance = False
            limit_player = False
            for s in datas:
                if s.status not in [Server.Status.MAINTENANCE, Server.Status.DELETED]:
                    not_maintenance = True
                    break
                sql = 'select count(id) from player_%s' % (s.id)
                conn = Server.get_conn(s.id)
                cursor = conn.cursor()
                cursor.execute(sql)
                result = cursor.fetchone()
                if int(result[0]) >= 100:
                    limit_player = True
                    break

            if not_maintenance:
                return HttpResponse(json.dumps({"code": 1, "msg": "%s 不是维护状态！" % s.id}))

            if limit_player:
                return HttpResponse(json.dumps({"code": 1, "msg": "%s 角色数超100！" % s.id}))

            clear_server_url = 'http://oms.shyouai.com/Net_api?'
            postData = get_clear_server_params(server_list)
            if not postData:
                return HttpResponse(json.dumps({"code": 1, "msg": "服务器开服时间有问题！"}))
            clear_server_url += postData

            print clear_server_url
            result = requests.get(clear_server_url, timeout=150).json()
            print result
            _r["code"] = 0 if result["status"] == 0 else 1

            if not result:
                _r["msg"] = "运维无法返回结果！"
                return HttpResponse(json.dumps(_r))

            if _r["code"] == 1:
                _r["msg"] = "校验失败！"
                return HttpResponse(json.dumps(_r))

            _r["msg"] = []

            for s in result["result"]:
                if s['status'] == 1:
                    _r["msg"].append(s['server_id'])

            if _r["msg"]:
                _r["msg"] = json.dumps(_r["msg"]) + ' 清档失败'
            else:
                _r["msg"] = "全部清档成功"
            return HttpResponse(json.dumps(_r))

        _r["code"] = 0
        _r["msg"] = '修改成功!'
    except:
        _r["msg"] = trace_msg()

    return HttpResponse(json.dumps(_r))


@Route()
def merge_server_json(request):
    _r = {"code": 1}
    server_list = request.POST.getlist('sid')
    server_list.append(1000)
    last_time = datetime.datetime.now()
    default_module = {"1": []}
    if not server_list:
        return HttpResponse("没有选择服务器")
    try:
        for sid in server_list:
            server = Server.objects.filter(id=int(sid))
            if not server:
                return HttpResponse(json.dumps({"code": 1, "msg": '没有id为%s的服务器' % sid}))
            server = server[0]
            db_config = server.get_log_db_config()
            _s = {}
            if db_config:
                _s["dbPort"] = db_config["port"]
                _s["serverType"] = 1 if sid != 1000 else 0
                _s["dbIp"] = db_config["host"]
                _s["dbName"] = db_config["db"][:6] + "ic" + db_config["db"][6:]
                _s["dbPassword"] = db_config["password"]
                _s["dbUser"] = db_config["user"]
                _s["serverId"] = int(sid)
            default_module["1"].append(_s)

        rootPath = os.path.dirname(__file__)
        folderPath = os.path.abspath(os.path.join(rootPath, '../../../static/operations'))
        _folderPath = os.path.abspath(os.path.join(rootPath, '../../../static/client/static/operations'))
        if not os.path.exists(folderPath):
            os.mkdir(folderPath)

        if not os.path.exists(_folderPath):
            os.mkdir(_folderPath)

        filePath = os.path.join(folderPath, 'merge_server.json')
        _filePath = os.path.join(_folderPath, 'merge_server.json')
        with open(filePath, 'w') as f:
            f.write(json.dumps(default_module))

        with open(_filePath, 'w') as f:
            f.write(json.dumps(default_module))
        return HttpResponse(json.dumps({"code": 0, "msg": "保存成功！！"}))
    except BaseException as e:
        print 'merge_server_json Error'
        return HttpResponse("%s" % e)


# def server_merge_json(master_server, merge_servers):
#     """生成合服用的json文件"""
#
#     # 构造json内容
#     content = list()
#     for one in merge_servers:
#         merge_dict = dict()
#         merge_dict['serverId'] = one.id
#         merge_dict['type'] = 0
#         merge_dict[
#             'dbUrl'] = "jdbc:mysql://" + one.game_db_addr_port + "/" + one.game_db_name + "?autoReconnect=true&characterEncoding=utf8"
#         merge_dict['dbUser'] = one.game_db_user
#         merge_dict['dbPassword'] = one.game_db_password
#         content.append(merge_dict)
#     master_dict = dict()
#     master_dict['serverId'] = master_server.id
#     master_dict['type'] = 1
#     master_dict[
#         'dbUrl'] = "jdbc:mysql://" + master_server.game_db_addr_port + "/" + master_server.game_db_name + "?autoReconnect=true&characterEncoding=utf8"
#     master_dict['dbUser'] = master_server.game_db_user
#     master_dict['dbPassword'] = master_server.game_db_password
#     content.append(master_dict)
#     content = json.dumps(content)
#
#     # 写入json文件
#     path = os.path.join(os.path.join(STATIC_PATH, 'server'), 'merge.json')
#     with open(path, 'w') as f:
#         f.write(content)


@Route()
def server_merge(request, auto_merge=False):
    if request.method == 'POST':
        if auto_merge:
            # import pdb;pdb.set_trace()
            master_server_id = request.POST.get("master_server_id", '')
            merge_server_ids = request.POST.get("server_id")
            close_time = ""
        else:
            master_server_id = request.REQUEST.get('master_server_id', '')
            merge_server_ids = request.REQUEST.getlist('server_id')
            close_time = request.REQUEST.get('close_time', '')
        err_msg = ''
        if not master_server_id:
            err_msg = '母服错误'
        if not merge_server_ids:
            err_msg = '没有勾选子服!'
        try:
            if not err_msg:
                master_server = Server.objects.get(id=master_server_id)
                master_server_db_config = master_server.get_log_db_config()
                master_server_confog = master_server.get_json_data()
                porxyport = master_server_confog.get(
                    'porxyport', '')  # 腾讯的代理端口
                host = master_server_db_config.get('host', '')
                port = master_server_db_config.get('port', 3306)
                user = master_server_db_config.get('user', '')
                password = master_server_db_config.get('password', '')
                mongo_port = master_server_db_config.get('mongo_port', 27017)
                gm_port = master_server_db_config.get('gm_port', '')
                db_name = master_server_db_config.get('db', '')

                report_url = master_server.report_url
                game_addr = master_server.game_addr
                game_port = master_server.game_port
                game_db_addr_port = master_server.game_db_addr_port
                game_db_name = master_server.game_db_name
                game_db_user = master_server.game_db_user
                game_db_password = master_server.game_db_password

                merge_servers = Server.objects.filter(id__in=merge_server_ids)

                # # 生成json文件
                # server_merge_json(master_server, merge_servers)

                mastrer_str = '母服 [%s]' % master_server.name
                err_msg = mastrer_str + '\n'
                for child_server in merge_servers:
                    if child_server.id == master_server.id:
                        continue
                    try:
                        source_model = copy.copy(child_server)
                        child_server.report_url = report_url
                        child_server.game_addr = game_addr
                        child_server.game_port = game_port
                        child_server.game_db_addr_port = game_db_addr_port
                        child_server.game_db_name = game_db_name
                        child_server.game_db_user = game_db_user
                        child_server.game_db_password = game_db_password
                        child_server_db_config = child_server.get_log_db_config()

                        child_server_db_config['gm_port'] = gm_port
                        child_server_db_config['host'] = host
                        child_server_db_config['port'] = port
                        child_server_db_config['user'] = user
                        child_server_db_config['password'] = password
                        child_server_db_config['mongo_port'] = mongo_port
                        child_server_db_config['close_time'] = close_time
                        child_server_db_config['db'] = db_name
                        child_server.set_log_db_config(child_server_db_config)

                        child_server_config = child_server.get_json_data()
                        child_server_config[
                            'master_server_id'] = master_server.id
                        if porxyport:  # 腾讯需要的设置
                            child_server_config['porxyport'] = int(porxyport)
                        child_server.set_json_data(child_server_config)

                        if '母服 ' in child_server.remark:
                            child_server.remark = re.sub(
                                '母服 \[.*\]', mastrer_str, child_server.remark)
                        else:
                            child_server.remark += mastrer_str

                        save_server_log(child_server.id, False,
                                        request, source_model, child_server)
                        child_server.save()
                        err_msg += '%s 保存成功!\n' % child_server.name
                    except:
                        err_msg += '%s 保存失败 %s!\n' % (
                            child_server.name, trace_msg())
        except:
            err_msg = trace_msg()

        if auto_merge:

            if "成功" in err_msg:
                return {"result": "success", "msg": err_msg}
            return {"result": "fail", "msg": err_msg}

        return render_to_response('feedback.html', err_msg.replace('\n', '<br>'))
    # group_servers_dict = get_group_servers_dict(request)
    group_servers_dict = groups_servers(request)
    list_server = Server.objects.all()
    return render_to_response('server/server_merge.html', locals())


@Route()
def auto_server_merge(request):
    server_list = request.POST.getlist('sid')
    server_list = [int(s) for s in server_list]
    base_query = Q(id__in=server_list)
    master_server_id = Server.objects.filter(base_query & Q(status=2))[0].id
    request.POST['master_server_id'] = master_server_id
    merge_server_ids = Server.objects.filter(base_query & Q(status=1))
    merge_server_ids = [s.id for s in merge_server_ids]
    request.POST["server_id"] = merge_server_ids
    write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), "开始合服", -1)

    write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), "开始踢人", -1)
    # 先踢所有子服玩家
    for s in merge_server_ids:
        gmp = GMProtocol(s)
        result = gmp.server_offline()
        if result != 0:
            return HttpResponse(json.dumps({"code": 0, "msg": "%s 服 踢人失败!!" % (s)}))
    write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), "踢人成功", -1)

    gmp = GMProtocol(master_server_id)
    result = gmp.auto_merge_server(merge_server_ids)
    print result
    msg = {"code": 1}
    if result == 0:
        write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), "杀子服进程", -1)
        # 子服杀自己
        for sid in merge_server_ids:
            gmp = GMProtocol(sid)
            _result = gmp.stop_server()
        write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), "杀子服进程完成", -1)
        result = server_merge(request, auto_merge=True)
        print result
        if result["result"] == "success":
            msg["msg"] = "合服成功！！！"
            write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), msg["msg"], 1)
            return HttpResponse(json.dumps(msg))
    msg["msg"] = "合服失败:%s" % (result["msg"] if type(result) == dict else "服务端返回失败！")
    write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), msg["msg"], 0)
    return HttpResponse(json.dumps(msg))


@Route()
def back_merge_server(request):
    server_list = request.POST.getlist('sid')
    server_list = [int(s) for s in server_list]
    base_query = Q(id__in=server_list)
    master_server_id = Server.objects.filter(base_query & Q(status=2))[0].id
    request.POST['master_server_id'] = master_server_id
    merge_server_ids = Server.objects.filter(base_query & Q(status=1))
    merge_server_ids = [s.id for s in merge_server_ids]
    request.POST["server_id"] = merge_server_ids
    write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), "开始回滚", -1)

    gmp = GMProtocol(master_server_id)
    result = gmp.back_merge_server(merge_server_ids)
    print result
    msg = {"code": 1}
    if result == 0:
        msg["msg"] = "回滚合服成功!!!"
        write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), msg["msg"], 2)
        return HttpResponse(json.dumps(msg))
    msg["msg"] = "回滚合服失败:%s" % (result["msg"] if type(result) == dict else "服务端返回失败！")
    write_hefu_log(request.admin.id, master_server_id, json.dumps(merge_server_ids), msg["msg"], 3)
    return HttpResponse(json.dumps(msg))


def Counter(obj):
    result = {}
    for s in obj:
        if result.has_key(s):
            result[s] += 1
        else:
            result[s] = 1
    return result


@Route()
def auto_server_merge_info(request):
    action = request.REQUEST.get('action', '')
    server_list = request.POST.getlist('sid')
    server_status = []
    status_dict = {}
    for s in server_list:
        model = Server.objects.get(id=int(s))
        if model.status not in (1, 2):
            return HttpResponse(json.dumps({"code": 1, "msg": "%s服 不是顺畅或维护状态" % (s)}))
        server_status.append(model.status)
        if status_dict.has_key(model.status):
            status_dict[model.status].append(s)
        else:
            status_dict[model.status] = [s]
    server_status = Counter(server_status)
    if server_status.has_key(2) and server_status[2] == 1 and server_status.has_key(1) and server_status[1] > 0:
        return HttpResponse(json.dumps({"code": 1, "msg": "母服:  %s \n子服:  %s \n请仔细核对服务器是否正确！" % (
            json.dumps(status_dict[2]), json.dumps(status_dict[1]))}))
    else:
        return HttpResponse(json.dumps({"code": 1, "msg": "存在多个母服:%s" % (json.dumps(status_dict[2]))}))


def save_server_log(server_id, is_add, request, source, target):
    the_user_id = request.admin.id
    ip = OperateLogManager.get_request_ipAddress(request)
    request_path = '/server/save/%s' % server_id
    if not is_add:
        save_modify_server_log(source, target, the_user_id, ip, request_path)
    else:
        OperateLogManager.save_operate_log(
            the_user_id, '新建服务器', request_path, ip)


def save_modify_server_log(source, target, the_user_id, ip, request_path):
    msg = []
    if source.client_ver != target.client_ver:
        msg.append(u'客户端版本')
    if source.name != target.name:
        msg.append(u'名称')
    if source.status != target.status:
        msg.append(u'状态')
    if source.commend != target.commend:
        msg.append(u'推荐')
    if source.require_ver != target.require_ver:
        msg.append(u'最低版本')
    if source.game_addr != target.game_addr:
        msg.append(u'ip')
    if source.game_port != target.game_port:
        msg.append(u'port')
    if source.report_url != target.report_url:
        msg.append(u'url')
    if source.log_db_config != target.log_db_config:
        msg.append(u'db_config')
    if source.remark != target.remark:
        msg.append(u'备注')
    if source.order != target.order:
        msg.append(u'排序')
    if source.json_data != target.json_data:
        msg.append(u'json_data')
    if source.create_time != target.create_time:
        msg.append(u'开服时间')

    if msg.__len__() == 0:
        str_msg = '无修改'
    else:
        str_msg = ','.join(msg)

    OperateLogManager.save_operate_log(the_user_id, str_msg, request_path, ip)


@Route()
def server_offline(request):
    result_msg = '操作'
    if request.method == 'POST':
        ids = request.REQUEST.get('ids', '')
        if not ids:
            return HttpResponse("没有选择服务器")
        ids = json.loads(ids)
        for sid in ids:
            gmp = GMProtocol(sid)
            result = gmp.server_offline()
            if result == 0:
                result_msg += '成功'
            else:
                result_msg += '失败'

    return HttpResponse(result_msg)


@Route()
def server_charge_reset(request):
    result_msg = ''
    if request.method == 'POST':
        ids = request.REQUEST.get('ids', '')
        if not ids:
            return HttpResponse("没有选择服务器")
        ids = json.loads(ids)
        for sid in ids:
            gmp = GMProtocol(sid)
            result = gmp.server_charge_reset()
            if result == 0:
                result_msg = '操作成功'
            else:
                result_msg = '操作失败'

    return HttpResponse(result_msg)


def get_clear_server_params(server_id):
    if not server_id:
        return
    opendates = []
    for s in server_id:
        model = Server.objects.get(id=s)
        opendate = time.mktime(model.create_time.timetuple())
        if opendate:
            opendates.append(opendate)
        else:
            return

    mantinance_key = "X9odXPVhn8xM6qHkO1IIzSW7qGyIld"
    cryt = "111.231.114.233" + mantinance_key + json.dumps([int(s) for s in server_id])
    params = {}
    params["action"] = "clean_game"
    params["type"] = 1
    params["id_list"] = [int(s) for s in server_id]
    params["opendate"] = [int(o) for o in opendates]
    params["version"] = 2
    params["key"] = make_password(cryt, None, 'pbkdf2_sha256')
    print params
    return urllib.urlencode(params)


@Route()
@notauth
def maintenance_new_server(request):
    is_add = True
    source_model = None
    params = request.REQUEST
    server_id = params.get("server_id", 0)
    if not server_id:
        return {"code": 1, "msg": "没有参数"}

    model = Server.objects.filter(id=int(server_id))
    if model:
        return HttpResponse(json.dumps({"code": 1, "msg": "已存在该服务器ID"}))

    try:
        model = Server()
        model.id = server_id
        model.name = params.get("name", "")
        model.tabId = params.get("tabId", 1)
        model.status = -1
        model.commend = params.get("commend", 0)
        model.game_addr = params.get("game_addr", "")
        model.game_port = params.get("game_port", "")
        model.log_db_config = params.get("log_db_config", "")
        model.order = params.get("server_id")
        model.alias = params.get("alias", "")
        model.create_time = datetime.datetime.strptime(
            params.get("create_time"), '%Y-%m-%d %H:%M:%S')
        model.last_time = datetime.datetime.now()
        model.save(using="write")
        # 保存详细操作日志
        save_server_log(server_id, is_add, request, source_model, model)
        return HttpResponse(json.dumps({"code": 0, "msg": "success"}))
    except BaseException as e:
        return HttpResponse(json.dumps({"code": 1, "msg": "save fail！"}))


@Route()
@notauth
def server_mysql_ip(request):
    server_list = json.loads(request.REQUEST.get("server_list", []))
    print server_list
    try:
        if server_list:
            result = []
            for sid in server_list:
                model = None
                try:
                    model = Server.objects.get(id=int(sid))
                except:
                    pass
                if not model:
                    result.append("")
                    continue
                host = json.loads(model.log_db_config)["host"]
                result.append(host)
    except BaseException as e:
        print e
    if result:
        return HttpResponse(",".join(result))
    return HttpResponse("")


def write_hefu_log(log_user, master_id, sub_server, msg, log_result):
    try:
        Log._meta.db_table = 'log_merge_server'
        log = Log()
        log.log_user = log_user
        log.log_time = datetime.datetime.now()
        log.f1 = master_id
        log.f2 = sub_server
        log.f8 = msg
        log.log_result = log_result
        log.save(using='write')
    except BaseException as e:
        print "views --> server --> server --> write_merge_server_log error:%s" % e
