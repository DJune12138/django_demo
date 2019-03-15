# -*- coding: utf-8 -*-
# 游戏公告

from django.shortcuts import render_to_response
from views.base import get_server_list, notauth
from django.http import HttpResponseRedirect, HttpResponse
from django.template import Context, Template
from models.center import Server, Notice, Group
from models.channel import Channel
from models.admin import Admin
from django.db.models import Q
from views.base import GlobalPathCfg
from urls.AutoUrl import Route
from views.widgets import get_group_servers_dict, get_group_channels_dict
import os, time
import json
import traceback
import copy
import hashlib
from util import trace_msg
from settings import STATIC_ROOT
import time, datetime
from util import datetime_to_str, datetime_to_timestamp
from django.template import loader
from PIL import Image
from views.game.base import GMProtocol
from handlerHTML import HTMLChange
from views.widgets import get_group_servers_dict, get_agent_channels_dict
import urlparse
from models.log import DictDefine
from django.utils.datastructures import SortedDict as OrderedDict

NOTICE_PATH = os.path.join(STATIC_ROOT, 'notice')
_NOTICE_PATH = os.path.join(STATIC_ROOT, 'client', 'static', 'notice')
_globalpathcfg = GlobalPathCfg()


def notice_list(request, notice_type=0):
    '''公告编辑列表
    '''
    server_id = int(request.GET.get('server_id', 0))
    the_user = request.admin
    server_list = the_user.get_resource("server").all()
    channel_list = the_user.get_resource("channel").all()
    if len(server_list) == 0:
        server_list = get_server_list()

    # if server_list.__len__() == 0 or len(channel_list) == 0:
    #     return HttpResponse("没有服务器或渠道可管理")

    if server_id > 0:
        if notice_type > 0:
            list_record = Notice.objects.using('read').filter(server=server_id, notice_type=notice_type)
        else:
            list_record = Notice.objects.using('read').filter(server=server_id)
    else:
        if notice_type > 0:
            list_record = Notice.objects.using('read').filter(notice_type=notice_type)
        else:
            list_record = Notice.objects.using('read').exclude(notice_type=4)

    # if channel_list.__len__() > 0 and notice_type != 4:
    #     _list_record = Notice.objects.using('read').exclude(~Q(channel__in = channel_list))
    #     list_record = Notice.objects.using('read').filter(notice_type=2)
    #     list_record = list_record | _list_record

    list_record = list_record.prefetch_related('server').order_by('-id')
    # list_record = set(list_record)
    now = datetime.datetime.now()
    group_notice_ids = []

    template_path = 'server/notice_list.html'
    if notice_type == 4:
        template_path = 'server/push_list.html'
        admins_list = Admin.objects.values_list('id', 'alias').all()
        admin_dict = dict(admins_list)
        for n in list_record:
            n.create_user = admin_dict.get(n.pub_user, n.pub_user)
            n.server_count = int(len(n.server.all()))

    parg = {}
    parg["server_list"] = server_list
    parg["server_id"] = server_id
    parg["list_record"] = list_record
    parg["usm"] = the_user

    return render_to_response(template_path, parg)


def notice_edit(request, model_id=0, notice_type=0, info_msg=''):
    '''公告编辑
    '''
    model_id = int(model_id)

    if model_id == 0:
        model_id = int(request.GET.get('notice_id', '0'))

    model = None
    if model_id > 0:
        model = Notice.objects.using('write').get(id=model_id)
        notice_type = model.notice_type
    if model == None:
        model = Notice()
        model.id = 0
        notice_type = notice_type or int(request.POST.get('type', request.GET.get('type', '0')))
        model.notice_type = notice_type

    list_group = Group.objects.using('write').all()
    if notice_type == Notice.Notine_Type.group:
        if model.id > 0:
            list_group_selected = model.group.all()
            group_selected = {}
            for item in list_group_selected:
                group_selected[item.id] = 1
            for item in list_group:
                item.is_show = group_selected.get(item.id, 0)

    if model.size == None:
        model.size = ''

    template_path = 'server/notice_edit.html'
    if notice_type == 4:
        jump_function = DictDefine.get_dict_for_key("jump_function")
        photo_list = DictDefine.get_dict_for_key("photo_list")
        photo_list = OrderedDict(sorted(photo_list.items(), key=lambda t: t[0]))
        model.photo_id = str(model.photo_id)
        template_path = 'server/push_edit.html'

    group_servers_dict = get_group_servers_dict(request)
    select_server_ids = [s.id for s in model.server.all()]
    # agent_channels_dict = get_agent_channels_dict(request)
    group_channels_dict = get_group_channels_dict()
    select_channel_ids = [c.id for c in model.channel.all()]

    return render_to_response(template_path, locals())


