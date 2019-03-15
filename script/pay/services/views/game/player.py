# -*- coding: utf-8 -*-
#
#游戏玩家相关

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

def get_player_info_param():
    return PLAYER_INFO_MAP

@Route()
def player_list(request):
    '''角色信息排序
    '''
    page_size = 100
    page_num = int(request.REQUEST.get("page_num","1"))
    is_block = int(request.REQUEST.get("block", 0))
    group_id = int(request.REQUEST.get("group_id", 0))
    server_id  = int(request.REQUEST.get("server_id","0"))
    sort_keys = [ x for x in request.REQUEST.get('sort_keys','').split(',') if x] #排序key顺勋
    country_code = int(request.REQUEST.get('nat','-1') or -1)
    total_record = 0
    ths = ["pi","pn","plv","vip","nat","of","pc","olt"]
    _sort_condition = []
    condition_map = SortedDict([(t,PLAYER_INFO_MAP.get(t,{}).get('name','')) for t in ths])
    condition_country = {"nat":country_code} if country_code != -999 else {}
    for k in sort_keys:
        if condition_map.get(k,''):
            _v = request.POST.get(k,'')
            _sort_condition.append((k,int(_v)))

    if server_id:
        try:
            server = Server.objects.get(id=server_id)
            db_name,mongo_conn = server.get_mongo_conn()
            total_record = mongo_conn[db_name].tk.player.find(condition_country).count()
            if page_num < 1 :
                page_num = 1
            offset = (page_num-1) * page_size
            if not _sort_condition:
                _sort_condition = [("olt",-1)] #默认最后登录时间
            _list = mongo_conn[db_name].tk.player.find(condition_country).sort(_sort_condition).skip(offset).limit(page_size)
            player_list = player_list_handle(ths,_list)
            mongo_conn.close()
        except Exception,e:
            traceback.print_exc()
            err_msg = str(e)
    #print country_code
    sort_condition = []
    for c in _sort_condition:
        sort_condition.append( c+(condition_map.get(c[0],''),))

    group_servers_dict = get_group_servers_dict(request)
    player_info_map = PLAYER_INFO_MAP
    country_map_list = sorted(PLAYER_INFO_MAP['nat']['dict'].iteritems(),key=lambda x:x[0])
    return render_to_response('game/player_list.html',locals())

def player_list_handle(ths,player_list):
    '''玩家列表处理
    '''
    _player_list = []
    for p in player_list:
            if  p.get('pc',''):
                p['pc'] = timestamp_to_datetime_str(p['pc'] + time.timezone)
            if  p.get('olt',''):
                p['olt'] = timestamp_to_datetime_str(p['olt'] + time.timezone)
            p['of'] = OFFICAL.get(str(p['of']),p['of'])
#            if  p.get('rg',''):
#                vip_level =  filter(lambda x:p['rg']>x,VIP_PRICE).__len__()
#                p['rg'] = '%s (VIP:%s)' % (p['rg'],vip_level)
            p['nat'] = '%s(%s)'  % (PLAYER_INFO_MAP['nat']['dict'].get(p.get('nat',-1),'没有'),p.get('nat'))
            _player_list.append(p)
    return _player_list


def get_player_account_info(conn,server_id,player_id):
    '''角色帐号信息
    '''
    cur = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
    query_player_sql = 'SELECT * FROM player_%d where player_id=%s limit 1' % (server_id,player_id)
    cur.execute(query_player_sql)
    result = cur.fetchone()
    return result

@Route()
def player_info(request, player_id=0,is_read=0,template = 'game/player_info.html'):
    '''玩家信息
    '''
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.GET.get('player_name','').strip()
    err_msg = ''
    try:
        #gmp = GMProtocol(server_id)
        #conn = gmp.server.mysql_conn()
        server_player = ServerPlayer(player_id)
        account_info = server_player.player_info
        #account_info = get_player_account_info(conn,server_id,player_id)
        #conn.close()
    except Exception, e:
        err_msg = trace_msg()
    return render_to_response(template, locals())

@Route()
def player_modify(request,player_id=0):
    '''修改玩家信息
    '''
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.REQUEST.get('player_name','')
    remark = request.REQUEST.get('remark',"")
    _r = {"code":-1,"msg":""}
    try:
        if remark:
            result = -1
            gmp = GMProtocol(server_id)
            json_msg = request.REQUEST.get('msg','{}')
            msg_jsson = json.loads(json_msg)
            msg_zy = msg_jsson.get('zy','')
            if msg_zy:
                keys = msg_zy.keys()
                msg = [0]*17
                for i in keys:
                    msg[int(i)] = msg_zy[i]
                result = gmp.player_resource_info(player_id,msg)

            msg_pb = msg_jsson.get('pb','')
            if msg_pb:
                player_info = gmp.get_player_base_info(player_id)
                msg = [0]*5
                msg[0] = player_info[1]
                msg[1] = player_info[3]
                msg[2] = player_info[4]
                msg[3] = player_info[5]
