# -*- coding: utf-8 -*-
#
#游戏服务器相关
#
#django 常用导入
#=========================================
from django.core.urlresolvers import reverse
from django.db import connection,connections
from django.db.models import Q
from django.utils.html import conditional_escape
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
from django.template import loader, RequestContext
#==========================================

from util import trace_msg,datetime_to_timestamp
from models.log import Log
from views.game.base import  write_gm_log
from models.server import Server, Group
from cache import center_cache
from views.base import getConn,json_response
from django.http import HttpResponse
from util.http import http_post
from views.base import GlobalPathCfg
import json, datetime
from util import trace_msg
from urls.AutoUrl import Route
from views.widgets import get_group_servers_dict,get_agent_channels_dict
from .base import GMProtocol,GM_battleProtocol
from .game_def import SERVER_PARAM_MAP
from util.threadpoll import ThreadPool
from models.game import Activity
from views.base import notauth
from settings import TEMPLATE_DIRS, MEDIA_ROOT, STATIC_ROOT

@Route()
def server_info(request, server_id=0):
    server_id = int(request.REQUEST.get('server_id','') or 0)
    if server_id:
        try:
            gmp = GMProtocol(server_id)
            gmp.time_out = 10
            server_params = gmp.get_server_param()
        except:
            err_msg = '%s' % trace_msg()
    default_params = json.dumps(SERVER_PARAM_MAP,ensure_ascii=True)
    group_servers_dict = get_group_servers_dict(request)
    return render_to_response('game/server_info.html', locals())


def server_modify_action(request,server_id,msg,remark):
    try:
        gmp = GMProtocol(server_id)
        result = gmp.modify_server_param(msg)
        if result == 0:
            gmp.save_log(request.admin.id, gmp.req_type, result,remark1=remark)
        err_msg = gmp.rsp_map.get(result)
    except Exception,e:
        err_msg = trace_msg()
        print err_msg
    return '%s:%s' % (server_id,err_msg)

def activity_params_handle(modify_param):
    activity_params = []
    for k,v in modify_param.iteritems():
        if isinstance(k,int):
            activity_params.append([k,v])

def input_server_param_handle(modify_param):
    remark = ''
    new_modify_param = []
    activity_params = []
    for k,v in modify_param.iteritems():
        if str(k).isdigit():
            k = int(k)
        param_config = SERVER_PARAM_MAP.get(k,None)
        if param_config and v:
            remark += '%s:%s\n' % (param_config.get('name',k),v)
    activity_params = activity_params_handle(modify_param)
    return modify_param,remark


@Route()
def server_modify(request, server_id=0):
    '''修改服务器参数
    '''
    server_ids = list(set(request.REQUEST.getlist('server_id')))
    modify_param = request.REQUEST.get('msg','')
    remark = ''
    try:
        if server_ids:
            modify_param = json.loads(modify_param)

            msg,remark = input_server_param_handle(modify_param)
            print msg
            servers_len = len(server_ids)
            if servers_len>1:
                poll_num = 100 if servers_len>100 else servers_len
                tp = ThreadPool(poll_num)
                for server_id in server_ids:
                    tp.append(server_modify_action,(request,server_id,msg,remark))
                tp.close()
                result = tp.get_all_result()
                tp.join()
                del tp
            else:
                server_id = server_ids[0]
                result = [server_modify_action(request,server_id,msg,remark) ]
            return HttpResponse('<br>'.join(result))
    except:
        err_msg = trace_msg()
    return HttpResponse(err_msg)



