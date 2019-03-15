# -*- coding: utf-8 -*-
#
# 游戏活动相关
#
import os
import hashlib
import zipfile
import time

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
from settings import STATIC_ROOT, STATIC_PATH
from util import trace_msg, str_to_datetime, constant, time_util
from models.log import Log
from models.center import Server, Notice, Group
from cache import center_cache
from views.base import getConn, json_response
from util.http import http_post
import json, datetime, time
from urls.AutoUrl import Route
from views.widgets import get_group_servers_dict, get_agent_channels_dict, groups_servers
from .base import GMProtocol, GMActionType
from util.threadpoll import ThreadPool
from views.log.query import query_view
from views.game.base import GMProtocol
from models.game import Activity, OperationActivity
from models.calevents import Calevents
from views.base import notauth
from views.game.activity_def import *
from models.log import DictDefine
from django.utils.datastructures import SortedDict as OrderedDict

ACTIVITY_PATH = os.path.join(STATIC_ROOT, 'activity')


def get_activity_model(request):
    '''获取活动模型
    '''
    activity_id = int(request.REQUEST.get('activity_id', '') or 0)
    if activity_id:
        model = Activity.objects.prefetch_related('server').get(id=activity_id)
    else:
        model = Activity()
    return model


@Route()
def activity_list(request, template="game/activity_list.html"):
    '''活动列表
    '''
    return query_view(request, query_name='游戏活动列表')


@Route()
def activity_edit(request, model=None, err_msg='', template="game/activity_edit.html"):
    '''活动编辑
    '''
    is_copy = request.REQUEST.get('is_copy', '')
    try:
        if not model:
            activity_id = int(request.REQUEST.get('activity_id', '') or 0)
            model = model or get_activity_model(request)
        model.id = model.id or 0
        if model.id:
            select_server_ids = [s.id for s in model.server.all()]
        if is_copy:
            model.id = 0
            msg = json.loads(model.msg)
            if isinstance(msg, dict):
                if not msg:
                    return HttpResponse('空配置的活动不能复制.')

                msg['kid'] = int(time.time())
                msg["id"] = 0
                model.msg = json.dumps(msg)
                print model.msg
            model.name = '%s-copy' % model.name

    except Exception, e:
        err_msg = trace_msg()

    # group_servers_dict = get_group_servers_dict(request)
    group_servers_dict = groups_servers(request)

    return render_to_response(template, locals())


def is_ditto_activity_in_date(model):
    '''活动时间冲突检测
    '''
    err_msg = ''
    err_msg_list = []
    # ditto_activity_list =  Activity.objects.prefetch_related('server').filter(type=model.type,sdate__range=[model.sdate,model.edate]).exclude(name=model.name)

    ditto_activity_list = Activity.objects.prefetch_related('server').filter(type=model.type, sdate__lte=model.sdate,
                                                                             edate__gte=model.sdate).exclude(
        name=model.name)

    # 排除不检测冲突的 活动
    ditto_activity_list = ditto_activity_list.exclude(Q(type__in=Activity.NOT_CONFLICT_CHECK_LIST) | Q(is_temp=1))

    if ditto_activity_list:
        for a in ditto_activity_list:
            ditto_server_ids = model.server_ids
            a_server_list = a.server.all()
            for s in a_server_list:
                if s.id in ditto_server_ids:
                    err_msg_list.append('%s - %s(%s) 时间段:%s - %s' % (a.name, s.name, s.id, a.sdate, a.edate))
    if err_msg_list:
        err_msg = '%s 时间段:%s - %s 与以下服务器冲突:\n' % (model.name, model.sdate, model.edate) + '-' * 40 + '\n' + '\n'.join(
            err_msg_list)
    return err_msg