#                msg[4] = player_info[9]
                keys = msg_pb.keys()
                for i in keys:
                    msg[int(i)] = msg_pb[i]
                result = gmp.player_base_info(player_id,msg)

            _r['code'] = result
            gmp.save_log(request.admin.id, gmp.req_type, _r['code'],role_name=player_name,remark1=remark,remark2=json_msg)
    except:
        _r['msg'] = trace_msg()
    return HttpResponse(json.dumps(_r))


@Route()
@json_response
def change_player_name(request):
    player_id = int(request.REQUEST.get('player_id','') or 0)
    player_name = request.REQUEST.get('player_name','').strip()
    server_id = player_id >> 20
    code = -1
    msg = ''
    if player_id and player_name and server_id:
        try:
            gmp = GMProtocol(server_id)
            code = gmp.change_role_name(player_id,player_name)
            msg = gmp.rsp_map.get(code)
            if code == 0:
                server_player = ServerPlayer(player_id)
                server_player.update_info('player_name', player_name)
        except:
            msg = trace_msg()

    return code,msg

@Route()
def role_info(request,player_id=0,template = 'game/role_info.html'):
    '''角色信息
    '''
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.GET.get('player_name','')

    
    gmp = GMProtocol(server_id)
    def_params = get_player_info_param()
    err_msg = ''
    #keji_map = KEJI_MAP
    #sj_map = SJ_MAP

    try:
        gmp.time_out = 10
        player_info = gmp.get_player_base_info(player_id)
        player_info = player_info[1] if player_info else []
        resource_list = gmp.get_player_resource(player_id)
        if player_info:
            player_info[2] = Occupation_Map[player_info[2]]
            player_info[5] = HEAD_TITLE[player_info[5]] if player_info[5] else ""
            player_info[6] = TRIBE_TITLE[player_info[6]]
        resource_list = resource_list[1] if resource_list else []

    except Exception, e:
        player_info = resource_list = []
        err_msg = trace_msg()
    return render_to_response(template, locals())


def player_info_handler(player_info):
    '''角色信息处理,转换vip等级..
    '''
    kj_dict = {}
    pb = player_info.get('pb',{})
    if pb:
        pay_gold = pb.get('rg',0)
        vip_level =  filter(lambda x:pay_gold>=x,VIP_PRICE).__len__()
        player_info['pb']['vip_level'] = vip_level
        psc = player_info.get('psc',{}) or {}
        for kj in psc:
            kj_dict[kj['id']] = kj['lv']
        player_info['psc'] = kj_dict
    return player_info



@Route()
def player_kick(request,player_id=0):
    '''踢玩家下线
    '''
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.REQUEST.get('player_name','')
    remark = '踢玩家下线'
    try:
            gmp = GMProtocol(server_id)
            result = gmp.player_kick(player_id)
            err_msg = gmp.rsp_map.get(result,result)
            gmp.save_log(request.admin.id, gmp.req_type, result,role_name=player_name,remark1=remark,remark2=err_msg)

    except:
        err_msg = trace_msg()
    return HttpResponse(err_msg)


def send_msg(request, server_id=0):
    '''发送消息
    '''
    player_id = int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.REQUEST.get('player_name','')
    msg_type = int(request.REQUEST.get('msg_type','') or 0)
    usm = request.admin

    server_list = request.admin.get_resource('server')
    err_msg = ''
    if request.method == 'POST':
        msg_content = request.POST.get('content', '').encode('utf-8')
        remark2 = ''
        user_server_list = [ s.id for s in server_list]
        if not user_server_list.__contains__(server_id):
                return HttpResponse(u'没有权限')
        try:
            if msg_content:
                gmp = GMProtocol(server_id)
                if msg_type == 1 : #全服
                    player_id = 0
                    remark2 = request.REQUEST.get('cause','')
                result = gmp.send_msg(msg_content,player_name)
                err_msg = gmp.rsp_map.get(result,result)
                gmp.save_log(request.admin.id, gmp.req_type, result,role_name=player_name,remark1=msg_content,remark2=remark2)
            else:
                err_msg = '没有填写消息!'
        except:
            err_msg = trace_msg()
        return render_to_response('feedback.html', locals())
    if not player_id:
        group_servers_dict = get_group_servers_dict(request)
    return render_to_response('game/send_msg.html', locals())


