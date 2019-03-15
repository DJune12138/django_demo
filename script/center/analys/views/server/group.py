# -*- coding: utf-8 -*-
# 服务器分区相关
# =========================================
from django.core.urlresolvers import reverse
from django.db import connection, connections
from django.utils.html import conditional_escape
from django.http import HttpResponse
from django.db.models import Q
from django.template.context import RequestContext
from django.shortcuts import redirect, render_to_response, HttpResponseRedirect
from django.views.generic import ListView, View
# ==========================================
from django.utils.datastructures import SortedDict
from django.shortcuts import render_to_response

from models import Channel
from models.server import Server, Group, GroupList
from models.center import Notice
from util.constant import tab_name_id
from views.base import OperateLogManager
from views.game.base import GMProtocol
from views.widgets import get_group_servers_dict
from util import trace_msg, constant
import copy, json, os
from models.log import DictDefine, DictValue
from settings import STATIC_ROOT, STATIC_PATH
import datetime
from urls.AutoUrl import Route


@Route()
def group_pids_make(request):
    '''生成37pid列表
    '''
    folderPath = os.path.abspath(os.path.join(STATIC_ROOT, 'pid'))

    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
        # clear old file
    for file_item in os.listdir(folderPath):
        try:
            itemsrc = os.path.join(folderPath, file_item)
            if os.path.isfile(itemsrc):
                os.remove(itemsrc)
        except:
            pass

    group_key = {}

    try:
        group_obj = Group.objects.using('read').all()
        for group in group_obj:
            group_list_str = group.pid_list
            if group_list_str:
                pid_list = eval(group.pid_list)

                if isinstance(pid_list, list):
                    for pid in pid_list:
                        key = group.key
                        group_key[pid] = key

    except Exception, e:
        print e

    if group_key:
        fileContent = json.dumps(group_key)
        filePath = os.path.join(folderPath, 'pid.json')
        file_handler = open(filePath, "w")
        file_handler.write(fileContent.encode('utf-8'))
        file_handler.close()

    return render_to_response('feedback.html')


def group_list(request):
    list_record = Group.objects.all()
    list_notice = Notice.objects.filter(notice_type=3)
    notice_dict = dict([(n.id, n) for n in list_notice])
    for g in list_record:
        if g.notice_select:
            g.notice = notice_dict.get(g.notice_select, None)
    parg = {}
    parg["list_record"] = list_record
    parg["list_notice"] = list_notice
    ##服务器分组
    group_list = GroupList.objects.all()
    parg["group_list"] = group_list
    parg["group_servers"] = [sl.server.filter(Q(status__gt=0, grouplist__id=sl.id)) for sl in group_list]

    return render_to_response('server/group_list.html', parg)


##服务器分组
def grouplist_edit(request, model_id=0):
    parg = {}
    parg['group_servers_dict'] = SortedDict()
    model_id = int(model_id)
    other_servers = request.admin.get_resource('server').prefetch_related('group_set')

    if model_id == 0:
        model_id = int(request.GET.get('model_id', '0'))
    model = None

    if model_id > 0:
        model = GroupList.objects.using('read').get(id=model_id)
        group_id = model.partion.id
        parg["select_group_id"] = group_id
        groups = request.admin.get_resource('server_group').filter(id=group_id)

    if model == None:
        model = GroupList()
        model.id = 0
        groups = request.admin.get_resource('server_group').all()

    for s in other_servers:
        g_s_list = s.group_set.all()

        if g_s_list:
            for g in g_s_list:
                if g in groups:
                    parg['group_servers_dict'].setdefault(g, set())
                    parg['group_servers_dict'][g].add(s)

    parg["model"] = model
    parg["select_server_ids"] = [s.id for s in model.server.all()]

    return render_to_response('server/grouplist_edit.html', parg)