def notice_save(request, model_id=0):
    '''公告保存
    '''
    model_id = int(model_id)
    title = request.POST.get('title', '').replace('\n', '\\n').replace('\r', '')
    sub_title = request.POST.get("sub_title", '').replace('\n', '\\n').replace('\r', '')
    post_list_server = request.POST.getlist('server_id')
    channel_list = request.POST.getlist('channel_id')
    usm = request.admin
    link_url = request.POST.get('link_url', '')
    is_ssl = request.POST.get('is_ssl', '0')
    import re
    size = request.POST.get('size', '')
    if re.sub('[\-\d+\,\.]+', '', size) != '':
        size = ''

    # 公告内容要转化为游戏客户端能接受的格式。
    content = request.POST.get('content', '')
    # content = re.sub(r'<p>|</p>','',content)
    content = content.replace('&nbsp;', '\space/')
    ChangeHTML = HTMLChange()
    ChangeHTML.feed(content)
    content = ChangeHTML.content
    content = content.replace('\space/', '&nbsp;')
    if content[-6:] == '<br />':
        content = content[:-6]

    allow_create = True
    # 权限判断   //如果不是管理员账号
    if not usm.is_manager:
        user_server_list = usm.get_resource('server').all()  # 获取当前登陆的管理员账号有权限管理的服务器列表
        user_server_id = []
        for user_server in user_server_list:
            user_server_id.append(user_server.id)

        # 添加公告的服务器不在当前登陆角色的服务器列表内，则作为没有权限操作
        for server_id in post_list_server:
            if not user_server_id.__contains__(int(server_id)):
                allow_create = False
                break

    if not allow_create:
        return HttpResponse('没有权限添加')

    if model_id == 0:
        model_id = int(request.GET.get('notice_id', '0'))

    model = None
    if model_id > 0:
        model = Notice.objects.using('write').get(id=model_id)
    if model == None:
        model = Notice()
        # model.id = 0
    old_model = copy.deepcopy(model)
    notice_type = int(request.POST.get('type', request.GET.get('type', '0')))

    # if notice_type == Notice.Notine_Type.login:
    server_list = []
    group_servers_dict = get_group_servers_dict(request)
    for g, servers in group_servers_dict.items():
        for s in servers:
            server_list.append(unicode(s.id))
    post_list_server = server_list
    # if not channel_list:
    #     agent_channels_dict = get_agent_channels_dict(request)
    #     channel_list = [c.id for c in agent_channels_dict]

    if notice_type == Notice.Notine_Type.push:
        model.content = request.POST.get('content', "")
        model.photo_id = request.POST.get('photo_id', 0)

    model.client_ver = request.POST.get('client_ver', '')
    model.status = int(request.POST.get('status', '0'))
    model.pub_ip = request.META.get('REMOTE_ADDR', '')
    model.pub_user = request.admin.id
    model.size = size
    model.link_url = link_url
    model.title = title
    model.sub_title = sub_title
    model.content = content
    model.sort = request.POST.get('noticeSort', 9999)
    model.begin_time = request.POST.get('begin_time', '')
    model.end_time = request.POST.get('end_time', '')
    model.tag = request.POST.get('tag', 0)
    model.is_temp = int(request.POST.get('is_temp', '0'))
    # model.notice_type = notice_type
    model.notice_type = 5  # 目前业务需求只需要网关登录公告
    model.intervalSecond = int(request.POST.get('intervalSecond', '0'))
    model.create_time = int(time.time())
    model.jump = request.POST.get("jump", "") if request.POST.get("jump", "") != "1" else ""
    ajax_post = request.POST.get('ajax', False) or request.is_ajax()

    not_use_template_list = [Notice.Notine_Type.scroll, Notice.Notine_Type.push]
    try:
        if model.id > 0:
            model.server.clear()
            model.group.clear()
            model.channel.clear()
        model.save(using='write')

        # 如果不是"游戏滚动公告","登录公告" 和 “推送消息”则生成静态html文件
        # if notice_type != Notice.Notine_Type.scroll and notice_type != Notice.Notine_Type.push and notice_type != Notice.Notine_Type.login:
        # 登陆公告也要生成html了
        if notice_type != Notice.Notine_Type.scroll and notice_type != Notice.Notine_Type.push:
            use_template = notice_type not in not_use_template_list
            if not link_url:
                _link_url = create_notice_html(request, model.id, title, content, notice_type, use_template, is_ssl)
                print _link_url
                model.link_url = _link_url
            model.save()

        if post_list_server:
            model.server.add(*Server.objects.using('write').filter(id__in=post_list_server))

        group_ids = request.POST.getlist('group_id')
        if group_ids:
            model.group.add(*Group.objects.using('write').filter(id__in=group_ids))

        if channel_list:
            model.channel.add(*Channel.objects.using('write').filter(id__in=channel_list))

        if ajax_post:
            # 最新消息要通知到服务端
            if notice_type == Notice.Notine_Type.game:
                for sid in post_list_server:
                    gmp = GMProtocol(int(sid))
                    result = gmp.update_notice()
            # 发协议给服务端
            if not link_url:
                return HttpResponse(
                    u'保存成功!<br>地址：%s' % '<a href="%s" target="_blank">%s</a>' % (model.link_url, model.link_url))
            else:
                return HttpResponse(
                    u'保存成功!但未更新内容到游戏内,如需更新,请清空地址再保存!<br>旧内容地址:%s' % '<a href="%s" target="_blank">%s</a>' % (
                        model.link_url, model.link_url))

        return notice_edit(request, model_id=model.id, info_msg='保存成功!')

    except Exception, e:
        traceback.print_exc()
        return HttpResponse("保存出错请重试！出错信息:%s" % e)
        if ajax_post:
            return HttpResponse("保存出错请重试！出错信息:%s" % e)

    parg = {}
    parg["model"] = old_model
    parg["group_servers_dict"] = get_group_servers_dict(request)
    parg["select_server_ids"] = [s.id for s in old_model.server.all()]

    return render_to_response('server/notice_edit.html', parg)