@Route()
def player_shutup(request, player_id=0):
    '''玩家解禁言和禁言
    '''
    player_ids = request.REQUEST.getlist('player_id')
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.REQUEST.get('player_name','')
    unshutup = request.REQUEST.get('unshutp','')
    remark = request.REQUEST.get('remark','')
    seconds = int(request.REQUEST.get('seconds','') or 0)
    slientType = request.REQUEST.get('slientType')
    _r = {"code":-1,"msg":''}
    msgs = []
    try:
        gmp = GMProtocol(server_id)
        if player_ids:
            for player_id in player_ids:
                try:
                    player_id = int(player_id)
                    if unshutup:
                        result = gmp.player_unshutup(player_id)
                        remark2 = ''
                    elif seconds and remark and slientType == 'standard':
                        result = gmp.player_shutup(player_id,seconds)
                        remark2 = '禁言(%s)秒' % (seconds)
                    elif seconds and remark and slientType == 'silent':
                        result = gmp.player_shutup_silent(player_id,seconds)
                        remark2 = '静默禁言(%s)秒' % (seconds)
                    gmp.save_log(request.admin.id, gmp.req_type, result,role_name=player_name,remark1=remark,remark2=remark2)
                    #  err_msg = gmp.rsp_map.get(result,result)
                    err_msg = u'失败'
                    if result == 0:
                        err_msg = u'成功'
                except Exception,e:
                    err_msg = str(e)
                msgs.append('%s:%s' % (player_id,err_msg))
            msgs = '\n'.join(msgs)
        elif server_id:
            # 获取禁言列表
            msgs = gmp.player_shutup_list(0)
            return HttpResponse(json.dumps(msgs))   
    except:
        msgs = trace_msg()
    return HttpResponse(msgs)


@Route()
def send_resouces(request, player_id=0):
    '''发送资源
    '''
    player_ids = request.REQUEST.getlist("player_id")
    servdr_id = request.REQUEST.get("server_id")
    subject = request.REQUEST.get('subject','')
    resources_str = request.REQUEST.get("resources", "")
    msg = {"msg":"","ok_list":[],'err_list':[]}
    resources = []
    if isinstance(resources_str,basestring) and resources_str != "":
        try:
            resources = json.loads(resources_str)
        except:
            return HttpResponse("资源数据JSON解析错误!")

    if player_ids:
        player_ids = [int(i) for i in player_ids]

    try:
        if player_ids and servdr_id:
            try:
                gmp = GMProtocol(servdr_id)
                result, err_list = gmp.send_resouces(player_ids, resources)
                rsp_msg = gmp.rsp_map.get(result, result)
                msg["msg"] = rsp_msg
                if err_list: msg["err_list"] = err_list
                for player_id in player_ids:
                    player_id = int(player_id)
                    if player_id not in err_list:
                        msg['ok_list'].append(player_id)
                        gmp.save_log(request.admin.id, gmp.req_type, result, player_id=player_id,remark1=subject, remark2=resources_str)
            except Exception,e:
                msg["msg"] = trace_msg()
        else:
            msg["msg"] = "缺少有效的服务器ID和玩家ID"
    except:
        msg["msg"] = trace_msg()

    return HttpResponse(json.dumps(msg,ensure_ascii=False))

@Route()
def send_red_packet(request,template='game/send_red_packet.html'):
    '''发红包
    '''
    server_id = int(request.REQUEST.get("server_id",'') or 0)
    player_name = request.REQUEST.get('player_name','')
    msg = request.REQUEST.get('msg','')

    if request.method == 'POST' and  server_id != 0:
        _r = {"code":-1,"msg":""}
        try:
            gmp = GMProtocol(server_id)
            msg = json.loads(msg)
            result = gmp.send_red_packet(msg)
            err_msg = gmp.rsp_map.get(result, result)
            _r['code'] = result
        except Exception,e:
            err_msg = trace_msg()
        _r['msg'] = err_msg
        return HttpResponse(json.dumps(_r))
    group_servers_dict = get_group_servers_dict(request)
    return render_to_response(template,locals())