@Route()
def activity_save(request):
    '''活动保存
    '''
    model = None
    err_msg = ''

    try:
        model = get_activity_model(request)
        activity_id = request.REQUEST.get('activity_id', '')
        model.set_attr('name', request.REQUEST.get('name', '').strip(), null=False)
        model.set_attr('type', request.REQUEST.get('type', '').strip(), null=False)
        model.set_attr('info', request.REQUEST.get('info', '').strip(), null=False)
        model.set_attr('sdate', request.REQUEST.get('sdate', '0').strip(), value_handler=str_to_datetime, null=False)
        model.set_attr('edate', request.REQUEST.get('edate', '0').strip(), value_handler=str_to_datetime, null=False)
        model.set_attr('is_auto', request.REQUEST.get('is_auto', '0'), value_handler=int, null=True)
        model.set_attr('is_auto_off', request.REQUEST.get('is_auto_off', '0'), value_handler=int, null=True)
        model.set_attr('is_temp', request.REQUEST.get('is_temp', '0'), value_handler=int, null=True)
        msg = request.REQUEST.get('msg', '{}').strip()
        tmp_msg = {}
        try:
            tmp_msg = json.loads(msg)
        except:
            err_msg = '非JSON'
        # if tmp_msg['id']==0:
        #     print 99999999999,activity_id
        #     tmp_msg['id']=int(activity_id)+1000
        #     msg=json.dumps(tmp_msg)
        model.set_attr('msg', msg, null=False)

        server_ids = request.REQUEST.getlist('server_id')
        if model.is_temp == 1 and not server_ids:
            server_ids = [-1]

        # if not server_ids:
        #     err_msg = '没有选择服务器!'
        # else:
        model.set_attr('server_ids', server_ids, value_handler=lambda x: [int(sid) for sid in x], null=True)
        # if model.type != '参数打折':
        #     err_msg  = is_ditto_activity_in_date(model)
        if not err_msg:
            model.save()

        Calevents.create_event(event_name='[%s]-%s' % (model.type, model.name), desc=model.info,
                               operator=request.admin.username, start=model.sdate,
                               end=model.edate)
    except Exception, e:
        err_msg = trace_msg()
    return activity_edit(request, model, err_msg=err_msg)


@Route()
def activity_remove(request):
    '''活动删除
    '''
    try:
        activity_ids = request.REQUEST.getlist('activity_id')
        if activity_ids:
            for model in Activity.objects.filter(id__in=activity_ids):

                # now = datetime.datetime.now()
                # if now < model.edate:
                #     err_msg = "进行中的活动不允许删除"
                if model.status not in [0, 1]:
                    err_msg = "当前状态不允许删除！"
                    continue
                # 删除活动前先关闭活动
                # for s in model.server.all():
                #    result = activity_action(model, 'off', s.id, model.msg, -999)
                model.delete()
    except Exception, e:
        err_msg = trace_msg()
    return render_to_response('feedback.html', locals())


def activity_action(activity_model, action, server_id, msg, admin_id, return_json=False, force_log=False):
    _r = {"code": -1, "msg": "", "content": []}
    try:
        if activity_model and server_id:
            activity_cls = activity_model.get_activity_protocol_class()
            save_log = False
            action_type = 0
            remark1 = activity_model.name
            remark2 = ''
            if activity_cls:
                activity = activity_cls(server_id, activity_model=activity_model)
                activity.gmp.time_out = 30
                _r["server_id"] = server_id
                _r["server_name"] = activity.gmp.server.name
                # 有提交MSG参数就使用
                msg = msg if msg else activity_model.msg
                msg = json.loads(msg)
                if action == 'on':
                    resutl = activity.on(msg)
                    save_log = True
                    action_type = GMActionType.activi_ty_on
                    remark2 = '开启'
                elif action == 'off':
                    resutl = activity.off(msg)
                    save_log = True
                    remark2 = '关闭'
                    action_type = GMActionType.activity_off
                elif action == 'query':
                    remark2 = '查询'
                    content = activity.query()
                    resutl = 0 if content else -1
                    _r["content"] = [content]

                _r["code"] = resutl
                _r["msg"] = '%s:%s' % (remark2, activity.rsp_map.get(resutl, str(resutl)))
                if save_log and getattr(activity_cls, 'IS_SAVE_LOG'):
                    activity.gmp.add_player_id(activity_model.id)  # 使用player_id来记活动ID
                    activity.gmp.save_log(admin_id, action_type, resutl, remark1=remark1, remark2=_r["msg"],
                                          force=force_log)
        print _r
    except:
        _r["msg"] = trace_msg()
    return json.dumps(_r) if return_json else _r


