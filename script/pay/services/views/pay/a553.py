# -*- coding: utf-8 -*-
from services.views import md5

def confirm_a553_get_link_id(request):
    return request.GET.get('payType', '')

 
def confirm_a553(request,pay_channel={}):
    
    app_key = pay_channel.get_config_value('app_key', 'sgesferyrhrgefegtrhe3trfq')
    user_type = pay_channel.get_config_value('user_type',25)
    
    uname = request.GET.get('uname', '')
    package = request.GET.get('package', '')
    count = request.GET.get('count', '')
    rmb = request.GET.get('rmb', '')
    orderid = request.GET.get('orderid', '')#平台订单号
    userdata = request.GET.get('userdata', '')#透传参数
    sign = request.GET.get('sign', '')#md5(游戏币包容量+游戏币包个数+人民币+玩家帐号+平台订单号+key)
    
    
    #********回调接口返回参数说明（字符型）*****
    #1    Sign验证失败
    #0&orderid    充值成功，返回0和平台传的订单号
    #2    该平台订单号已经为玩家充值，本此回调未再充值
    #3    充值失败
    
    server_sign = '%s%s%s%s%s%s' % (package, count, rmb, uname, orderid, app_key)
    print server_sign
    server_sign = md5(server_sign)
    print (sign, server_sign)
    
    pay_amount = 0
    result_code = '1'
    order_id = ''
    open_id = ''
    server_id = 0
    player_id = ''
    remark = ''
    try:
        if sign == server_sign:
            amount = float(rmb)
            if 0 < amount:
                result_code = '0&%s' % orderid
                order_id = orderid
                open_id = uname
                server_id, player_id = userdata.split('_')
                
                server_id = int(server_id)
                player_id = int(player_id)
                
                pay_amount = amount
        else:
            result_code = '1'
    except Exception, ex:
        remark = '错误信息 %s' % ex
        
    return {'server_id':server_id, 'player_id':player_id, 'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_code}