@Route()
def roll_broadcast(request,template='game/roll_broadcast.html'):
    '''滚动公告
    '''
    server_id = int(request.REQUEST.get('server_id','') or 0)
    group_servers_dict = get_group_servers_dict(request)
    select_server_ids = [server_id]
    try:
        if server_id:
            gmp = GMProtocol(server_id)
            #server_time = gmp.query_server_time()[0]

            if request.method == 'POST':
                json_msg = request.REQUEST.get('msg','')
                msg = json.loads(json_msg)

                _r = {"code":-1,"msg":""}
                if request.REQUEST.get('req_type','') == 'roll_broadcast_del':
                    result = gmp.roll_broadcast_del(msg)
                else:
                    msg[0]["bc"] = msg[0]["bc"].replace("<br />","")
                    result = gmp.roll_broadcast_set(msg)
                _r['code'] = result
                _r['msg'] = gmp.rsp_map.get(result,result)
                gmp.save_log(request.admin.id, gmp.req_type, _r['code'],remark1='remark',remark2=json_msg)
                return HttpResponse(json.dumps(_r))
            else:
                roll_broadcasts = gmp.roll_broadcast_query()
                server_model = Server.objects.get(id=server_id)
        else:
            the_user = request.admin
            server_list = the_user.get_resource("server").all()
            # 返回所有正在滚动的公告
            roll_broadcasts = []
            # for g,servers in group_servers_dict.items():
            #     for s in servers:
            for s in server_list:
                gmp =GMProtocol(s.id)
                result = gmp.roll_broadcast_query()
                if result:
                    for i in range(len(result)):
                        result[i]['serverId'] = s.id
                        result[i]['serverName'] = s.name
                    roll_broadcasts.extend(result)


            # gmp = GMProtocol(7)
            # roll_broadcasts = gmp.roll_broadcast_query()
            # print roll_broadcasts
            # if roll_broadcasts:
            #     roll_broadcasts[0]['serverId'] = 7
            #     roll_broadcasts[0]['serverName'] = 'test'
            # server_model = Server.objects.get(id=7)
    except:
        err_msg = trace_msg()
    return render_to_response(template, locals())

@Route()
def server_time(request,template='game/server_time.html'):
    server_id = int(request.REQUEST.get('server_id','') or 0)
    server_time = diff_time = 0
    if server_id :
        gmp = GMProtocol(server_id)
        result = gmp.query_server_time()
        server_time = result[0]
        diff_time = result[2]

        if request.method == 'POST':
            modify_time = request.REQUEST.get('modify_time','')
            server_time_str = request.REQUEST.get('server_time_str','')
            if server_time_str and modify_time:
                modify_timestamp = datetime_to_timestamp(modify_time)
                server_timestamp = datetime_to_timestamp(server_time_str)
                add_sec = modify_timestamp - server_timestamp
                add_sec = 0 if add_sec < 0 else add_sec
#            day = int(request.REQUEST.get('day','') or 0)
#            hour = int(request.REQUEST.get('hour','') or 0)
#            minute = int(request.REQUEST.get('minute','') or 0)
#            sec = int(request.REQUEST.get('sec','') or 0)
#            add_sec = day * 86400 + hour * 3600 + minute * 60 + sec
                if add_sec >= 10* 86400:
                    err_msg = '嘿嘿嘿 增加时间不能大于 10天!'
                else:
                    result = gmp.add_server_time(add_sec)
#                    server_time = result[0]
#                    diff_time = result[2]
                    info_msg = '成功!' if server_time else '失败!'
        else:
            server_time = result[0]
            diff_time = result[2]
        real_time = server_time - diff_time
        add_day = diff_time / 86400
        add_hour = (diff_time % 86400 ) / 3600
        add_minute = ((diff_time % 86400 ) % 3600 ) / 60
        add_second = ((diff_time % 86400 ) % 3600 ) % 60

    return render_to_response(template, locals())


