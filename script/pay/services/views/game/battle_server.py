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
from views.base import getConn,json_response,notauth
from django.http import HttpResponse
from util.http import http_post
from views.base import GlobalPathCfg
import json, datetime ,time
from util import trace_msg
from urls.AutoUrl import Route
from views.widgets import get_group_servers_dict,get_agent_channels_dict
from .base import GMProtocol,GM_battleProtocol
from .game_def import BATTLE_PARAM_MAP
from util.threadpoll import ThreadPool
from models.game import Activity


@Route()
def battle_server_time(request,template='game/battle_server_time.html'):
    server_id = int(request.REQUEST.get('server_id','') or 0)
    server_time = diff_time = 0
    if server_id :
        gmp = GM_battleProtocol(server_id)
        result = gmp.battle_info()
        server_time = result[3]
        diff_time = result[4]
        jieshu = result[1]
        state = result[2]

        if request.method == 'POST':
            modify_time = request.REQUEST.get('modify_time','')
            server_time_str = request.REQUEST.get('server_time_str','')
            on_off = request.REQUEST.get('on_off','')
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
                if on_off == 'true':
                    on_off = True
                    gmp.battle_button(on_off)
                elif on_off == 'false':
                    on_off = False
                    gmp.battle_button(on_off)
                else:
                    pass

                if add_sec >= 6* 86400:
                    err_msg = '腿毛说 增加时间不能大于 6天!'
                else:
                    server_time,diff_time = gmp.add_battle_server_time(add_sec)
                    info_msg = '成功!' if server_time else '失败!'
        else:
            server_time = result[3]
            diff_time = result[4]
        real_time = server_time - diff_time
        add_day = diff_time / 86400
        add_hour = (diff_time % 86400 ) / 3600
        add_minute = ((diff_time % 86400 ) % 3600 ) / 60
        add_second = ((diff_time % 86400 ) % 3600 ) % 60

    return render_to_response(template, locals())

@Route()
def battle_parameter(request, server_id=0):
    server_id = int(request.REQUEST.get('server_id','') or 0)
    if server_id:
        try:
            gmp = GM_battleProtocol(server_id)
            gmp.time_out = 10
#            server_params = gmp.get_server_param()
        except:
            err_msg = '%s' % trace_msg()
    default_params = json.dumps(BATTLE_PARAM_MAP,ensure_ascii=True)
#    group_servers_dict = get_group_servers_dict(request)
    return render_to_response('game/battle_parameter.html', locals())

@Route()
def battle_ID_map(request):
    server_id = int(request.REQUEST.get('server_id','') or 0)
    if server_id:
        try:
            gmp = GM_battleProtocol(server_id)

            if request.method == 'POST':
                msg = request.REQUEST.get('msg','')
                result = gmp.battle_serverId_map(msg)

        except:
            err_msg = '%s' % trace_msg()

    return render_to_response('game/battle_map.html', locals())

@Route()
@notauth
def ranking(request):
    activity_id = int(request.REQUEST.get('activity_id','') or 0)
    tp = request.REQUEST.get('tp','')
    mn = request.REQUEST.get('mn','')
    rc = request.REQUEST.get('rc','') or 0
    if activity_id:
        model =  Activity.objects.prefetch_related('server').get(id=activity_id)
        if model.id and model.msg:
            select_server_ids = [ s.id for s in model.server.all() ]
            sid = [int(sid) for sid in select_server_ids]
            dict = json.loads(model.msg)
            sdate = dict['st']
            sdate = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(sdate))
            edate = dict['et']
            edate = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(edate))
        try:
            if int(tp) == 1:
                sql = '''select p.server_id,s.name,pay_user,sum(post_amount) pay_amount,sum(pay_gold) pay_gold,GROUP_CONCAT(distinct(IFNULL(player_name,''))) \
                from pay_action p LEFT JOIN servers s ON p.server_id=s.id where p.server_id in %s and p.post_time between '%s' and '%s' \
                group by pay_user order by pay_amount desc limit 0,%s''' %(sid,sdate,edate,mn)
                sql = sql.replace('[','(').replace(']',')')
                cursor = connection.cursor()
                rows = cursor.execute(sql)
                fetchall = cursor.fetchall()
                lis = []

                for i in range(int(rows)):
                    if int(fetchall[i][4]) < int(rc):
                        continue

                    dic = {}
                    dic['sid'] = int(fetchall[i][0])
                    dic['sn'] = fetchall[i][1]
                    dic['pi'] = int(fetchall[i][2])
                    dic['na'] = fetchall[i][5].replace(',','')
                    dic['am'] = int(fetchall[i][4])
                    lis.append(dic)

                return HttpResponse(json.dumps(lis))

            else:
                return HttpResponse(json.dumps('跨服充值tp=1'))

        except:
            err_msg = '%s' % trace_msg()

    return HttpResponse(json.dumps(err_msg))