@Route()
def send_expense_rank(request,template='game/send_expense_rank.html'):
    '''发送跨服消费排行
    '''
    activity_id = int(request.REQUEST.get('activity_id','') or 0)
    server_id = int(request.REQUEST.get("server_id",'') or 0)
    msg = request.REQUEST.get('msg','')
    if activity_id:
        model =  Activity.objects.prefetch_related('server').get(id=activity_id)
        select_server_ids = [ s.id for s in model.server.all() ]
    if request.method == 'POST' and  server_id != 0:
        _r = {"code":-1,"msg":""}
        try:
            gmp = GMProtocol(server_id)
            msg = json.loads(msg)
            msg[1] = json.loads(msg[1])
            result = gmp.send_expense_rank(msg)
            err_msg = gmp.rsp_map.get(result, result)
            _r['code'] = result
        except Exception,e:
            err_msg = trace_msg()
        _r['msg'] = err_msg
        return HttpResponse(json.dumps(_r))
    group_servers_dict = get_group_servers_dict(request)
    return render_to_response(template,locals())

@Route()
def send_mail(request,template="game/conferen_send_mail.html"):
    server_id = int(request.REQUEST.get("server_id",'') or 0)
    send_type = int(request.REQUEST.get('send_type','') or 0 )
    player_ids = request.REQUEST.get("player_ids",'') # 角色列表 格式 x1,x2,
    msg = request.REQUEST.get("msg",'')
    send_text = request.REQUEST.get('send_text','')

    select_channel_ids = []
    agent_channels_dict = get_agent_channels_dict(request)

    if player_ids:
        player_ids = json.loads(player_ids)
    if msg:
        _r = {'code':-1, 'msg':'', 'succ': [], 'fail': [] }
        # 保存邮件内容
        try:
            msg = json.loads(msg)
            model = Mail()
            # "ty":类型(0 个人 2 全服 3 联远商ID)
            model.title = msg.get("t","")
            model.content = msg.get("m","")
            if msg["rw"]:
                model.bonus_content = json.dumps(msg["rw"][0]["act"])
            model.type = msg["ty"]
            model.server_ids = str(server_id)
            model.channel_id = int(msg["arg"][0][0]) if msg["ty"] == 3 else 0 
            model.player_id = json.dumps(player_ids) if player_ids else ""
            model.Applicant = str(request.admin.id)
            model.create_time = datetime.datetime.now()
            model.status = 0
            model.save(using='write')
            _r['code'] = 0
            err_msg = "成功保存"
        except Exception,e:
            traceback.print_exc()
            err_msg = trace_msg()
        _r['msg'] = err_msg
        return HttpResponse(json.dumps(_r))

    group_servers_dict = get_group_servers_dict(request)
    return render_to_response(template,locals())


@Route()
def mail_info(request, template='game/mail_info.html'):
    ''' 查看邮件列表
    '''
    player_id = int(request.REQUEST.get('player_id', -1))
    server_id = int(request.REQUEST.get('server_id', 0))
    player_name = request.GET.get('player_name', '')
    page_num = int(request.GET.get('page_num', 1))
    page_size = 20
    total_record = 0

    gmp = GMProtocol(server_id)
    err_msg = ''
    mail_list = []
    try: 
        result = gmp.get_mail(player_id, page_num-1)
        if result and result.get('n'):
            total_record = result['n']
            mail_list = result['l']
            if mail_list and total_record:
                for mail in mail_list:
                    mail['m']['pl'] = json.dumps(mail['m']['pl'], ensure_ascii=False)
                    mail['rw'] = json.dumps(mail['rw'], ensure_ascii=False) if 'rw' in mail else ''
    except Exception, e:
        err_msg = trace_msg()
    return render_to_response(template, locals())


@Route()
def del_mail(request):
    ''' 删除邮件
    '''
    player_id = int(request.REQUEST.get('player_id', -1))
    server_id = int(request.REQUEST.get('server_id', 0))
    mail_id = int(request.REQUEST.get('mail_id', 0))
    svr = request.REQUEST.get('svr')
    svr = int(svr) if svr else 0

    gmp = GMProtocol(server_id)
    err_msg = ''
    try: 
        result = gmp.del_mail(player_id, mail_id, svr)
    except Exception, e:
        err_msg = trace_msg()
    ajax = request.GET.get('ajax', '')
    if ajax:
        if not err_msg: 
            return HttpResponse('{"code":0}')
        else:
            return HttpResponse('{"code":1}')
    return render_to_response('feedback.html')


@Route()
@json_response
def modify_war_story_process(request):
    player_id = int(request.REQUEST.get('player_id','') or 0)
    player_name = request.REQUEST.get('player_name','')
    server_id = player_id >> 20
    code = -1
    msg = ''
    try:
        msg = request.REQUEST.get('msg','')
        msg = json.loads(msg)
        if player_id and server_id:
            gmp = GMProtocol(server_id)
            code = gmp.modify_war_story_process(player_id,msg)
            msg = gmp.rsp_map.get(code,'')
            gmp.save_log(request.admin.id, gmp.req_type, code, role_name=player_name)
    except:
        msg = trace_msg()
    return code,msg

