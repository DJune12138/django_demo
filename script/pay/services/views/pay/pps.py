# -*- coding: utf-8 -*-
from services.views import md5
import json, urllib

def confirm_pps_get_link_id(request):
    return ''
    
    
def confirm_pps(request, pay_channel={}):
    g = request.GET
    user_id = g.get('user_id', '')
    role_id = g.get('role_id', '')
    order_id = g.get('order_id', '')#平台订单号（唯一） 
    money = g.get('money', '')#充值金额（人民币） 
    server_id = g.get('server_id', '')
    time = g.get('time', '')
    userData = g.get('userData', '')
    sign = g.get('sign', '')
    
    
    
    player_id = 0
    s_id = 0
    pay_amount = 0
    remark = ''
    result_msg = '{"result":-6, "message":""}'
    
    sign_p_list = ['user_id=%s' % user_id, 'role_id', 'role_id', 'order_id', 'money', 'server_id', 'time', 'userData']
    s_sign = reduce(lambda x,y: '%s&%s=%s' % (x, y, g.get(y, '')), sign_p_list)
    
    app_key = pay_channel.get_config_value('app_key','')
    s_sign = '%s&key=%s' % (s_sign, app_key)
    print s_sign
    s_sign = md5(s_sign)
    print (sign, s_sign)
    try:
        if sign == s_sign:
            player_id = int(role_id)
            s_id = int(server_id)
            money = float(money)
            if money > 0:
                pay_amount = money
            result_msg = '{"result":0, "message":""}'
    except Exception, ex:
        print 'pps confirm error '
        print ex
        
    
    return {'server_id':s_id, 'player_id':player_id ,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

    
    