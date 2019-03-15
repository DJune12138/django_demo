# -*- coding: utf-8 -*-
from services.views import md5

def confirm_pptv_new_get_link_id(request):
    return ''
    
def confirm_pptv_new(request,pay_channel={}):
    sid = request.GET.get('sid', '')
    roid = request.GET.get('roid', '')
    username = request.GET.get('username', '')
    oid = request.GET.get('oid', '')
    amount = request.GET.get('amount', '')#元
    extra = request.GET.get('extra', '')#透传参数
    time = request.GET.get('time', '')
    sign = request.GET.get('sign', '')
    
    app_key = pay_channel.get_config_value('app_key','dd950209bfb86dd9e6e449e7d14d365f')
    
    server_id = 0
    player_id = 0
    pay_amount = 0
    order_id = ''
    remark = ''
    result_msg = '{"code":"2","message":""}'
    
    #md5(sid + username + roid + oid + amount + time + key)
    server_sign = ''
    try:
        server_sign = '%s%s%s%s%s%s%s' % (sid, username, roid, oid, amount, time, app_key)
    except Exception, ex:
        print 'confirm_pptv error'
        print ex
    
    server_sign = md5(server_sign)
    sign = sign.lower()
    if server_sign == sign:
        result_msg = '{"code":"1","message":""}'
        try:
            amount = float(amount)
            if amount > 0:
                pay_amount = amount
                server_id = int(sid)
                player_id = int(roid)
                order_id = oid
                remark = 'success'
        except Exception, ex:
            print 'confirm pptv error'
            print ex
    else:
        result_msg = '{"code":"4","message":""}'
        remark = 'sign error'
    
    return {'server_id':server_id,'player_id':player_id,'order_id':order_id, 'amount':pay_amount, 'remark':remark,'result_msg':result_msg}


# --- 接口 ---
from services.views import query_player,getConn
from services.models.center import Server, Channel

from django.http import HttpResponse
import json,time,datetime

def query_pptv_new(request):
    action = request.GET.get('action','')
    if action == 'server_list':
        return server_list(request)
    elif action == 'player_exists':
        return player_exists(request)
    elif action == 'other_info':
        return other_info(request)
    
    return HttpResponse('pptv')


def server_list(request):
    '''服务器列表接口
    {"status":1,"msg":"提示信息","servers":{"2":{"sname":"\u53cc\u7ebf2\u670d","status":"1","opentime":"1395284400"},"1":{"sname":"\u53cc\u7ebf1\u670d","status":"1","opentime":"1395111600"}}
    '''
    _d = {"status":0,"servers":[],"msg":""}
    gid = request.REQUEST.get
    channel_key = '0002470000'
    list_server = Server.objects.filter(channel__key=channel_key)
    if list_server:
        _d['status'] = 1
        for s in list_server:
            
            _s = {"%s"%s.id:{"sname":s.name,"status":s.status,
                               "opentime": "%s" % int(time.mktime(s.create_time.timetuple()))
                               }
                 }
            _d['servers'].append(_s)
    return HttpResponse(json.dumps(_d))

def player_exists(request):
    '''0 ：未注册(角色不存在)
1 ：已注册(角色存在)
2 ：参数错误
3 ： 签名错误
4 ：平台或区服错误
5 ： 其他错误
    '''
    _d = {"status":5,"msg":"","data":""}
    user_type = 13
    
    try:
        openid = request.GET.get('username','')
        server_id = int(request.GET.get('server_num','0'))
        player = query_player(user_type, openid, server_id)
        if player["user_id"]:
            _d["status"] = 1
            _d["data"] = player
    except:
        pass
    return HttpResponse(json.dumps(_d))


def other_info(request):
    pass