@Route()
def activity_status(request, template='game/activity_status.html'):
    '''活动状态
    '''
    model = get_activity_model(request)
    default_params = model.get_activity_protocol_class().get_default_msg()
    return render_to_response(template, locals())


@Route()
def activity_setting(request, template='game/activity_setting.html'):
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    is_read = request.REQUEST.get('is_read', '')
    model = get_activity_model(request)
    default_params = model.get_activity_protocol_class().get_default_msg()
    charge_dict = DictDefine.get_dict_for_key("recharge_type")
    charge_dict = OrderedDict(sorted(charge_dict.items(), key=lambda t: int(t[0])))
    return render_to_response(template, locals())


@Route()
def activity_on(request):
    '''活动开启
    '''
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    msg = request.REQUEST.get('msg', '')
    activity_model = get_activity_model(request)
    if msg:
        msg = json.loads(msg)
        if msg and type(msg) == dict:
            Type = activity_model.type
            type_id = activity_model.activity_id(Type)
            # if msg['id'] ==0:
            #     return HttpResponse("activity_model.id参数异常！")
            msg["id"] = activity_model.id + 1000
            msg["type"] = type_id or 0
            msg["rm"] = False
            if msg.has_key("ae"):
                new_ae = datetime.datetime.fromtimestamp(msg["ae"]).strftime('%Y-%m-%d %H:%M:%S')
                activity_model.set_attr('edate', new_ae, value_handler=str_to_datetime, null=False)
            if msg.has_key("ab"):
                new_ab = datetime.datetime.fromtimestamp(msg["ab"]).strftime('%Y-%m-%d %H:%M:%S')
                activity_model.set_attr('sdate', new_ab, value_handler=str_to_datetime, null=False)
        msg = activity_model.msg = json.dumps(msg)
        activity_model.save(using="write")

    Open = request.REQUEST.get('open', '')
    if Open == "all":
        servers = activity_model.server.all()
        msg = activity_model.msg
        unSuccess = []
        for s in servers:
            result = activity_action(activity_model, 'on', s.id, msg, request.admin.id, True)
            result = json.loads(result)
            if result["code"] != 0:
                unSuccess.append(str(s.id))

        msg = str(unSuccess) + "开启不成功"
        if unSuccess:
            activity_model.status = 3
            activity_model.save()
            return HttpResponse(msg)
        activity_model.status = 2
        activity_model.save()
        return HttpResponse("全部开启成功")

    if not server_id:
        _r = {"code": -1, "msg": ""}
        try:
            _r['msg'] = '保存活动配置成功!'
            _r["code"] = 0
            activity_model.save()
        except:
            err_msg = trace_msg()
            _r['msg'] = err_msg
        return HttpResponse(json.dumps(_r))

    activity_model.status = 2
    activity_model.save()
    return HttpResponse(activity_action(activity_model, 'on', server_id, msg, request.admin.id, True))