@Route()
@notauth
def get_new_notice(request):
    """游戏客户端获取最新的网关公告"""

    # 获取渠道号
    channel_key = request.GET.get('channel')

    # 查询对应渠道最新的公告
    channel = Channel.objects.get(channel_key=channel_key)
    notice = channel.notice_set.all().order_by('-id')[0]

    # 获取最新公告的信息
    title = notice.title
    content = notice.content
    begin_time = int(time.mktime(notice.begin_time.timetuple()))
    end_time = int(time.mktime(notice.end_time.timetuple()))

    # 组织数据
    data = '{"title": "%s", "content": "%s", "begin_time": %s, "end_time": %s}' % (title, content, begin_time, end_time)

    # 返回数据
    return HttpResponse(data)


@Route()
def notice_upload(request):
    # 上传登录公告图片
    img_path = os.path.join(NOTICE_PATH, 'img')
    _img_path = os.path.join(_NOTICE_PATH, 'img')
    msg = '没有图片'
    reqfile = request.FILES.get('fileToUpload', None)
    msg_sl = request.REQUEST.get("channel_list", '')
    sl1 = json.loads(msg_sl).get('sl', [])

    # sl2 = []
    # 去重  呃，为什么不用set直接去重？
    # for i in sl1:
    #     if i not in sl2:
    #         sl2.append(i)

    sl2 = list(set(sl1))

    model_id = int(request.REQUEST.get('notice_id', '0'))
    if reqfile and len(sl2) > 0:
        # 创建目录
        try:
            for i in sl2:
                print type(i)
                channel_key = Channel.objects.filter(id=int(i))[0].channel_key
                ser_dir = os.path.join(img_path, channel_key)
                _ser_dir = os.path.join(_img_path, channel_key)

                if not os.path.isdir(ser_dir):
                    os.makedirs(ser_dir)
                if not os.path.isdir(_ser_dir):
                    os.makedirs(_ser_dir)
        except Exception, e:
            print e
            return HttpResponse("目录错误")

        try:
            channel_key = Channel.objects.filter(id=int(sl2[0]))[0].channel_key

            ser_dir = os.path.join(img_path, channel_key)
            _ser_dir = os.path.join(_img_path, channel_key)

            img_name = os.path.join(ser_dir, str(reqfile)).replace('.jpg', '')
            _img_name = os.path.join(_ser_dir, str(reqfile)).replace('.jpg', '')
            img_name = img_name.replace('.png', '')
            _img_name = _img_name.replace('.png', '')

            img = Image.open(reqfile)
            img.save("%s.png" % img_name, "png")
            img.save("%s.png" % _img_name, "png")
            # 保存一个服务器的图片后,复制到其他服务器
            if len(sl2) > 1:
                import shutil
                for i in range(len(sl2)):
                    if i + 1 == len(sl2):
                        break
                    channel_key = Channel.objects.filter(id=int(sl2[i]))[0].channel_key
                    _channel_key = Channel.objects.filter(id=int(sl2[i + 1]))[0].channel_key
                    for j in os.listdir(os.path.join(img_path, channel_key)):
                        adir = os.path.join(img_path, channel_key)
                        bdir = os.path.join(img_path, _channel_key)
                        shutil.copyfile(os.path.join(adir, j), os.path.join(bdir, j))

                    for p in os.listdir(os.path.join(_img_path, channel_key)):
                        cdir = os.path.join(_img_path, channel_key)
                        ddir = os.path.join(_img_path, _channel_key)
                        shutil.copyfile(os.path.join(cdir, p), os.path.join(ddir, p))

            msg = '保存成功'
        except Exception, e:
            return HttpResponse("Error %s" % e)
    return HttpResponse(msg)


def create_notice_html_file(model_id, title, content, notice_type, use_template=True):
    '''创建公告模版
    '''
    gl_path = _globalpathcfg
    file_name = '%s.html' % model_id
    save_path = gl_path.get_notice_html_save_path(file_name)
    _save_path = gl_path.get_notice_html_save_path_client(file_name)
    file_tpl = open(gl_path.get_notice_html_template_path(), 'r')
    tpl_content = file_tpl.read()
    file_tpl.close()
    t = Template(tpl_content)
    html_file = open(save_path, 'w')
    if use_template:
        c = Context({"title": title, "content": content, 'notice_type': notice_type})
        c = t.render(c)
    else:
        c = content  # 只保存内容，不使用模版 || 会有乱码，需添加一个meta
    html_file.write(c.encode("utf-8"))
    html_file.close()

    # 保存到客户端会去读取的目录
    _html_file = open(_save_path, 'w')
    _html_file.write(c.encode("utf-8"))
    _html_file.close()

    return file_name