@Route()
def battle_server_time(request,template='game/battle_server_time.html'):
    server_id = int(request.REQUEST.get('server_id','') or 0)
    server_time = diff_time = 0
    if server_id :
        group_servers_dict = get_group_servers_dict(request)
        gmp = GM_battleProtocol(server_id)
        result = gmp.query_battle_server_time()
        server_time = result[0]
        diff_time = result[2]

        if request.method == 'POST':
            modify_time = request.REQUEST.get('modify_time','')
            server_time_str = request.REQUEST.get('server_time_str','')
            if server_time_str and modify_time:
                modify_timestamp = datetime_to_timestamp(modify_time)
                server_timestamp = datetime_to_timestamp(server_time_str)
                add_sec = modify_timestamp - server_timestamp
                add_sec = 0 if add_sec < 0 else add_sec
#            day = int(request.REQUEST.get('day','') or 0)
#            hour = int(request.REQUEST.get('hour','') or 0)
#            minute = int(request.REQUEST.get('minute','') or 0)
#            sec = int(request.REQUEST.get('sec','') or 0)
#            add_sec = day * 86400 + hour * 3600 + minute * 60 + sec
                if add_sec >= 10* 86400:
                    err_msg = '嘿嘿嘿 增加时间不能大于 10天!'
                else:
                    result = gmp.add_battle_server_time(add_sec)
#                    server_time = result[0]
#                    diff_time = result[2]
                    info_msg = '成功!' if server_time else '失败!'

            kid = request.REQUEST.get('kid','')
            sids = request.REQUEST.get('sids','')
            if sids:
                sids = json.loads(sids)

            if kid and len(sids) > 0:

                _r = {'success':[],'failed':[]}
                for s in sids:
                    try:
                        gmp = GMProtocol(s)
                        stime_res = gmp.query_server_time()
                        sid_time = stime_res[0]
                        dif_time = server_time - sid_time
                        result = -1
                        while 1:
                            if dif_time >= 10* 86400:
                                _dif_time = 10* 86300
                                try:
                                    result = gmp.add_server_time(_dif_time)
                                except:
                                    break
                                dif_time = dif_time - _dif_time
                            else:
                                result = gmp.add_server_time(dif_time)
                                break

                        if result==0:
                            _r['success'].append(s)
                        else:
                            _r['failed'].append(s)

                    except Exception,e:
                        print trace_msg()
                        _r['failed'].append(s)
                        pass

                return HttpResponse(json.dumps(_r))
        else:
            server_time = result[0]
            diff_time = result[2]
        real_time = server_time - diff_time
        add_day = diff_time / 86400
        add_hour = (diff_time % 86400 ) / 3600
        add_minute = ((diff_time % 86400 ) % 3600 ) / 60
        add_second = ((diff_time % 86400 ) % 3600 ) % 60

    return render_to_response(template, locals())