@Route()
def activity_off(request):
    '''关闭活动
    '''
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    msg = request.REQUEST.get('msg', '')
    activity_model = get_activity_model(request)

    close = request.REQUEST.get('close', '')
    if close == "all":
        servers = activity_model.server.all()
        msg = activity_model.msg
        unSuccess = []
        for s in servers:
            result = activity_action(activity_model, 'off', s.id, msg, request.admin.id, True)
            result = json.loads(result)
            if result["code"] != 0:
                unSuccess.append(str(s.id))
        msg = str(unSuccess) + "关闭不成功"
        if unSuccess:
            activity_model.status = 3
            activity_model.save()
            return HttpResponse(msg)
        activity_model.status = 1
        activity_model.save()
        return HttpResponse("全部关闭成功")

    return HttpResponse(activity_action(activity_model, 'off', server_id, msg, request.admin.id, True))


@Route()
@json_response
def activity_query(request):
    '''活动查询
    '''
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    msg = request.REQUEST.get('msg', '')
    activity_model = get_activity_model(request)
    if not server_id:
        _r = {"code": -1, "msg": "", "content": []}
        try:
            model = get_activity_model(request)
            _r["code"] = 0
            _r["content"] = [json.loads(model.msg)]
        except:
            _r['msg'] = trace_msg()
        return _r
    result = activity_action(activity_model, 'query', server_id, msg, request.admin.id, True)
    result = json.loads(result)
    # ((0,'未开始'),(1,'关闭成功'),(2,'开启成功'),(3,'服务器配置异常'),)
    if result["code"] == 0 and result["content"][0]["open"] == False:
        activity_model.status = 1
    elif result["code"] == 0 and result["content"][0]["open"] == True:
        activity_model.status = 2
    else:
        activity_model.status = 3
    activity_model.save()
    return HttpResponse(json.dumps(result))


@Route()
def activity_upload(request):
    '''活动图片上传
    '''
    # 上传登录公告图片
    img_path = os.path.join(ACTIVITY_PATH, 'img')
    rsp = {
        "msg": "没有图片"
    }
    file_ext = '.png'
    reqfile = request.FILES.get('fileToUpload', None)
    pid = request.REQUEST.get('pid', '')
    if reqfile:
        # 创建目录
        try:
            if not os.path.isdir(img_path):
                os.makedirs(img_path)
        except Exception, e:
            return HttpResponse({"msg": "目录错误"})
        try:
            old_img_name, old_ext = os.path.splitext(str(reqfile))
            img_name = raw_img_name = hashlib.md5(old_img_name).hexdigest()
            count = 0
            path_name = os.path.join(img_path, img_name)
            while os.path.isfile(path_name + file_ext):
                count += 1
                img_name = '%s_%s' % (raw_img_name, count)
                path_name = os.path.join(img_path, img_name)
            img = Image.open(reqfile)
            img.save("%s" % path_name + file_ext, "png")

            # 取消 zip 保存 20160616
            # with zipfile.ZipFile(path_name + '.zip', 'w') as zipimg:
            #   zipimg.write(path_name+file_ext, img_name+file_ext)

            # for python 2.6
            #  import contextlib
            #  with contextlib.closing(zipfile.ZipFile(path_name + '.zip', 'w')) as zipimg:
            #  zipimg.write(path_name+file_ext, img_name+file_ext)

            rsp = {
                "pid": pid,
                "key": img_name,
                "msg": "保存成功",
            }
        except Exception, e:
            print trace_msg()
            return HttpResponse("Error %s" % e)
    return HttpResponse(json.dumps(rsp))