def create_notice_html(request, model_id, title, content, notice_type, use_template=True, is_ssl=0):
    file_name = create_notice_html_file(model_id, title, content, notice_type, use_template)
    file_url = _globalpathcfg.get_notice_html_url(request, file_name, is_ssl)
    return file_url


from views.game.base import GMProtocol


def push_create(request):
    '''推送公告创建
    '''
    usm = request.admin
    # 需要管理员账号
    if not usm.is_manager:
        return HttpResponse(u'没有权限操作')
    sid_list = []
    list_content = {}
    now = datetime.datetime.now()
    # base_query = Q(begin_time__lte=now) & Q(end_time__gte=now) & Q(notice_type=Notice.Notine_Type.push)
    base_query = Q(end_time__gte=now) & Q(notice_type=Notice.Notine_Type.push)
    list_push = Notice.objects.filter(base_query).prefetch_related('group')
    server_all_list = Server.objects.all()
    rootPath = os.path.dirname(__file__)
    try:
        folderPath = os.path.abspath(os.path.join(rootPath, '../../../static/notice/push'))
        if not os.path.exists(folderPath):
            os.mkdir(folderPath)

        _folderPath = os.path.abspath(os.path.join(rootPath, '../../../static/client/static/notice/push'))
        if not os.path.exists(_folderPath):
            os.mkdir(_folderPath)

        for model in list_push:
            title = model.title
            content = model.content
            fileContent = '{"id":%d,"title":"%s","message":"%s","url":"%s","start_time":"%s","end_time":"%s","photo_id":"%s","jump":"%s","sort":"%s"}' % (
                model.id,
                title,
                content,
                model.link_url.encode('utf-8'),
                int(time.mktime(model.begin_time.timetuple())),
                int(time.mktime(model.end_time.timetuple())),
                model.photo_id or "",
                model.jump or "",
                model.sort or "")
            servers_list = model.server.all()

            if len(servers_list) == 0:
                servers_list = server_all_list
                for server in servers_list:
                    if list_content.get(server.id, None) == None:
                        list_content[server.id] = []
                    list_content[server.id].append(fileContent)
            else:
                for server in servers_list:
                    if list_content.get(server.id, None) == None:
                        list_content[server.id] = []
                    list_content[server.id].append(fileContent)

        ##GM推送通知

        # for i in sid_list:
        #     try:
        #         gmp = GMProtocol(int(i))
        #         result = gmp.push_online()
        #         if result == 0:
        #             print '服务器%s推送OK' %(i)
        #         else:
        #             continue
        #     except Exception,e:
        #         traceback.print_exc()
        server_all_list = Server.objects.all()
        for s in server_all_list:
            filePath_template = os.path.abspath(os.path.join(rootPath, '../../../static/notice/push/%s.json'))
            _filePath_template = os.path.abspath(os.path.join(_folderPath, '%s.json'))
            filePath = filePath_template % s.id
            _filePath = _filePath_template % s.id
            if s.id not in list_content:
                file_handler = open(filePath, "w")
                file_handler.write("")
                file_handler.close()
                _file_handler = open(filePath, "w")
                _file_handler.write("")
                _file_handler.close()
                continue
            file_handler = open(filePath, "w")
            file_handler.write('[%s]' % (','.join(list_content[s.id])))
            file_handler.close()
            _file_handler = open(_filePath, "w")
            _file_handler.write('[%s]' % (','.join(list_content[s.id])))
            _file_handler.close()

    except Exception, e:
        err_msg = trace_msg()
        print('create push file:', e)

    return render_to_response('feedback.html', locals())


# def get_notice_cont(model,server_obj):
#         rootPath = os.path.dirname(__file__)
#         if model.notice_type == Notice.Notine_Type.scroll:
#             filePath_template = os.path.abspath(os.path.join(rootPath, '../../../static/notice/scroll/%s.json'))
#             fileContent = "{\"beginDate\":\"%s\",\"endDate\":\"%s\",\"intervalSecond\":%s,\"txt\":\"%s\"}" % (model.begin_time,
#                                                                               model.end_time,
#                                                                               model.intervalSecond,
#                                                                               model.title.encode('utf-8'))

#        #  # 最新消息公告
#        # if model.notice_type == 2:
#        #     size_str = '0.7,0.8'
#        #     if None != model.size and '' != model.size:
#        #         size_str = model.size
#        #     filePath_template = os.path.abspath(os.path.join(rootPath, '../../../static/notice/game/%s.json'))
#        #     fileContent = "{\"beginDate\":\"%s\",\"endDate\":\"%s\",\"title\":\"%s\",\"size\":[%s],\"positioin\":[-1,-1],\"url\":\"%s\"}" % (model.begin_time,
#        #                                                                       model.end_time,
#        #                                                                       model.title.encode('utf-8'),
#        #                                                                       size_str.encode('utf-8'),
#        #                                                                       '%s?sid=%s' % (model.link_url.encode('utf-8'),server_obj.id))

