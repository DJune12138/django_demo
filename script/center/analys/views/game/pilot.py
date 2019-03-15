# -*- coding: utf-8 -*-
#
#游戏玩家装备英雄
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

from django.utils.datastructures import SortedDict 
from views.game.base import write_gm_log
from views.base import getConn, get_server_list, quick_save_log
from models.server import Server
from cache import center_cache
from util.http import http_post
from util import str_to_datetime,datetime_to_timestamp,timestamp_to_datetime_str
from views.widgets import get_group_servers_dict,get_agent_channels_dict
import json, time, MySQLdb,traceback
from urls.AutoUrl import Route
import datetime
from util import trace_msg
from .base import GMProtocol

from .game_def import PLAYER_INFO_MAP,VIP_PRICE,PLAYER_BUILDING_MAP,KEJI_MAP

from models.log import DictDefine


@Route()
def pilot_info(request,template = 'game/pilot_info.html'):
    '''武将信息
    '''
    player_id = int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.GET.get('player_name','')
    pilot_id = request.POST.get('pilot_id','')
    gmp = GMProtocol(server_id)
    #pilots_dict = DictDefine.get_dict_for_key('pilots')      #英雄名
    err_msg = ''
    pilots_list = []
    try: 
        gmp.time_out = 10
        pilots_list = gmp.get_pilot_info(player_id)

    except Exception, e:
        err_msg = trace_msg()
    return render_to_response(template, locals())


@Route()
def pilot_modify(request,player_id=0):
    '''武将修改
    '''
    _r = {"code":-1,"msg":""}
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.REQUEST.get('player_name','')
    json_msg = request.REQUEST.get('msg','')
    msg_wj = json.loads(json_msg)

    try:
        if 'wj' in msg_wj:
            wj_list = msg_wj.get('wj','')
            gmp = GMProtocol(server_id)
            result = gmp.set_pilot_modify(player_id,wj_list)

        if 'add_wj' in msg_wj:
            wj_list = msg_wj.get('add_wj','')
            gmp = GMProtocol(server_id)
            result = gmp.add_pilot(player_id,wj_list)

        _r['msg'] = gmp.rsp_map.get(result,result)
        _r['code'] = result
        gmp.save_log(request.admin.id, gmp.req_type, _r['code'],role_name=player_name,remark2=json_msg)
    except:
        err_msg = trace_msg()
        _r['msg'] = err_msg
        
    return HttpResponse(json.dumps(_r))