def get_activity_status(activity_type, server, server_time, query_type=None):
    class hashabledict(dict):
        def __hash__(self):
            return hash(tuple(sorted(self.items())))

    def get_ac_dict(aid, sd, ed):
        return hashabledict({
            'aid': aid,
            'sdate': sd,
            'edate': ed,
        })

    result = {'cur': [], 'nor': [], 'out': []}
    if query_type == 'type':
        activity_set = Activity.objects.filter(server=server)
    else:
        activity_set = Activity.objects.filter(type=activity_type, server=server)

    for ac in activity_set:
        ac_cls = ac.get_activity_protocol_class()
        if not ac_cls:
            continue
        act = ac_cls(server.id, activity_model=ac)
        act.gmp.time_out = 30
        act_config = act.query()
        sd = ed = 0
        is_open = True
        if len(act_config) > 1:
            if ac_cls == SevenDaysActivity:
                sd = act_config.get('rbt')
                ed = act_config.get('ret')
            elif ac_cls == CustomGiftActivity:
                sd = act_config[0][4]
                ed = act_config[0][5]
            elif ac_cls == DiscountActivity:
                sd = act_config[0][0]
                ed = act_config[0][1]
            elif ac_cls in (AccumulatedPayActivity, AccumulatedConsumeActivity):
                sd = act_config.get('ab')
                ed = act_config.get('ae')
            elif ac_cls == DailySinglePayActivity:
                sd = act_config[-2]
                ed = act_config[-1]
                if act_config[1] == 0:
                    is_open = False
            elif ac_cls == FestivalActivity:
                sd = act_config.get('bt')
                ed = act_config.get('et')
            elif ac_cls == RankingActivity:
                sd = act_config.get('time')[1]
                ed = act_config.get('time')[2]

        if sd < server_time < ed and is_open:
            result['cur'].append(get_ac_dict(ac.id, sd, ed))
        else:
            sdate = time.mktime(ac.sdate.timetuple())
            edate = time.mktime(ac.edate.timetuple())
            result['nor'].append(get_ac_dict(ac.id, sdate, edate))
    return result


@Route()
def activity_manage(request, template="game/activity_manage.html"):
    server_ids = request.REQUEST.getlist('server_id')
    server_ids = list(set(server_ids)) if server_ids else []
    server_ids = [int(i) for i in server_ids]
    activity_type = request.REQUEST.get('activity_type', u'7天乐活动')
    query_type = request.REQUEST.get('query_type', None)
    query_type_dict = {
        u'status': u'按活动状态分类',
        u'id': u'按活动ID分类',
        u'type': u'查看当前活动（单服）',
        u'temp': u'查看当前模版活动'
    }

    table_head = []
    results = {}
    server = None

    for server_id in server_ids:
        try:
            server = Server.objects.filter(id=server_id).first()
            gmp = GMProtocol(server_id)
            server_time = gmp.query_server_time()[0]
            results[server] = get_activity_status(activity_type, server, server_time, query_type)
        except Exception:
            err_msg = trace_msg()
    activity_data = {}
    if query_type == 'status':
        table_head = ['活动ID', '开始时间', '结束时间', '活动状态', '服务器']
        for server, result in results.iteritems():
            cur = result.get('cur')
            nor = result.get('nor')
            for i in cur:
                activity_data.setdefault(i, {}).setdefault(u'正在进行', []).append(server)
            for i in nor:
                activity_data.setdefault(i, {}).setdefault(u'尚未开启', []).append(server)

    elif query_type == 'id':
        table_head = ['活动ID', '开始时间', '结束时间', '服务器']
        for server, result in results.iteritems():
            results[server] = []
            results[server].extend(result['cur'])
            results[server].extend(result['nor'])
        for server, ids in sorted(results.iteritems()):
            for i in ids:
                activity_data.setdefault(i, []).append(server)

    elif query_type == 'temp':
        table_head = ['活动类型', '显示开始', '活动开始', '活动结束', '显示结束']
        res = gmp.get_temp_activity()
        res_obj = {}
        res_obj[res[0]] = res[1:5]
        res_obj[res[6]] = res[7:11]
        res_obj[res[12]] = res[13:17]
        res_obj[res[18]] = res[19:23]

    else:
        table_head = ['活动类型', '活动ID']
        if server and results:
            cur = results[server].get('cur')
            for i in cur:
                ac_type = Activity.objects.filter(id=i['aid']).first().type
                if ac_type not in activity_data:
                    activity_data[ac_type] = []
                activity_data[ac_type].append(i)

    model = get_activity_model(request)
    select_server_ids = server_ids
    group_servers_dict = get_group_servers_dict(request)
    return render_to_response(template, locals())