#         #登录公告和分区公告
#         if model.notice_type == Notice.Notine_Type.group or model.notice_type == Notice.Notine_Type.login:
#             size_str = '0.7,0.8'
#             if None != model.size and '' != model.size:
#                 size_str = model.size
#             filePath_template = os.path.abspath(os.path.join(rootPath, '../../../static/notice/login/%s.json'))
#             fileContent = "{\"create_time\":\"%s\",\"tag\":%d,\"beginDate\":\"%s\",\"endDate\":\"%s\",\"title\":\"%s\",\"size\":[%s],\"positioin\":[-1,-1],\"url\":\"%s\",\"status\":%d,\"sort\":%d}" % (
#             model.create_time,
#             int(model.tag),
#             model.begin_time,
#             model.end_time,
#             model.title.encode('utf-8'),
#             size_str.encode('utf-8'),
#             '%s?sid=%s' % (model.link_url.encode('utf-8'), server_obj.id), 
#             int(model.status),
#             model.sort if model.sort else 9999)

#         return filePath_template,fileContent

def get_notice_cont(model, channel_model_id):
    rootPath = os.path.dirname(__file__)
    if model.notice_type == Notice.Notine_Type.scroll:
        filePath_template = os.path.abspath(os.path.join(rootPath, '../../../static/notice/scroll/%s.json'))
        fileContent = "{\"beginDate\":\"%s\",\"endDate\":\"%s\",\"intervalSecond\":%s,\"txt\":\"%s\"}" % (
            model.begin_time,
            model.end_time,
            model.intervalSecond,
            model.title.encode('utf-8'))

    # 登录公告和分区公告
    if model.notice_type == Notice.Notine_Type.group or model.notice_type == Notice.Notine_Type.login:
        size_str = '0.7,0.8'
        if None != model.size and '' != model.size:
            size_str = model.size
        url2 = urlparse.urlparse(model.link_url).path
        filePath_template = os.path.abspath(os.path.join(rootPath, '../../../static/notice/login/%s.json'))
        fileContent = "{\"create_time\":\"%s\",\"tag\":%d,\"beginDate\":\"%s\",\"endDate\":\"%s\",\"title\":\"%s\",\"sub_title\":\"%s\",\"size\":[%s],\"positioin\":[-1,-1],\"url\":\"%s\",\"url2\":\"%s\",\"status\":%d,\"sort\":%d}" % (
            model.create_time,
            int(model.tag),
            model.begin_time,
            model.end_time,
            model.title.encode('utf-8'),
            model.sub_title.encode('utf-8') if model.sub_title else "",
            size_str.encode('utf-8'),
            '%s?sid=%s' % (model.link_url.encode('utf-8'), channel_model_id),
            '%s' % (url2.encode('utf-8')),
            int(model.status),
            model.sort if model.sort else 9999)

    return filePath_template, fileContent


def notice_createStaticFile(request, model_id=0):
    '''公告json静态文件创建
    '''
    model_id = int(model_id)
    just_check = request.GET.get('just_check', '')
    if model_id == 0:
        model_id = int(request.GET.get('notice_id', '0'))
    msg = '未生成!'
    if model_id > 0:
        filePath_template = ""
        fileContent = ""
        filePath = ""

        try:
            model = Notice.objects.prefetch_related('server').using('write').get(id=model_id)
            model_server_list = model.server.all()
            model_channel_list = model.channel.all()
            usm = request.admin

            allow_create = True
            # 权限判断   //如果不是管理员账号
            if not usm.is_manager:
                user_server_list = usm.get_resource("server").all()
                # 获取当前登陆的管理员账号有权限管理的服务器列表
                # 需要生成公告的服务器不在当前登陆角色的服务器列表内，则作为没有权限操作
                for model_server in model_server_list:
                    if not user_server_list.__contains__(model_server):
                        allow_create = False
                        break
            if not allow_create:
                return HttpResponse('没有权限生成')

            rootPath = os.path.dirname(__file__)

            msg = ''
            if just_check:
                err_sids = []
                empty_sids = []
                for ser in model_server_list:
                    filePath_template, _ = get_notice_cont(model, ser)
                    filePath = filePath_template % ser.id
                    if os.path.exists(filePath):
                        try:
                            file_handler = open(filePath, "rb")
                            j_d = json.loads(file_handler.read())
                            if model.title != j_d['title'] and model.notice_type != 1:
                                err_sids.append(ser.id)
                        except Exception, e:
                            traceback.print_exc()
                        finally:
                            file_handler.close()
                    else:
                        empty_sids.append(ser.id)
                return HttpResponse(u'%s(%s):<br><br>公告不符服务器id:<br>%s<br>不存在的服务器id:<br>%s<br>' %
                                    (model.get_notice_type_display(), model.id, str(err_sids), str(empty_sids))
                                    )
            else:
                for ser in model_server_list:
                    filePath_template, fileContent = get_notice_cont(model, ser)
                    filePath = filePath_template % ser.id
                    file_handler = open(filePath, "w")
                    file_handler.write(fileContent)
                    file_handler.close()
                    # msg += '%s,' % ser.id
                msg += '成功！'

        except Exception, e:
            msg += '失败,原因 %s' % e
            import traceback
            traceback.print_exc()
            print('notice createStaticFile error:', e)

    return HttpResponse(msg)