import os,time
from util import str_to_datetime,datetime_to_str,timestamp_to_datetime_str,datetime_to_timestamp
def server_active_cfg_list(request):
    _now = int(time.time())
    g = lambda x,y:request.GET.get(x, request.POST.get(x, y))
    status = int(g('status','1'))
    sdate = g('sdate','')
    edate = g('edate','')
    page_num = int(g('page_num', '1'))

    _result_list = load_active_task_data()

    if sdate and edate:
        _sd = datetime_to_timestamp(sdate)
        _ed = datetime_to_timestamp(edate)
    else:
        sdate = edate = timestamp_to_datetime_str(_now)
        _sd = _ed = 0

    result_list = []
    for item in _result_list:
            _ststamp = datetime_to_timestamp(item['sdate'])
            _etstamp = datetime_to_timestamp(item['edate'])

            if _sd and _ed:#时间搜索
                _is_append = (_ed> _ststamp > _sd)
            else:
                if status == 1:#活动中
                    _is_append =  _now < _etstamp
                elif status == 2:#过期
                    _is_append = _now > _etstamp
                else:
                    _is_append = True
            if _is_append:
                result_list.append(item)

    page_size = int(g('page_size','20'))
    total_record = len(result_list)
    sp = (page_num - 1 ) * page_size
    result_list = result_list[sp:sp+page_size]

    list_len = result_list.__len__()
    param_dict = {}
    for p in get_server_param():
        param_dict[p[0]] = p[1]
    i = 0
    while list_len > i:
        k = 1 + i
        item1 = result_list[i]
        while list_len > (k):
            item2 = result_list[k]
            sdate1 = datetime.datetime.strptime(item1['sdate'], '%Y-%m-%d %H:%M:%S')
            info1 = item1['server_info']
            edate1 = datetime.datetime.strptime(item1['edate'], '%Y-%m-%d %H:%M:%S')
            rev_info1 = item1['recover_server_info']

            sdate2 = datetime.datetime.strptime(item2['sdate'], '%Y-%m-%d %H:%M:%S')
            info2 = item2['server_info']
            edate2 = datetime.datetime.strptime(item2['edate'], '%Y-%m-%d %H:%M:%S')
            rev_info2 = item2['recover_server_info']

            error_dict = {}
            def set_msg(p1, p2):
                for key1 in p1:
                    value1 = p1.get(key1)
                    value2 = p2.get(key1, None)

                    if None != p2.get(key1, None) and value1 != value2:
                        d = error_dict.get(i, {})
                        if None == d.get(key1, None):
                            msg_list = item1.get('msg_list', [])
                            msg = '%s(%s)' % (item2['title'].encode('utf-8'), param_dict.get(key1, ''))
                            msg_list.append(msg)
                            item1['msg_list'] = msg_list
                            d[key1] = 1
                        error_dict[i] = d
            s1 = set([int(server_id) for server_id in item1["server_list"]])
            s2 = set([int(server_id) for server_id in item2["server_list"]])

            if (datetime.datetime.now() - edate1).days < 2 and (s1 & s2).__len__() != 0:
                if abs((sdate1 - sdate2).days) <= 1:
                    set_msg(info1, info2)

                if abs((sdate1 - edate2).days) <= 1:
                    set_msg(info1, rev_info2)

                if abs((edate1 - edate2).days) <= 1:
                    set_msg(rev_info1, rev_info2)

                if abs((edate1 - sdate2).days) <= 1:
                    set_msg(rev_info1, info2)

            k += 1

        i += 1

    return render_to_response('game/cfg_server_active_list.html', locals())
    #return render_to_response('game/cfg_server_active_list.html', {"result_list":result_list})

def edit_server_active_cfg(request):
    group_server_dict = center_cache.get_master_server_dict_group_by()
    g = request.GET.get
    item_id = g('id', '')
    list_infos = []
    server_info = {}
    recover_server_info = {}
    sdate=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    edate=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    title = ''
    selected_server = []
    if item_id != '':
        item_id = int(item_id)
        result_list = load_active_task_data()
        item = result_list[item_id]
        server_info = item['server_info']
        recover_server_info = item['recover_server_info']
        sdate = item['sdate']
        edate = item['edate']
        title = item['title']
        selected_server = item['server_list']
    def_params = get_server_param()

    for item in def_params:
        allow_modify = int(item[2])
        if allow_modify <= 0:
            continue
        remark = negative = ''
        if 5 <= item.__len__():
            if item[4]:
                negative = '-'
        remark = item[3]
        list_infos.append({'name':item[1], 'key':item[0], 'value':server_info.get(item[0], negative),
                           'is_modify':item[2], 'remark':remark, 'recover_value':recover_server_info.get(item[0],''),
                            })

    return render_to_response('game/cfg_server_active_info.html', {"list_infos":list_infos, "group_server_dict":group_server_dict, 'sdate':sdate, 'edate': edate, 'item_id':item_id, 'title':title, 'selected_server':selected_server})