@Route()
@notauth
def save_activity_msg(request):
    '''本地保存准备开启的活动信息和关联公告
排行榜 ：开服第二天00:00至第五天23:59分关闭（共4天）
累计充值：跟着开服时间开启至第五天23:59分关闭（开5天）
累计消费：跟着开服时间开启至第五天23:59分关闭（开5天）
每日单笔充值：跟着开服时间开启至第7天晚上23:59分关闭（开7天）
    '''
    res = 'fail'
    on = int(request.REQUEST.get('on', '0'))
    sid = int(request.REQUEST.get('sid', '0'))
    msg_path = os.path.join(ACTIVITY_PATH, 'msg')
    # 创建msg目录
    try:
        if not os.path.isdir(msg_path):
            os.makedirs(msg_path)
    except Exception, e:
        return HttpResponse("目录错误")
    # 创建sid目录并生成文件
    try:
        if on > 0 and sid:
            sid = str(sid)
            server = Server.objects.filter(id=sid)
            if len(server) > 0:
                sct = server[0].create_time

                activity_obj_list = Activity.objects.filter(is_temp=1)
                if len(activity_obj_list) > 0:
                    #######创建sid目录#######
                    sid_path = os.path.join(msg_path, sid)
                    if not os.path.isdir(sid_path):
                        os.makedirs(sid_path)
                    ########################
                    ########修改模版活动#########
                    for act in activity_obj_list:
                        msg = act.msg
                        file_name = ''
                        msg_dict = json.loads(msg)
                        if msg_dict:
                            type = act.type
                            if type == '排行榜':
                                key = msg_dict['key']
                                file_name = 'rank_activity_%s.json' % key
                                st = date_to_ts(
                                    datetime.datetime.replace(sct + datetime.timedelta(days=1), hour=0, minute=0,
                                                              second=0))
                                et = date_to_ts(
                                    datetime.datetime.replace(sct + datetime.timedelta(days=4), hour=23, minute=59,
                                                              second=59))
                                msg_dict['time'][0] = st - 1
                                msg_dict['time'][1] = st
                                msg_dict['time'][2] = et
                                msg_dict['time'][3] = et + 1

                            if type == '累计充值':
                                file_name = 'money_activity_0.json'
                                st = date_to_ts(sct)
                                et = date_to_ts(
                                    datetime.datetime.replace(sct + datetime.timedelta(days=4), hour=23, minute=59,
                                                              second=59))
                                msg_dict['ab'] = st
                                msg_dict['ae'] = et
                                msg_dict['sb'] = st - 1
                                msg_dict['se'] = et + 1

                            if type == '累计消费':
                                file_name = 'money_activity_1.json'
                                st = date_to_ts(sct)
                                et = date_to_ts(
                                    datetime.datetime.replace(sct + datetime.timedelta(days=4), hour=23, minute=59,
                                                              second=59))
                                msg_dict['ab'] = st
                                msg_dict['ae'] = et
                                msg_dict['sb'] = st - 1
                                msg_dict['se'] = et + 1

                            if type == '每日单笔充值':
                                file_name = 'daily_inpour.json'
                                st = date_to_ts(sct)
                                et = date_to_ts(
                                    datetime.datetime.replace(sct + datetime.timedelta(days=6), hour=23, minute=59,
                                                              second=59))
                                msg_dict.insert(0, 2)
                                msg_dict[-1] = et
                                msg_dict[-2] = st

                        msg = json.dumps(msg_dict)
                        if file_name and sid_path and msg:
                            filename = '%s/%s' % (sid_path, file_name)
                            filet = open(filename, 'w')
                            filet.write(msg.encode('utf-8'))
                            filet.close()

                            res = '1'
                    #############################
                    os.chdir(msg_path)
                    import zipfile
                    z = zipfile.ZipFile(sid + '.zip', 'w')
                    if os.path.isdir(sid_path):
                        for d in os.listdir(sid_path):
                            z.write(sid + os.sep + d)
                            # close() 是必须调用的！
                        z.close()

                    relate_notice(sid)

                else:
                    res = '没有开服模版活动'

            else:
                res = '没有服务器信息'

        else:
            res = '参数无效'

    except Exception:
        res = trace_msg()

    return HttpResponse(res)


