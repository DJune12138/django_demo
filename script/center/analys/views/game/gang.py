# -*- coding: utf-8 -*-
#
#部族相关

import copy 
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
from views.game.base import  write_gm_log
from views.base import getConn, get_server_list, quick_save_log
from models.server import Server, ServerPlayer
from cache import center_cache
from util.http import http_post
from util import str_to_datetime,datetime_to_timestamp,timestamp_to_datetime_str,filter_sql

from views.widgets import get_group_servers_dict,get_agent_channels_dict
import json, time, MySQLdb,traceback
from urls.AutoUrl import Route
import datetime,time
from util import trace_msg
from .base import GMProtocol
from models.log import DictDefine
from .game_def import PLAYER_INFO_MAP,VIP_PRICE,PLAYER_BUILDING_MAP,OFFICAL,SJ_MAP
#from models.player import ServerPlayer
from views.base import notauth,json_response
from models.game import Activity,Mail
from models.channel import Channel
from .game_def import Occupation_Map,HEAD_TITLE,TRIBE_TITLE


@Route()
def break_gang(request):
    #解散部族
    gang_id = int(request.REQUEST.get('id',0))
    server_id = request.REQUEST.get('server_id',0)
    err_msg = ''
    if gang_id and server_id:
        gmp = GMProtocol(server_id)
        result = gmp.break_gang(gang_id)
        if result == 0:
            return HttpResponse(json.dumps({"msg":"解散成功！"}))
        else:
            return HttpResponse(json.dumps({"msg":"解散失败！"}))
    else:
        err_msg = '没有部族ID'
    return HttpResponse(json.dumps({"msg":err_msg}))


@Route()
def modify_gang(request):
    #修改部族信息
    server_id = int(request.REQUEST.get('server_id',0))
    gang_id = int(request.REQUEST.get("gang_id",0))
    gang_name = request.REQUEST.get("gang_name","")
    declaration = request.REQUEST.get("declaration","")
    err_msg = ''
    if gang_id == 0:
        return HttpResponse("没有对应部族!")
    if request.method == 'POST':
        gang_name = request.REQUEST.get("gang_name","")
        declaration = request.REQUEST.get("declaration","")    
        msg = [gang_id,gang_name,declaration]
        gmp = GMProtocol(server_id)
        result = gmp.modify_gang(msg)
        if result == 0:
            return render_to_response('feedback.html', locals())
    return render_to_response('player/gang_edit.html',locals())


@Route()
def kick_gang_member(request):
    #踢成员
    server_id = int(request.REQUEST.get('server_id',0))
    player_id = int(request.REQUEST.get('player_id',0))
    err_msg = ''
    if server_id and player_id:
        gmp = GMProtocol(server_id)
        result = gmp.kick_gang_member(player_id)
        if result == 0:
            return HttpResponse(json.dumps({"msg":"踢出成功！"}))
    err_msg = '无玩家ID'
    return render_to_response('player/gang_edit.html',locals())