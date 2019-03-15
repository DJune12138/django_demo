# -*- coding: utf-8 -*-
#
#游戏玩家相关
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
from models.game import Activity


@Route()
def concubine_info(request,player_id=0,template = 'game/concubine_info.html'):
    '''查询后宫信息
    '''
    player_id = int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.GET.get('player_name','')
    err_msg = ''

    try:
        #concubine_map = DictDefine.get_dict_for_key('concubine')
        gmp = GMProtocol(server_id)
        result = gmp.get_concubine_info(player_id)
        title_list = result_list = []
        if result:
            title_list = result[-1]
            result_list = result[0]
            if title_list:
                for i in xrange(len(title_list)):
                    if len(title_list[i]) > 0:
                        title_list[i].append(title_list[i][0]/1000)
                    else:
                        continue
            if result_list:
                for i in xrange(len(result_list)):
                    if len(result_list[i]) > 0:
                        result_list[i].append(result_list[i][0]/1000)
                    else:
                        continue
        book_name = json.dumps(DictDefine.get_dict_for_key('concubine_book'))
        book = gmp.get_concubine_book(player_id)
        book_len = len(book)
        split_num = book_len % 10
        import re
        if split_num > 0:
            book_s1 = book[:-split_num]
            book_s2 = book[-split_num:]
            book_list = re.findall('.{10}', book_s1)
            book_list.append(book_s2)

        else:
            book_list = re.findall('.{10}', book)

        player_info = gmp.get_player_base_info(player_id)
        player_lv = player_info[3]

    except Exception,e:
        err_msg = trace_msg()

    return render_to_response(template, locals())

@Route()
def concubine_modify(request,player_id=0):
    '''修改秀女
    '''
    _r = {"code":-1,"msg":""}
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.REQUEST.get('player_name','')
    json_msg = request.REQUEST.get('msg','')
    try:
        if json_msg:
            msg = json.loads(json_msg)
            gmp = GMProtocol(server_id)

            if 'concubine-add' == request.REQUEST.get('req_type',''):
                iid_list = msg.get('iid_list','')
                num_list = msg.get('num_list','')
                add_l = [list(l) for l in zip(iid_list,num_list)]
                result = gmp.add_concubine(player_id,add_l)

            elif 'concubine-del' == request.REQUEST.get('req_type','') or 'concubine-del_nums' == request.REQUEST.get('req_type',''):
                result = gmp.del_concubine(player_id,msg)

            elif 'concubine-add_nums' == request.REQUEST.get('req_type',''):
                result = gmp.add_concubine(player_id,msg)

            elif 'concubine-modity' == request.REQUEST.get('req_type',''):
                result = gmp.modity_concubine(player_id,msg)

            elif 'book-change' == request.REQUEST.get('req_type',''):
                book_id_dict = DictDefine.get_dict_for_key('concubine_book_id')
                msg['id'] = int(book_id_dict.get(msg['id'],''))
                result = gmp.change_concubine_book(player_id,msg)

            else:
                return HttpResponse(json.dumps(_r))

            _r['msg'] = gmp.rsp_map.get(result,result)
            _r['code'] = result
            gmp.save_log(request.admin.id, gmp.req_type, _r['code'],role_name=player_name,remark2=json_msg)
    except:
        err_msg = trace_msg()
        _r['msg'] = err_msg

    return HttpResponse(json.dumps(_r))