# -----------------------


def can_delete_notice(filePath, notine_model):
    '''判断能否删除公告
    '''
    if notine_model.notice_type == 1:
        return True
    if os.path.exists(filePath):
        try:
            file_handler = open(filePath, "rb")
            j_d = json.loads(file_handler.read())
            if notine_model.title == j_d['title']:
                return True
        except Exception, e:
            return False
            traceback.print_exc()
        finally:
            file_handler.close()
    else:
        return False


def notice_remove(request, model_id=0):
    '''公告删除
    '''
    model_id = int(model_id)

    if model_id == 0:
        model_id = int(request.GET.get('notice_id', '0'))
    if model_id > 0:
        try:
            import datetime
            all_notice_list = [item for item in Notice.objects.prefetch_related('server').all()]
            now = datetime.datetime.now()
            model = Notice.objects.using('write').get(id=model_id)
            try:
                rootPath = os.path.dirname(__file__)

                if model.notice_type == 4:
                    group_dict = {}
                    for item in all_notice_list:
                        if item.id == model.id:
                            continue
                        if item.end_time <= now:
                            continue

                        for group in item.group.all():
                            group_dict[group.id] = 1

                    for group in model.group.all():
                        if None != group_dict.get(group.id, None):
                            continue
                        filePath_template = os.path.abspath(
                            os.path.join(rootPath, '../../../static/notice/push/%s.json' % group.group_key))
                        os.remove(filePath_template)
                else:
                    if model.notice_type == Notice.Notine_Type.game:  # 游戏公告不删除
                        pass
                    else:
                        for item in model.server.all():
                            dir_name = Notice.TYPE_DICT.get(model.notice_type)['path']
                            filePath_template = os.path.abspath(
                                os.path.join(rootPath, '../../../static/notice/%s/%s.json' % (dir_name, item.id)))
                            if can_delete_notice(filePath_template, model):
                                os.remove(filePath_template)
            except:
                print('delete file error')
            model.server.clear()
            model.delete(using='write')
        except Exception, e:
            print('notice remove error:', e)
    ajax = request.GET.get('ajax', '')
    if ajax:
        return HttpResponse('{"code":0}')
    return render_to_response('feedback.html')


class NoticeCreater(object):
    notice_save_path = 'notice'
    notice_save_path_client = os.path.join('client', 'static', 'notice')


class LoginNoticeCreater(NoticeCreater):
    '''登录公告创建
    登陆公告在选服前，所以不需要生成各个服的公告
    '''
    json_file_save_dir = _globalpathcfg.get_static_root(NoticeCreater.notice_save_path, 'login')
    json_file_save_dir_client = _globalpathcfg.get_static_root(NoticeCreater.notice_save_path_client, 'login')

    def __init__(self, notice_model):
        self.server_models = notice_model.server.all()
        self.notice_model = notice_model
        self.channel_models = notice_model.channel.all()

    @classmethod
    def get_server_json_file_path(cls, server_model):
        return os.path.join(cls.json_file_save_dir, '%s.json' % server_model.id)

    @classmethod
    def get_channel_json_file_path(cls, channel_model_id):
        return os.path.join(cls.json_file_save_dir, '%s.json' % channel_model_id)

    @classmethod
    def clear_json_file(cls, channel_model_id):
        # server_json_save_path = cls.get_server_json_file_path(server_model)
        # if os.path.isfile(server_json_save_path):
        #     try:os.remove(server_json_save_path)
        #     except:pass
        channel_json_save_path = cls.get_channel_json_file_path(channel_model_id)
        _channel_json_save_path = os.path.join(cls.json_file_save_dir_client, '%s.json' % channel_model_id)
        if os.path.isfile(channel_json_save_path):
            try:
                os.remove(channel_json_save_path)
            except:
                pass

        if os.path.isfile(_channel_json_save_path):
            try:
                os.remove(_channel_json_save_path)
            except:
                pass

    def create_notice_static_file(self):
        loginNoticePath = os.path.join(self.json_file_save_dir, 'login.json')
        # for server_obj in self.server_models:
        #     channel_json_save_path = self.get_server_json_file_path(server_obj)
        #     filePath_template,fileContent = get_notice_cont(self.notice_model, server_obj)
        loginContent = []
        for channel in self.channel_models:
            channel_json_save_path = self.get_channel_json_file_path(channel.channel_key)
            _channel_json_save_path = os.path.join(self.json_file_save_dir_client, '%s.json' % channel.channel_key)
            filePath_template, fileContent = get_notice_cont(self.notice_model, channel.channel_key)
            fpContent = []
            if os.path.isfile(channel_json_save_path):
                with open(channel_json_save_path, 'rb') as fp:
                    fpContent = fp.read()
                    fpContent = json.loads(fpContent) if fpContent else []
                    if fpContent:
                        fpContent = fpContent if fpContent else []

            with open(channel_json_save_path, 'wb') as fp:
                fileContent = json.loads(fileContent)
                fpContent.extend([fileContent])
                fp.write(json.dumps(fpContent))
                with open(_channel_json_save_path, 'wb') as jp:
                    jp.write(json.dumps(fpContent))
                if fileContent not in loginContent:
                    loginContent.extend([fileContent])