def save_server_active_cfg(request):
    code = 0
    msg = ''
    title = "没有标题"
    g = lambda x,y='':request.POST.get(x, request.GET.get(x,y))
    gl = lambda x,y=[]:request.POST.getlist(x, request.GET.getlist(x, y))
    def_params = get_server_param()
    setting_param = {}
    recover_param = {}
    for item in def_params:
        allow_modify = int(item[2])
        if allow_modify <= 0:
            continue
        param_name = item[0]
        recover_param_name = 'recover_%s' % item[0]
        recover_value = g(recover_param_name, '')
        value = g(param_name, '')

        v1 = recover_value.lower()
        v2 = value.lower()
        if v1 == 'true':
            recover_value = True
        elif v1 == 'false':
            recover_value = False
        if v2.lower() == 'true':
            value = True
        elif v2 == 'false':
            value = False

        recover_value = recover_value.strip() if isinstance(recover_value,basestring) else recover_value
        value = value.strip() if isinstance(value,basestring) else value
        if recover_value == '' or value == '' or recover_value == '-':
            continue
        if value != '-' and value:
            setting_param[param_name] = value
        if recover_value != '-' and recover_value:
            recover_param[param_name] = recover_value

    setting_param_len = setting_param.__len__()
    recover_param_len = recover_param.__len__()
    #print setting_param_len, recover_param_len
    msg = '保存成功!'
    for item in range(1):
        if setting_param_len  + recover_param_len <= 0 or setting_param_len != recover_param_len :
            msg = '请设置修改项'
            code = 1
            break
        if g('title', '') != '':
            title = g('title')
        server_list = gl('server_list', [])

        sdate = g('sdate', '')
        edate = g('edate', '')
        try:
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S')
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d %H:%M:%S')
        except Exception, ex:
            print ex
            sdate = ''
            edate = ''

        if server_list.__len__() == 0:
            msg = '没有选择服务器'
            code = 1
            break

        if sdate == '' or edate == '':
            msg = '时间格式错误'
            code = 1
            break

        data_list = load_active_task_data()
        item_id = g('item_id', '')
        if '' != item_id:
            item_id = int(item_id)

        save_item = {"title":title, "server_list":server_list, "sdate":sdate.strftime('%Y-%m-%d %H:%M:%S'), "edate":edate.strftime('%Y-%m-%d %H:%M:%S'), "server_info":setting_param, "recover_server_info":recover_param}
        if data_list.__len__ > item_id and item_id != '':
            data_list[item_id] = save_item
        else:
            data_list.append(save_item)

        if not save_active_task_data(data_list):
            code = 1
            msg = '保存失败请再尝试!'
    return HttpResponse(msg)
    #return HttpResponse('{"msg":"%s", "code":%d}' % (msg, code))

def delete_server_active_cfg(request):
    msg = ''
    code = 0

    g = lambda x,y='':request.POST.get(x, request.GET.get(x,y))
    gl = lambda x,y='':request.POST.getlist(x, request.GET.getlist(x,y))
    item_id_list = gl('id',[])
    data_list = load_active_task_data()
    new_list = []
    print item_id_list
    for i,item in enumerate(data_list):
        if unicode(i) in item_id_list:
            continue
        new_list.append(item)
    if not save_active_task_data(new_list):
        msg = '删除失败，稍候再试'
        code = 1
    return render_to_response('feedback.html')
    #return HttpResponse('{"msg":"%s", "code":%d}' % (msg, code))


def load_active_task_data():
    result_list = []
    cfg = GlobalPathCfg()
    cfg_json_path = cfg.get_server_active_cfg_save_path()
    if os.path.exists(cfg_json_path):
        fp = None
        try:
            fp = open(cfg_json_path)
            json_str = fp.read()
            result_list = json.loads(json_str)
            for i,item in enumerate(result_list):
                item['index'] = i
        except Exception, ex:
            print 'active_task_list load file error:', ex
            print ex
        finally:
            if None != fp:
                fp.close()
    return result_list

