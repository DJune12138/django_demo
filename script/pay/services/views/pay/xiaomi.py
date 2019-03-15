# -*- coding: utf-8 -*-
import hmac, hashlib
import binascii, datetime

def confirm_xiaomi_get_link_id(request):
    return ''
     
def confirm_xiaomi(request, pay_channel={}):
    
    
    app_id = pay_channel.get_config_value('app_id', '5596')
    app_key = pay_channel.get_config_value('app_key', '8952d691-6c09-9fa3-2075-5100dcee1f3c')
    
    cpOrderId = get_param(request, 'cpOrderId', '')#开发商订单ID
    cpUserInfo = get_param(request, 'cpUserInfo', '')#开发商透传参数
    uid = get_param(request, 'uid', '')#用户ID
    orderId = get_param(request, 'orderId', '')#游戏平台订单ID
    orderStatus = get_param(request, 'orderStatus', '')#订单状态
    payFee = get_param(request, 'payFee', '0')
    productCode = get_param(request, 'productCode', '')
    productName = get_param(request, 'productName', '')
    productCount = get_param(request, 'productCount', '')
    payTime = get_param(request, 'payTime', '')
    
    
    signature = get_param(request, 'signature', '')
    
    server_id, player_id, timestuple = cpOrderId.split('_')
    app_key = app_key.encode('utf-8')
    server_sign = u'appId=%s&cpOrderId=%s&cpUserInfo=%s&orderId=%s&orderStatus=%s&payFee=%s&payTime=%s&productCode=%s&productCount=%s&productName=%s&uid=%s'
    server_sign = server_sign % (app_id, cpOrderId, cpUserInfo, orderId, orderStatus, payFee, payTime, productCode, productCount, productName, uid)
    server_sign = server_sign.encode('utf-8')
    hashed = hmac.new(app_key, server_sign, hashlib.sha1)
    server_sign = binascii.b2a_hex(hashed.digest())
    
    query_id = ''
    orderid = ''
    amount = 0
    remark = '' 
    result_code = ''
    
    server_id = int(server_id)
    player_id = int(player_id)
    
    if signature == server_sign:
        query_id = cpOrderId
        orderid = orderId 
        result_code = '{"errcode":200}'
        if orderStatus == 'TRADE_SUCCESS':
            amount = float(payFee) / 100 
            remark = 'success'
    else:
        result_code = '{"errcode":1525}'
    
    return {'query_id':query_id, 'player_id':player_id,'server_id':server_id,'order_id':orderid,'amount':amount,'remark':remark,'result_msg':result_code}




def get_param(request, param_name, default, lambda_expression = lambda p:p):
    return lambda_expression(request.GET.get(param_name, default))




    