def date_to_ts(date):
    # 转时间戳
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    ts = int(time.mktime(time.strptime(date_str, '%Y-%m-%d %H:%M:%S')))
    return ts


def relate_notice(sid):
    '''关联模版公告
    '''

    if int(sid):
        post_list_server = [sid]
        try:
            notice_list = Notice.objects.filter(is_temp=1)
            for notice in notice_list:
                ###关联####
                notice.server.add(*Server.objects.filter(id__in=post_list_server))
                notice.save()

        except Exception, e:
            print e


@Route()
def operation_activity_edit(request):
    """运营活动编辑页面"""

    # 获取sid
    sid = request.REQUEST.get('sid', '')

    # 参数
    group_servers_dict = groups_servers(request)
    operation_activity = eval(DictDefine.objects.get(id=constant.operation_activity_type_id_dict).json_dict)
    if sid:
        model = OperationActivity.objects.get(sid=sid)
        model.activityId = str(model.activityId)  # 用于模版语法中活动类型判等
        select_server_ids = eval(model.server)  # 用于勾选服务器

    # 返回模版与参数
    return render_to_response('game/operation_activity_edit.html', locals())


@Route()
def operation_activity_save(request):
    """运营活动保存"""

    # 获取参数
    server = request.REQUEST.get('server')
    activityId = request.REQUEST.get('activityId')
    icon = request.REQUEST.get('icon')
    backIcon1 = request.REQUEST.get('backIcon1')
    backIcon2 = request.REQUEST.get('backIcon2')
    titleIcon = request.REQUEST.get('titleIcon')
    shopIcon = request.REQUEST.get('shopIcon')
    enterIcon = request.REQUEST.get('enterIcon')
    name = request.REQUEST.get('name')
    content = request.REQUEST.get('content')
    imageIcon = request.REQUEST.get('imageIcon')
    imageContent = request.REQUEST.get('imageContent')
    imageScore = request.REQUEST.get('imageScore')
    eventActivityRankAwardList = request.REQUEST.get('eventActivityRankAwardList')
    startTime = request.REQUEST.get('startTime')
    endTime = request.REQUEST.get('endTime')
    endRewardTime = request.REQUEST.get('endRewardTime')
    sid = request.REQUEST.get('sid')

    # 根据有没有sid判断是新建还是修改
    if sid:
        model = OperationActivity.objects.get(sid=sid)
    else:
        model = OperationActivity()

    # 保存进数据库
    model.server = server
    model.activityId = activityId
    model.icon = icon
    model.backIcon1 = backIcon1
    model.backIcon2 = backIcon2
    model.titleIcon = titleIcon
    model.shopIcon = shopIcon
    model.enterIcon = enterIcon
    model.name = name
    model.content = content
    model.imageIcon = imageIcon
    model.imageContent = imageContent
    model.imageScore = imageScore
    model.eventActivityRankAwardList = eventActivityRankAwardList
    model.startTime = startTime
    model.endTime = endTime
    model.endRewardTime = endRewardTime
    model.status = 0
    if not sid:
        model.sid = time_util.now_sec()
    model.save()

    # 返回应答
    response = HttpResponse()
    response['ok'] = 'ok'
    return response