def grouplist_save(request, model_id=0):
    #    print "##",request.POST
    model_id = int(model_id)
    if model_id == 0:
        model_id = int(request.GET.get('model_id', '0'))

    model = None
    if model_id > 0:
        model = GroupList.objects.using('write').get(id=model_id)
    if model == None:
        model = GroupList()
        groupid = request.POST.get('group_id', '')
        if groupid:
            group = Group.objects.using('write').get(id=groupid)
            model.partion = group
        else:
            return HttpResponse("没有选择分区.")

    model.key = request.POST.get('key', '')
    model.name = request.POST.get('name', '')
    model.order = request.POST.get('order', '')
    ajax_post = request.POST.get('ajax', False)

    try:
        is_updateServerList = False

        post_server_list = request.POST.getlist('server_id')
        post_server_list = set(post_server_list)
        source_server_list = []
        if model.id > 0:
            model.server.clear()
            if post_server_list.__len__() != model.server.count():
                source_server_list = model.server.all().values('id')
                is_updateServerList = True

        model.save(using='write')
        model.server.add(*Server.objects.using('write').filter(id__in=post_server_list))

        if ajax_post:
            return HttpResponse("保存成功！")

    except Exception, e:
        err_msg = trace_msg()
        if ajax_post:
            return HttpResponse("保存出错，请重试")
        print('group save error:', e)

    return render_to_response('feedback.html', locals())


def grouplist_remove(request, model_id=0):
    model_id = int(model_id)

    if model_id > 0:
        try:
            model = GroupList.objects.using('write').get(id=model_id)
            model.server.clear()
            model.delete(using='write')
        except Exception, e:
            print('group remove error:', e)
    return render_to_response('feedback.html')


##分区
def group_edit(request, model_id=0):
    model_id = int(model_id)
    if model_id == 0:
        model_id = int(request.GET.get('model_id', '0'))

    model = None

    if model_id > 0:
        model = Group.objects.using('read').get(id=model_id)
    if model == None:
        model = Group()
        model.id = 0
        model.other = ''

    list_notice = Notice.objects.using('read').filter(notice_type=3)

    parg = {}
    parg["models"] = model
    parg["group_servers_dict"] = get_group_servers_dict(request)
    parg["select_server_ids"] = [s.id for s in model.server.all()]
    parg["list_notice"] = list_notice

    ######PID列表#####
    pid_list = parg["models"].pid_list
    try:
        if pid_list and pid_list != 'None':
            pid_list = eval(pid_list)
            parg["model"].pid_list = ','.join(pid_list)
            r = {}
            o = DictDefine.objects.filter(key='gid_pid')
            _r = o[0].get_dict()
            if pid_list:
                for i in pid_list:
                    if i in _r:
                        r[i] = _r[i]
            parg["pids_dict"] = r
    except Exception, e:
        print e
    ###########
    parg['model_id'] = model_id  # 用于模板筛选当前分区
    parg['request'] = request  # 用于权限

    # 获取当前分区的渠道
    if model_id:
        channel = Group.objects.get(id=model_id).channel.all()
        parg['channel'] = channel

    # # 获取所有服务器，并根据id排序分组
    # list_record = request.admin.get_resource('server').all().order_by("id", "-status", "order")
    # servers_list = []
    # for i in list_record:
    #     servers_list.append(i)
    # integer = len(servers_list) // 30  # 取整
    # remainder = len(servers_list) % 30  # 取余
    # if remainder > 0:  # 余数大于0的话组数+1，否则组数等于整数
    #     group_num = integer + 1
    # else:
    #     group_num = integer
    # groups_list = list()
    # j = 0
    # for i in range(1, group_num + 1):  # 数据格式：[["分组1", [Server, Server, ...]], ["分组2", [Server, Server, ...]], ...]
    #     original_j = j
    #     servers_groups_list = list()
    #     while j < len(servers_list) and j < original_j + 30:
    #         servers_groups_list.append(servers_list[j])
    #         j += 1
    #     one_group = list()
    #     one_group.append("分组%s" % i)
    #     one_group.append(servers_groups_list)
    #     groups_list.append(one_group)
    # parg['list_record'] = groups_list

    # 根据服务器的分组进行服务器分组排列
    m = eval(DictValue.objects.using('read').get(dict_id=tab_name_id).json_dict)
    server_group = dict()
    for num, name in m.items():
        servers_list = request.admin.get_resource('server').filter(tabId=int(num))
        servers = list()
        for server in servers_list:
            servers.append(server)
        server_group[name] = servers
    parg['list_record'] = server_group

    return render_to_response('server/group_edit.html', parg)


