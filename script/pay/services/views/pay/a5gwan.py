# -*- coding: utf-8 -*-
from services.views import md5
import base64

def confirm_a5gwan_get_link_id(request):
    return request.GET.get('payType', '')

def confirm_a5gwan(request,pay_channel={}): 
    app_key = pay_channel.get_config_value('app_key', '8d1e5d350af49d29843f0ba8cc3c0f7e')
    
#    username：用户名
#    change_id：订单号
#    money：金额（元）
#    hash：md5(username|change_id|money |app_key)
#    ad_key：渠道号
#    object：游戏方从客户端传回的自定义扩展参数，服务器号可该参数来传（可选）

    
    username = request.POST.get('username', '')
    change_id = request.POST.get('change_id', '')
    money = request.POST.get("money", '') 
    hash_str = request.POST.get("hash", '')
    pc_object = request.POST.get('object', '')
     
    
    server_sign = '%s|%s|%s|%s' % (username, change_id, money, app_key)
    print server_sign
    server_sign = md5(server_sign)
    server_sign = server_sign.upper()
    print (hash_str, server_sign)
    
    orderid = ''
    pay_amount = 0
    remark = ''
    result_code = '0'
    server_id = 0
    player_id = 0
    hash_str = hash_str.lower()
    server_sign = server_sign.lower()
    result = {}
    try:
        if hash_str == server_sign:
            result_code = '1'
            orderid = change_id  
            
            pay_amount = float(money)
            if 0 < pay_amount:
                pc_object = str(pc_object)
                if -1 != pc_object.find('_'):
                    server_id, player_id = pc_object.split('_')
                    server_id = int(server_id)
                    player_id = int(player_id)
                    result = {'server_id':server_id, 'player_id':player_id} 
                else:
                    open_id = username
                    server_id = int(pc_object)
                    user_type = pay_channel.get_config_value('user_type', 61)
                    result = {'server_id':server_id, 'open_id':open_id, 'user_type':user_type}
                
                result['order_id'] = orderid
                result['amount'] = pay_amount
        else:
            remark = 'sign error'
    except Exception, ex:
        print '5gwan interal error'
        print ex
        remark = 'internal error'
        
    result['remark'] = remark
    result['result_msg'] = result_code
    return result


    
