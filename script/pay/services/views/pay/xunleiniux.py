# -*- coding: utf-8 -*-
from services.views import md5

def confirm_xunleiniux_get_link_id(request):
    return ''

def confirm_xunleiniux(request,pay_channel={}):
    
    g = lambda x,y:request.POST.get(x,request.GET.get(x,y))
    app_key = pay_channel.get_config_value('app_key','0e7a4c2691b623a69c6ef0337896ec04')
    
    orderid = g('orderid', '')
    user = g('user', '')
    gold = g('gold', '')
    money = g('money', '')
    time = g('time', '')
    sign = g('sign', '')
    server = g('server', '')
    roleid = g('roleid', '')
    
    sign_str = '%s%s%s%s%s%s'% (orderid, user, gold, money, time, app_key)
    
    remark = ''
    result_msg = ''
    order_id = ''
    server_id = 0
    player_id = 0
    amount = 0
    
    if sign == md5(sign_str):
        try:                
            server_id = int(server)
            player_id = int(roleid)
            amount = int(money)
            order_id = orderid
        except Exception, ex:
            print 'Urecharge_Id error'
         
        result_msg = '1'
    else:
        result_msg = '-2'
    
    return {'server_id':server_id,'player_id':player_id, 'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg}