@Route()
def operation_activity_audit(request):
    """运营活动审核"""

    # 获取参数
    sid = request.REQUEST.get('sid')

    # 获取对应运营活动模型类
    model = OperationActivity.objects.get(sid=sid)

    # 判断是否已经审核
    if model.status == 1:
        return HttpResponse(u'SID为%s的活动已审核！' % sid)

    # 获取原本activity.json文件，如果存在，则遍历一遍并根据领取结束时间删除已过期的活动
    path = os.path.abspath(os.path.join(os.path.abspath(os.path.join(STATIC_PATH, 'server')), 'activity.json'))
    try:
        with open(path, 'r') as f:
            old_activity_list = eval(f.read())
    except IOError:
        old_activity_list = list()
    else:
        for activity in old_activity_list[:]:
            if time_util.now_sec() > activity['endRewardTime']:
                old_activity_list.remove(activity)

    # 构造activity.json文件
    award_list = model.eventActivityRankAwardList.split('\n')
    activity_award_list = list()
    for award in award_list:
        award_config_list = award.split('|')
        award_config_dict = dict()
        award_config_dict['startRank'] = int(award_config_list[0])
        award_config_dict['endRank'] = int(award_config_list[1])
        award_config_dict['rewardId'] = int(award_config_list[2])
        activity_award_list.append(award_config_dict)
    new_activity_dict = dict()
    new_activity_dict['eventActivityRankAwardList'] = activity_award_list
    new_activity_dict['imageIcon'] = model.imageIcon.split('|')
    new_activity_dict['imageContent'] = model.imageContent.split('|')
    new_activity_dict['imageScore'] = map(int, model.imageScore.split('|'))
    new_activity_dict['server'] = eval(model.server)
    new_activity_dict['activityId'] = model.activityId
    new_activity_dict['icon'] = model.icon
    new_activity_dict['backIcon1'] = model.backIcon1
    new_activity_dict['backIcon2'] = model.backIcon2
    new_activity_dict['titleIcon'] = model.titleIcon
    new_activity_dict['shopIcon'] = model.shopIcon
    new_activity_dict['enterIcon'] = model.enterIcon
    new_activity_dict['name'] = model.name
    new_activity_dict['content'] = model.content
    new_activity_dict['startTime'] = time_util.formatTimestamp(str(model.startTime))
    new_activity_dict['endTime'] = time_util.formatTimestamp(str(model.endTime))
    new_activity_dict['endRewardTime'] = time_util.formatTimestamp(str(model.endRewardTime))
    new_activity_dict['sid'] = int(sid)
    old_activity_list.append(new_activity_dict)
    old_activity_list = json.dumps(old_activity_list)
    with open(path, 'w') as f:
        f.write(old_activity_list)

    # 告诉服务端活动变更
    for server in eval(model.server):
        gmp = GMProtocol(server)
        result = gmp.tell_activity_json()
        if result[0] != 0:
            return HttpResponse(u'与服务端协议通讯失败！')

    # 修改活动状态，并添加审核人
    model.status = 1
    model.auditor = request.admin.id
    model.save()

    # 返回应答
    return HttpResponse(u'SID为%s的活动审核成功！' % sid)


@Route()
def operation_activity_copy(request):
    """运营活动复制"""

    # 获取参数
    sid = request.REQUEST.get('sid')

    # 获取对应模型
    model = OperationActivity.objects.get(sid=sid)

    # 参数
    model.sid = ''  # 由于模版会根据sid判断是否新建，因此需要先把sid清空
    model.status = 0  # 由于模版会根据状态判断有没有保存按钮，因此需要先把状态设为未审核
    model.activityId = str(model.activityId)  # 用于模版语法中活动类型判等
    select_server_ids = eval(model.server)  # 用于勾选服务器
    group_servers_dict = groups_servers(request)
    operation_activity = eval(DictDefine.objects.get(id=constant.operation_activity_type_id_dict).json_dict)

    # 返回模版与参数
    return render_to_response('game/operation_activity_edit.html', locals())