@Route()
@json_response
def modify_expedition_progress(request):
    player_id = int(request.REQUEST.get('player_id','') or 0)
    player_name = request.REQUEST.get('player_name','')
    server_id = player_id >> 20
    code = -1
    msg = ''
    try:
        msg = request.REQUEST.get('msg','')
        msg = json.loads(msg)
        if player_id and server_id:
            gmp = GMProtocol(server_id)
            code = gmp.modify_expedition_progress(player_id,msg)
            msg = gmp.rsp_map.get(code,'')
            gmp.save_log(request.admin.id, gmp.req_type, code, role_name=player_name)
    except:
        msg = trace_msg()
    return code,msg


@Route()
def kill_all_players(request):
    server_id = int(request.REQUEST.get('server_id',0))
    try:
        gmp = GMProtocol(server_id)
        result = gmp.kill_all_players()
        err_msg = gmp.rsp_map.get(result,result)
    except:
        err_msg = trace_msg()

    return HttpResponse(err_msg)

from models.pay import PayChannel,PayAction
from views.game.pay import game_pay

@Route()
def pay(request):
    '''手工充值
    '''
    msg = ''
    try:
        player_id = int(request.REQUEST.get('player_id','') or 0 )
        month_card_gold = int(request.REQUEST.get('month_card_gold','') or 0)
        pay_gold = int(request.REQUEST.get('pay_gold','') or 0)
        extra_gold = int(request.REQUEST.get('extra_gold','') or 0)
        amount = int(request.REQUEST.get('amount','') or 0)
        charge_id = int(request.REQUEST.get('charge_id','') or 0)
        server_id = player_id >> 20
        extra = request.REQUEST.get("extra","")
        if player_id and pay_gold and charge_id:
            order_id = '%s_%s' % (month_card_gold,time.time())
            # amount = pay_gold / 10
            is_card = month_card_gold
            # gmp = GMProtocol(server_id)
            # result = gmp.player_pay(player_id,order_id,pay_gold,extra_gold,is_card=is_card)
            # msg = gmp.rsp_map.get(result)
            now = datetime.datetime.now()
            pay_channel = PayChannel()
            pay_channel.card_key = is_card
            pay_channel.gold = month_card_gold
            the_action = PayAction()
            the_action.query_id = the_action.get_query_id()
            the_action.order_id = order_id
            the_action.channel_key = ''
            the_action.channel_id = 0
            the_action.server_id = server_id
            the_action.pay_type = 0
            the_action.pay_user = player_id
            the_action.pay_ip = ''
            the_action.pay_status = 2
            the_action.post_time = now
            the_action.last_time = now
            the_action.post_amount = amount
            the_action.pay_amount = amount
            the_action.pay_gold = pay_gold
            the_action.extra = extra_gold
            the_action.charge_id = charge_id
            the_action.charge_type = 0
            the_action.remark = '手工充值 (%s), 账号 %s' % (pay_channel.card_key,request.admin.alias)
            the_action.save()
            msg =  game_pay(the_action,pay_channel,extra=extra)
            msg = '成功!' if not msg else msg
    except:
        msg = trace_msg()
    return HttpResponse(msg)


@Route()
def deduction(request):
    '''
    扣款，或者加buffID的
    '''
    msg = ''
    
    player_id = int(request.REQUEST.get('player_id','') or 0 )
    ly_amount = int(request.REQUEST.get('ly_amount','') or 0 )
    by_amount = int(request.REQUEST.get('by_amount','') or 0 )
    add_buff_id = int(request.REQUEST.get('add_buff_id','') or 0 )
    remove_buff_id = int(request.REQUEST.get('remove_buff_id','') or 0 )
    buff_time = int(request.REQUEST.get("buff_time",'') or 0 )

    if not ly_amount and not by_amount and not add_buff_id and not remove_buff_id:
        msg = "未填写任何参数！"
        return HttpResponse(msg)

    server_id = player_id >> 20

    gmp = GMProtocol(server_id)
    if ly_amount or by_amount:
        result = gmp.deduction_jade([player_id,ly_amount,by_amount])
        if result == 0:
            msg += " 扣除成功  \n"

    if add_buff_id:
        if not buff_time:
            return HttpResponse("没有填写BUFF时间！")
        result = gmp.add_buffID([player_id,add_buff_id,buff_time])
        if result == 0:
            msg += " 添加BUFF成功  \n"

    if remove_buff_id:
        result = gmp.remove_buffID([player_id,remove_buff_id])
        if result == 0:
            msg += " 移除BUFF成功  \n"

    return HttpResponse(msg)