def save_active_task_data(data_list):
    cfg = GlobalPathCfg()
    cfg_json_path = cfg.get_server_active_cfg_save_path()
    fp = None
    try:
        fp = open(cfg_json_path, 'w')
        fp.write(json.dumps(data_list))
    except Exception ,ex:
        print 'active task save cfg error:', ex
        return False
    finally:
        if None != fp:
            fp.close()

    return True

def setting_task(server, net_id, trigger_time, recover_time, recover_data, setting_data):
    server_id = server.id
    title = u"服务器ID%s活动设置" % server.name
    #过滤是否已经设置过
    q = Q(title=title) & Q(trigger_date=trigger_time) & Q(end_date=recover_time)
    task = TaskDefine()
    list_data = TaskDefine.objects.filter(q)
    if 0 < list_data.__len__():
        task = list_data[0]

    setting_param = {"req_type":606, "server_id":server_id, "net_id":net_id, "config_type":0, "json_param":{"config_json":setting_data}}
    recover_param = {"req_type":606, "server_id":server_id, "net_id":net_id, "config_type":0, "json_param":{"config_json":recover_data}}

    task.title = title
    task.type = u"服务器参数设置"
    task.state = 0
    task.request_url = game_server_url.GM_SERVER_URL
    task.source_cfg = json.dumps(recover_param)
    task.target_cfg = json.dumps(setting_param)
    task.trigger_date = trigger_time
    task.end_date = recover_time
    task.interval = 0
    task.result_msg = '{"content": [0], "code": 0}'
    task.remark = ''
    task.counter = 0
    task.save()


@Route()
@notauth
def get_7daysact(request):
    '''7天乐活动msg
    '''
    kid = int(request.GET.get('kid','0') or 0)
    result = 'activity is not fand!'
    obj_list = Activity.objects.filter(type='7天乐活动')
    try:
        for model in obj_list:
            msg = json.loads(model.msg)
            if msg:
                if kid and kid == msg['kid']:
                    result = msg
                    for al in result['al']:
                        for tl in al:
                            for rw in tl['tl']:
                                for i in range(len(rw['rw'])):
                                    rw['rw'][i] = d2l(rw['rw'][i])

                    for tl in result['tl']:
                        for i in range(len(tl['rw'])):
                            tl['rw'][i] = d2l(tl['rw'][i])

                    if result['ar']['ty'] == 2:
                        rw = result['ar']['rw']
                        for i in range(len(rw)):
                            rw[i] = d2l(rw[i])

    except Exception,e:
        print trace_msg()

    return HttpResponse(json.dumps(result))

def d2l(msg_d):
    msg_l = []
    if len(msg_d) == 2:
        msg_l.append(msg_d['aID'])
        msg_l.append(msg_d['v'])

    else:
        msg_l.append(msg_d['aID'])
        msg_l.append(msg_d['id'])
        msg_l.append(msg_d['v'])

    return msg_l

@Route()
@notauth
def get_festival(request):
    '''节日活动msg
    '''
    kid = int(request.GET.get('kid','0') or 0)
    result = 'activity is not fand!'
    obj_list = Activity.objects.filter(type='节日活动')
    try:
        for model in obj_list:
            msg = json.loads(model.msg)
            if msg:
                if kid and kid == msg['kid']:
                    result = msg


    except Exception,e:
        print trace_msg()

    return HttpResponse(json.dumps(result))


@Route()
@notauth
def save_ranging_msg(request):
    '''保存排行榜活动规则信息
    '''
    path = '%s/activity' %STATIC_ROOT

    if not os.path.exists(path):
        os.makedirs(path)

    if request.method == 'POST':
        data = request.POST.get('data', '')
        filename = request.POST.get('filename', '')
        try:
            filename = '%s/%s' %(path,filename)
            filet = open(filename, 'w')
            filet.write(data.encode('utf-8'))
            filet.close()
            return HttpResponse('OK')

        except Exception,e:
            print trace_msg()

    return HttpResponse(json.dumps('fail'))











