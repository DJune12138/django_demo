# -*- coding: utf-8 -*-
from services.views import md5
 

def confirm_wanpu_get_link_id(request):
    g = request.GET.get
    pay_type = g('pay_type', '')
    return pay_type

def confirm_wanpu(request, pay_channel={}):
    app_key = pay_channel.get_config_value('app_key', '981C9025F2C764A6')
    
    g = request.GET.get
    
    order_id = g('order_id', '')  #商户订单ID
    app_id = g('app_id', '')  #商户应用ID
    user_id = g('user_id', '')  #用户ID
    pay_type = g('pay_type', '')  #支付方式
    result_code = g('result_code', '')  #支付结果状态
    result_string = g('result_string', '')  #支付结果描述
    trade_id = g('trade_id', '')  #支付流水号
    amount = g('amount', '')  #实际支付金额
    pay_time = g('pay_time', '')  #支付时间
    sign = g('sign', '').lower()  #签名

    server_sign = '%s%s%s%s' % (order_id,user_id,amount,app_key)
    
    server_sign = md5(server_sign)
    
    remark = ''
    result_msg = ''
    o_id = ''
    pay_amount = 0
    player_id = 0
    server_id = 0
    if sign == server_sign:
        result_msg = 'success'
        amount = float(amount)
        if amount > 0 and (result_code == '0' or result_code == 0):
            pay_amount = amount
        
        o_id = trade_id
        tmp = order_id.split('_')
        server_id = int(tmp[0])
        player_id = int(tmp[1])
    else:
        remark = 'sign error'
        
    
    
    return {"amount":pay_amount, "order_id":o_id, "server_id":server_id, "player_id":player_id, "remark":remark, "result_msg":result_msg}
 
