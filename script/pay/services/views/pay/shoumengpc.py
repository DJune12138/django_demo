# -*- coding: utf-8 -*-
from services.views import md5

def confirm_shoumengpc_get_link_id(request):
    return ''

def confirm_shoumengpc(request,pay_channel):
    app_key = pay_channel.get_config_value('app_key','dcb60382d326868980c2c4d080811666')
    
    keys = ['user_id','login_account','game_id','packet_id','game_server_id','game_role_id','order_id','game_coin','total_fee','pay_time','pay_result','sign']
    user_id,login_account,game_id,packet_id,game_server_id,game_role_id,order_id,game_coin,total_fee,pay_time,pay_result,sign = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]
    sign_str = 'user_id=%s&login_account=%s&game_id=%s&packet_id=%s&game_server_id=%s&game_role_id=%s&order_id=%s&game_coin=%s&total_fee=%s&pay_time=%s&pay_result=%s&secret=%s' % \
                (user_id,login_account,game_id,packet_id,game_server_id,game_role_id,order_id,game_coin,total_fee,pay_time,pay_result,app_key)
    sign_str = md5(sign_str)
    print '-' * 40
    print dict(request.POST)
    print (sign,sign_str)
    remark = ''
    result_msg = 'FAILURE'
    pay_amount = 0
    server_id = player_id = 0
    orderId = ''
    if sign.encode('utf-8') == sign_str.encode('utf-8'):
        try:
            pay_amount = float(total_fee)
            if int(pay_result) == 1 and pay_amount > 0:
                server_id = int(game_server_id)
                player_id = int(game_role_id)
                orderId = order_id
                result_msg =  'SUCCESS'
        except Exception,e:
            print('confirm youai has error',e)
    else:
        result_msg = 'ErrorSign'
    
    _r = {'server_id':server_id, 'player_id':player_id,'order_id':orderId,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        
    return _r
    
        
        
'''
[参数]传输方式：HTTP POST
user_id:用户ID
login_account:用户帐号（Login_Account）
game_id:游戏编号
packet_id:渠道包ID
game_server_id:区服ID
game_role_id:角色ID--规范所有游戏一样提供
order_id:定单ID
game_coin：转换元宝数量
total_fee:付款金额
pay_time:支付时间[使用时间戳]
pay_result:支付状态，支付结果成功=1，失败=0
sign:签名[上面11个参数，MD5]，
     【CP返回参数】成功：返回SUCCESS

''' 
        
        
        
        
        