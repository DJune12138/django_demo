# -*- coding: utf-8 -*-
#
#游戏军团相关
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
from views.game.base import  write_gm_log
from views.base import getConn, get_server_list, quick_save_log,json_response
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

from .game_def import PLAYER_INFO_MAP,VIP_PRICE,PLAYER_BUILDING_MAP,KEJI_MAP,ARMY_TITLE


@Route()
def army_info(request):
    '''军团信息查询
    '''
    server_id = int(request.REQUEST.get('server_id','') or 0)
    army_name = request.REQUEST.get('army_name','')
    err_msg = ''
    try:
        if server_id and army_name:
            gmp = GMProtocol(server_id)
            result = gmp.query_army_info(army_name)
            if not result:
                err_msg = '没有该军团信息!'
    except:
        err_msg = trace_msg()
    group_servers_dict = get_group_servers_dict(request)
    army_title = ARMY_TITLE
    return render_to_response('game/army_info.html',locals()) 
    
    
@Route()
def query_army_member(request):
    '''军团成员信息
    '''
    server_id = int(request.REQUEST.get('server_id','') or 0)
    army_name = request.REQUEST.get('army_name','')
    member_num = int(request.REQUEST.get('member_num','') or 0)
    err_msg = ''
    _r = {"code":-1,"msg":"","content":[]}
    try:
        if  army_name and server_id and member_num:
            gmp = GMProtocol(server_id)
            result = gmp.query_army_member(army_name,member_num)
            _r['content'] = result
            _r['code'] = 0
    except:
        err_msg = trace_msg()
        _r['msg'] = err_msg
    return HttpResponse(json.dumps(_r))

@Route()
def army_science_modify(request):
    ''' 军团科技修改 '''
    server_id = request.REQUEST.get("server_id", 0)
    msg = request.REQUEST.get("msg", "")

    ret_msg = ""
    ret_code = 1
    try:
        if server_id and msg:
            gmp = GMProtocol(server_id)
            result = gmp.modify_army_science(json.loads(msg))
            ret_msg = gmp.rsp_map.get(result, result)
            gmp.save_log(request.admin.id, gmp.req_type, result)
            ret_code = 0 if result == 0 else 1
    except Exception,e:
        ret_msg = "协议请求错误: %s" % e
    return HttpResponse(json.dumps({"code":ret_code, "msg":ret_msg}))
    
    

@Route()
@json_response
def change_army_name(request):
    '''修改星盟名
    '''
    server_id = request.REQUEST.get("server_id", 0)
    old_name = request.REQUEST.get('old_name','')
    new_name = request.REQUEST.get('new_name','')
    msg = ''
    code = -1
    try:
        if old_name and new_name:
            gmp = GMProtocol(server_id)
            code = gmp.change_army_name(old_name, new_name)
            msg = gmp.rsp_map.get(code,'error!')
    except:
        msg = trace_msg()
        
    return code,msg