class GameNoticeCreater(NoticeCreater):
    '''游戏公告创建
    '''

    def __init__(self, server_model, notice_list):
        self.server_model = server_model

        self.notice_list = sorted(notice_list, key=lambda n: n.tag)

        self.json_file_save_dir = _globalpathcfg.get_static_root(self.notice_save_path, 'game')

        self.json_file_save_path = os.path.join(self.json_file_save_dir, '%s.json' % server_model.id)

        self.html_save_dir = _globalpathcfg.get_static_root(self.notice_save_path, 'html', server_model.id)

        self.the_index_file_name = 'index.html'
        self.the_menu_file_name = 'menu.html'

        self.the_index_save_path = os.path.join(self.html_save_dir, self.the_index_file_name)
        self.the_menu_save_path = os.path.join(self.html_save_dir, self.the_menu_file_name)

        if len(notice_list) > 0:
            self.the_first_notie = self.notice_list[0]
            self.the_first_address = self.get_first_notice_address()
        else:
            self.the_first_notie = None
            self.the_first_address = ''

    def get_notice_html_str(self, template_name, dict_kwargs):
        '''获取公告模版字符串
        '''
        return loader.render_to_string(template_name, dict_kwargs)

    def get_first_notice_address(self):
        '''获取公告的地址
        '''
        notice = self.the_first_notie
        return '/'.join(notice.link_url.split('/')[:-1])

    def create_server_notice_json(self):
        '''创建游戏公告json文件
        '''

        try:
            the_min_begindate = min(self.notice_list, key=lambda n: n.begin_time).begin_time
            the_max_endDate = max(self.notice_list, key=lambda n: n.end_time).end_time
            the_index_url = '%s/%s/%s' % (self.the_first_address, self.server_model.id, self.the_index_file_name)
            game_notice_dict = {}
            game_notice_dict['beginDate'] = datetime_to_str(the_min_begindate)
            game_notice_dict['endDate'] = datetime_to_str(the_max_endDate)
            game_notice_dict['title'] = self.the_first_notie.title
            game_notice_dict['url'] = the_index_url
            game_notice_dict['game_notice_dict'] = [-1, -1]
            game_notice_dict['size'] = [0.9, 0.9]
            cont = json.dumps(game_notice_dict, ensure_ascii=False)
            with open(self.json_file_save_path, 'wb') as fp:
                fp.write(cont)
            # fpContent = []
            # if os.path.isfile(self.json_file_save_path):
            #     with open(self.json_file_save_path,'rb') as fp:
            #         fpContent = fp.read()
            #         if fpContent:
            #             fpContent = json.loads(fpContent)

            # with open(self.json_file_save_path,'wb') as fp:
            #     fpContent.extend([json.loads(cont)])
            #     fp.write(json.dumps(fpContent))
        except:
            print trace_msg()

    def create_server_notice_html(self):
        '''创建游戏公告html文件
        '''

        the_menu_uri = '/static/notice/html/%s/%s' % (self.server_model.id, self.the_menu_file_name)
        dict_kwargs = {"server_modle": self.server_model,
                       "notice_list": self.notice_list,
                       "first_notie": self.the_first_notie,
                       "the_menu_uri": the_menu_uri,
                       }

        the_index_cont = self.get_notice_html_str('server/notice_index.html', dict_kwargs)
        # the_menu_cont = self.get_notice_html_str('server/notice_menu.html',dict_kwargs)
        try:
            with open(self.the_index_save_path, 'wb') as fp:
                fp.write(the_index_cont)
        #            with open(self.the_menu_save_path,'wb') as fp_m :
        #                fp_m.write(the_menu_cont)
        except:
            print trace_msg()

    def create_notice_static_file(self):
        '''创建游戏公告文件
        '''
        try:
            self.create_server_notice_html()
            self.create_server_notice_json()

        except:
            print trace_msg()

    def clear(self):
        try:
            if os.path.exists(self.json_file_save_path):
                os.remove(self.json_file_save_path)
            if os.path.exists(self.the_index_save_path):
                os.remove(self.the_index_save_path)
        except:
            pass


