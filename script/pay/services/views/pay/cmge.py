# -*- coding: utf-8 -*-
from services.views import md5

def confirm_cmge_get_link_id(request):
    return ''
    
__request = None
def confirm_cmge(request,pay_channel={}):
    
    app_key = pay_channel.get('app_key', '')
    user_type = pay_channel.get('user_type', '')
    
    __request = request
    
    openId = get_param('openId', '')
    serverId = get_param('serverId', '')
    serverName = get_param('serverName', '')
    roleId = get_param('roleId', '')
    roleName = get_param('roleName', '')
    orderId = get_param('orderId', '')
    orderStatus = get_param('orderStatus', -1, lambda x:float(x))
    payType = get_param('payType', '')
    amount = get_param('amount', '')
    remark = get_param('remark', '')
    callBackInfo = get_param('callBackInfo', '')
    sign = get_param('sign', '')
    
    
    #sign = MD5(“openId=100000& serverId=123& serverName=测试服务器& roleId=147& roleName=测试角色& orderId=20121129115114758& orderStatus=1& payType=支付宝& amount=1000& remark=&callBackInfo=自定义数据&app_key=1478523698”)
    server_sign = 'openId=%s&serverId=%s&serverName=%s&roleId=%s&roleName=%s&orderId=%s&orderStatus=%s&payType=%s&amount=%s&remark=%s&callBackInfo=%s&app_key=%s'
    server_sign = server_sign % (openId, serverId, serverName, roleId, roleName, orderId, orderStatus, payType, amount, remark, callBackInfo, app_key)
    print server_sign
    server_sign = md5(server_sign)
    print (sign, server_sign)
     
    order_id = ''
    server_id = 0
    pay_amount = 0
    result_code = 'error'
    if sign == server_sign:
        orderid = order_id
        open_id = openId
        server_id = serverId
        result_code = 'success'
        if 1 == orderStatus:
            pay_amount = amount / 100
    else:
        result_code = 'errorSign'
    
    return {'open_id':open_id, 'user_type': user_type, 'server_id':server_id, 'order_id':orderid,'amount':pay_amount,'remark':remark,'result_msg':result_code}



def get_param(param_name, default, lambda_expression = lambda p:p):
    return lambda_expression(__request.GET.get(param_name, default))
    