def url_json_content():
    """url.json的文件内容"""

    # 查出所有渠道
    channels = Channel.objects.all()

    # 遍历渠道查询集，查出对应分区，并组织数据
    channel_dict = dict()
    for channel in channels:
        url_dict = dict()
        group = channel.group_set.first()
        url_dict['card_url'] = group.card_url
        url_dict['gateway_notice_url'] = group.cdn_url
        url_dict['custom_url'] = group.custom_url
        if channel.novice_mail:
            mail_list = channel.novice_mail.split('\r\n')
        else:
            mail_list = group.novice_mail.split('\r\n')
        url_dict['mail'] = mail_list
        channel_dict[channel.channel_key] = url_dict

    # json化
    url_json = json.dumps(channel_dict)

    # 返回json数据
    return url_json


def group_save(request, model_id=0):
    # 是否只修改公告(用于批量修改)
    only_updateNotice = request.POST.get('notice', False)
    only_updateAction = request.POST.get('action', False)

    if only_updateAction in ["version", "resource_version"]:
        # 只修改版本号或资源版本号
        print  u"操作类型:", only_updateAction
        value = int(request.POST.get('value', 0))
        model_id = int(request.GET.get('model_id', '0'))
        if not value:
            return HttpResponse("无新值！")
        try:
            model = Group.objects.using('write').get(id=model_id)

            if only_updateAction == "version":
                model.version = value
            else:
                model.resource_version = value
            model.last_time = datetime.datetime.now()
            model.save()
            return HttpResponse("保存成功")
        except BaseException as e:
            print e
            return HttpResponse('未知错误')

    model_id = int(model_id)

    if model_id == 0:
        model_id = int(request.GET.get('model_id', '0'))

    model = None
    if model_id > 0:
        model = Group.objects.using('write').get(id=model_id)
    if model == None:
        model = Group()

    source_model = copy.copy(model)

    if not only_updateNotice:
        model.group_key = request.POST.get('group_key', '')
        model.name = request.POST.get('name', '')
        model.login_url = request.POST.get('login_url', '')
        model.card_url = request.POST.get('card_url', '')
        model.cdn_url = request.POST.get('cdn_url', '')
        # model.sdk_url = request.POST.get('sdk_url', '')
        model.custom_url = request.POST.get('custom_url', '')
        model.notice_url = request.POST.get('notice_url', '')
        model.notice_select = request.POST.get('notice_select', '0')
        model.remark = request.POST.get('remark', '').replace('\n', '\\n').replace('"', "“")
        model.other = request.POST.get('other', '').replace('\n', '')
        model.version = int(request.POST.get('version')) if request.POST.get('version') else None
        # model.audit_version = int(request.POST.get("audit_version")) if request.POST.get("audit_version") else None
        # model.audit_server = int(request.POST.get("audit_server")) if request.POST.get("audit_server") else None
        model.resource_version = int(request.POST.get("resource_version")) if request.POST.get(
            "resource_version") else None
        model.audit_versions = request.POST.get("audit_versions", "")
        model.audit_servers = request.POST.get("audit_servers", "")
        model.last_time = datetime.datetime.now()
        model.game_app_key = request.POST.get("game_app_key", "")
        model.novice_mail = request.POST.get("novice_mail", "")
    else:
        model.notice_select = request.POST.get('notice_select', '')
        model.last_time = datetime.datetime.now()
        model.save()
        return HttpResponse("保存成功！")

    ajax_post = request.POST.get('ajax', False)

    try:
        is_updateServerList = False

        post_pid_list = str(request.POST.get('pid_list', '')).split(',')
        post_pid_list = list(set(post_pid_list))
        model.pid_list = post_pid_list
        ####判断重复的PID#####

        if post_pid_list:
            group_obj_all = Group.objects.all()
            for group in group_obj_all:
                if int(model_id) == int(group.id):
                    continue
                group_list_str = group.pid_list
                if group_list_str:
                    group_pid_list = eval(group_list_str)
                    if isinstance(group_pid_list, list):
                        for pid in post_pid_list:
                            if pid in group_pid_list and pid:
                                return HttpResponse("存在重复的PID:%s" % pid)

        #####################

        post_server_list = request.POST.getlist('server_id')
        post_server_list = set(post_server_list)
        source_server_list = []
        if model.id > 0:
            model.server.clear()
            if post_server_list.__len__() != model.server.count():
                source_server_list = model.server.all().values('id')
                is_updateServerList = True
        model.save(using='write')
        model.server.add(*Server.objects.using('write').filter(id__in=post_server_list))

        save_group_modify_log(request, source_model, model, is_updateServerList, post_server_list, source_server_list)

        if ajax_post:
            return HttpResponse("保存成功！")

    except Exception, e:
        err_msg = trace_msg()
        if ajax_post:
            return HttpResponse("保存出错，请重试")
        print('group save error:', e)

    # 编写url.json
    content = url_json_content()
    path = os.path.abspath(os.path.join(os.path.abspath(os.path.join(STATIC_PATH, 'server')), 'url.json'))
    with open(path, 'w') as f:
        f.write(content)

    # 走服务端协议，告知服务端文件变更
    servers = Server.objects.all()
    for server in servers:
        gmp = GMProtocol(server.id)
        result = gmp.tell_url_json()

    return render_to_response('feedback.html', locals())