def create_server_notice():
    ''' 创建服务器的公告
    '''
    now = datetime.datetime.now()
    # base_query = Q(begin_time__lte=now) & Q(end_time__gte=now) & Q(status=1)
    base_query = Q(begin_time__lte=now) & Q(end_time__gte=now)

    # 只有游戏公告和登录公告需要创建json文件
    game_notice_query = base_query & Q(notice_type=Notice.Notine_Type.game)
    game_notice_list = Notice.objects.prefetch_related('server').filter(game_notice_query)

    # 模版公告
    temp_notice_query = Q(notice_type=Notice.Notine_Type.game) & Q(is_temp=1) & Q(status=1)
    temp_notice_list = Notice.objects.prefetch_related('server').filter(temp_notice_query)
    temp_notice_dict = {}

    for notice in temp_notice_list:
        notice_server_list = notice.server.all()
        for server in notice_server_list:
            begin_time = server.create_time
            timedelta = datetime.datetime.now() - begin_time
            if timedelta.days >= 9:
                notice.server.remove(*Server.objects.filter(id__in=[int(server.id)]))
                notice.save()
                continue

            temp_notice_dict.setdefault(server, [])
            temp_notice_dict[server].append(notice)

    login_notice_query = base_query & Q(notice_type=Notice.Notine_Type.login)

    # login_notice_model_list = Notice.objects.prefetch_related('server').filter(login_notice_query).order_by('-id')[:1]
    # login_notice_model = login_notice_model_list[0] if login_notice_model_list else None
    login_notice_model_list = Notice.objects.prefetch_related('server').filter(login_notice_query)
    server_notice_list = {}
    channel_notice_list = {}

    # 创建游戏公告
    for notice in game_notice_list:
        notice_server_list = notice.server.all()
        for server in notice_server_list:
            server_notice_list.setdefault(server, [])
            server_notice_list[server].append(notice)

    # 创建登陆公告
    for notice in login_notice_model_list:
        notice_channel_list = notice.channel.all()
        for channel in notice_channel_list:
            channel_notice_list.setdefault(channel, [])
            channel_notice_list[channel].append(notice)

    for server_model in Server.objects.all():
        notice_list = server_notice_list.get(server_model, [])

        ###添加模版公告到notice_list
        https_url = 'https://fytx2.37wan.server.fytxonline.com:8004/static/notice/html/'
        temp_list = temp_notice_dict.get(server_model, [])
        begin_time = server_model.create_time
        end_time = datetime.datetime.replace(begin_time + datetime.timedelta(days=9), hour=23, minute=59, second=59)
        if temp_list:
            for i in temp_list:
                i.begin_time = begin_time
                i.end_time = end_time
                if server_model.is_ios == 1:
                    i.link_url = '%s%s.html' % (https_url, i.id)

            notice_list.extend(temp_list)

        if notice_list:
            for i in notice_list:
                if i.tag:
                    i.tag = int(i.tag)
                else:
                    continue
        game_notrce_creater = GameNoticeCreater(server_model, notice_list)

        if notice_list:
            game_notrce_creater.create_notice_static_file()
        else:
            print '[%s] %s clear json file' % (datetime.datetime.now(), server_model.name)
            game_notrce_creater.clear()

        LoginNoticeCreater.clear_json_file(server_model)

    # 登陆弹窗公告的
    for channel in Channel.objects.all():
        LoginNoticeCreater.clear_json_file(channel.channel_key)
    if login_notice_model_list:
        for login_notice_model in login_notice_model_list:
            login_notice_creater = LoginNoticeCreater(login_notice_model)
            login_notice_creater.create_notice_static_file()

    json_file_save_dir = _globalpathcfg.get_static_root(NoticeCreater.notice_save_path, 'login')
    _json_file_save_dir = _globalpathcfg.get_static_root(NoticeCreater.notice_save_path_client, 'login')
    for channel in Channel.objects.all():
        MD5path = os.path.join(STATIC_ROOT, 'md5', '%s.json' % channel.channel_key)
        _MD5path = os.path.join(STATIC_ROOT, 'client', 'static', 'md5', '%s.json' % channel.channel_key)
        path = os.path.join(json_file_save_dir, '%s.json' % channel.channel_key)
        _path = os.path.join(_json_file_save_dir, '%s.json' % channel.channel_key)
        writeMd5 = False
        print '%s making file' % (channel.channel_key)

        if not os.path.isfile(path):
            with open(path, 'wb') as fp:
                fp.write('')

        if not os.path.isfile(_path):
            with open(_path, 'wb') as fp:
                fp.write('')

        if os.path.isfile(path):
            fileMd5 = GetFileMd5(path)

        if os.path.isfile(MD5path):
            with open(MD5path, 'rb') as mp:
                content = mp.read()
                content = json.loads(content) if content else {}
                if content.has_key("notice") and content["notice"]:
                    last_fileMd5 = content["notice"]
                    if last_fileMd5 != fileMd5:
                        content["notice"] = fileMd5
                        writeMd5 = True
                if not content.has_key("notice") or not content["notice"]:
                    content["notice"] = fileMd5
                    writeMd5 = True

        if writeMd5:
            with open(MD5path, 'wb') as np:
                np.write(json.dumps(content) if content else '')
            with open(_MD5path, 'wb') as np:
                np.write(json.dumps(content) if content else '')


@Route()
def notice_menu(request, template_name='server/notice_menu.html'):
    '''游戏公告菜单
    '''
    server_id = int(request.REQUEST.get('sid', '') or 0)
    return render_to_response(template_name, locals())


def GetFileMd5(filePath):
    if not os.path.isfile(filePath):
        return
    hashi = hashlib.md5()
    f = file(filePath, 'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        hashi.update(b)
    f.close()
    return hashi.hexdigest()
