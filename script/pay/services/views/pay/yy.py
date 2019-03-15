# -*- coding: utf-8 -*-
from services.views import md5
from django.http import HttpResponse
from services.views import query_player
from django.shortcuts import render_to_response
import json

def confirm_yy_get_link_id(request):
    return request.GET.get('type', '')


def confirm_yy(request, pay_channel={}):
    g = request.GET
    #print g
    account = g.get('account', '') 
    orderid = g.get('orderid', '')
    rmb = g.get('rmb', '')#单位：元
    coin = g.get('coin', '')
    sign = g.get('sign', '')
    type = g.get('type', '')
    time = g.get('time', '')
    game = g.get('game', '')
    server = g.get('server', '')
    nickname = g.get('nickname', '')
    
    user_type = pay_channel.get_config_value('user_type','')
    server_id = 0
    open_id = ''
    order_id = ''
    pay_amount = 0
    remark = ''
    result_msg = ''
    
    
    #MD5(account+ orderid + rmb + coin + game+ server +nickname+time+ 密钥)，其中nickname不用进行编码
    
    try: 
        app_key = pay_channel.get_config_value('app_key','dpmoFiT05iTvMYGrvvuokwybDz0n0Jja')
        s_sign = '%s%s%s%s%s%s%s%s%s' % (account, orderid, rmb, coin, game, server, nickname, time, app_key)
        s_sign = md5(s_sign)
        print sign, s_sign
        
        open_id = account
        order_id = orderid
        server_list = pay_channel.get_config_value('server_list',None)
        if server_list != None and server_id!='':
            server_id = server_list.get(str(server),server)
        else:
            server_id = server
        
        server_id = int(server_id)
            
        if sign == s_sign:
            rmb = float(rmb)
            result_msg = '1'
            if rmb > 0:
                pay_amount = rmb
        else:
            remark = 'sign error'
            result_msg = '-11'
        
    except Exception, ex:
        print 'confirm yy error'
        print ex
    
    
    return {'server_id':server_id, 'open_id':open_id, 'user_type':user_type, 'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

def query_yy(request):
    g = request.GET
    account = g.get('account', '')
    time = g.get('time', '')
    game = g.get('game', '')
    server = g.get('server', '')
    sign = g.get('sign', '')
    
    code = -1
    
    s_sign = md5('%s%s%s%s%s' % (account, game, server, time, 'dpmoFiT05iTvMYGrvvuokwybDz0n0Jja'))
    
    player = {'user_id':0, 'player_id':0, 'player_name':'', 'level':0, 'server_id':0}
    sign = sign.lower()
    if sign != s_sign:
        return render_to_response('client/yy/player_info.html', {'player':player, 'code':code})
    
    try:
        server = int(server)
        player = query_player(46, account, server)
        code = 0
    except Exception, ex:
        print 'query yy error:', ex
    
    return render_to_response('client/yy/player_info.html', {'player':player, 'code':code})
    
    
    