def save_group_modify_log(request, source, target, is_updateServerList, post_server_list, source_server_list):
    admin_id = request.admin.id
    msg = []

    msg_str = u"没有操作"

    if source.group_key != target.group_key:
        msg.append('group_key')
    if source.name != target.name:
        msg.append('name')
    if source.login_url != target.login_url:
        msg.append("login_url")
    if source.card_url != target.card_url:
        msg.append('card_url')
    if source.cdn_url != target.cdn_url:
        msg.append('cdn_url')
    if source.notice_url != target.notice_url:
        msg.append('notice_url')
    if int(source.notice_select) != int(target.notice_select):
        msg.append('notice_select')
    if source.remark != target.remark:
        msg.append('remark')

    if is_updateServerList:
        msg.append(u'server(')
        tmp_list = []
        for item in source_server_list:
            tmp_list.append(str(item['id']))
        msg.append(','.join(tmp_list))
        msg.append(':')
        msg.append(','.join(post_server_list))
        msg.append(')')

    if msg.__len__() != 0:
        msg_str = ','.join(msg)

    request_path = 'group/save/%s' % source.id

    OperateLogManager.save_operate_log(admin_id, msg_str, request_path,
                                       OperateLogManager.get_request_ipAddress(request))


def group_remove(request, model_id=0):
    model_id = int(model_id)

    if model_id > 0:
        try:
            model = Group.objects.using('write').get(id=model_id)
            model.server.clear()
            model.delete(using='write')
        except Exception, e:
            print('group remove error:', e)
    return render_to_response('feedback.html')


@Route()
def relate_gid(request, template='server/relate_gid.html'):
    '''37gid关联pid
    '''
    try:
        from models.log import DictDefine
        pid_m = DictDefine.objects.filter(key='pid')
        pid_j = pid_m[0].get_json_data()
        result = {'code': -1, 'msg': 'false'}

        m = DictDefine.objects.using('read').get(key='gid_pid')
        old_dict = json.loads(m.get_json_data())
        d = m.dict
        if bool(m) is False:
            return HttpResponse('没有新建关联字典.')

        type = request.POST.get('type', '')
        if type == 'up':
            new_json_dict = request.POST.get('msg', '')
            if new_json_dict:
                # 追加合并
                old_dict.update(json.loads(new_json_dict))
                m.json_dict = json.dumps(old_dict)
                m.save(using='write')
                result['code'] = 0
                result['msg'] = '成功'
                return HttpResponse(json.dumps(result))

        if type == 'del':
            del_val = request.POST.get('msg', '')
            del_key = old_dict.pop(del_val)
            m.json_dict = json.dumps(old_dict)
            m.save(using='write')
            result['code'] = 0
            result['msg'] = '%s:删除成功' % del_key
            return HttpResponse(json.dumps(result))
    except:
        print trace_msg()

    return render_to_response(template, locals())
