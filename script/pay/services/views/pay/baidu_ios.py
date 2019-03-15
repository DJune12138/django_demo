# -*- coding: utf-8 -*-
from services.views import md5

def confirm_baidu_ios_get_link_id(request):
    return request.POST.get('product_id')
    
    
def confirm_baidu_ios(request,pay_channel={}):
    
    result_code = 'ERROR_SIGN'
    
    try:
        api_key = pay_channel.get_config_value('api_key', '3bcc6690013b5d1794881a2dd0c8d38f')
        secret_key = pay_channel.get_config_value('secret_key', '8a97a9943bcc6690013bd0c8d38f1a2e')
        user_type = pay_channel.get_config_value('user_type', 22)
    except:
        result_code = 'ERROR_PAY_CONFIG'
    
    user_id = request.POST.get('user_id', '')#玩家登陆游戏时向厂商传入的user_id
    server_id = request.POST.get('server_id', '')#百度游戏开放平台分配给合作商户游戏的服务器编号
    order_id = request.POST.get('order_id', '')#百度游戏平台对应商户订单号（厂商与百度对账时使用）
    transaction_id = request.POST.get('transaction_id', '')#苹果应用内支付对应订单号
    product_id = request.POST.get('product_id', '')
    quantity = request.POST.get('quantity', '')
    timestamp = request.POST.get('timestamp', '')
    sign = request.POST.get('sign', '')
    my_server_id = ''
    server_list = pay_channel.get_config_value('server_list',None)
    if server_list != None and server_id!='':
        my_server_id = server_list.get(str(server_id),server_id)
    #print 'my_server_id:%s' % my_server_id
    
    sign_str = '%sapi_key%sorder_id%sproduct_id%squantity%sserver_id%stimestamp%suser_id%stransaction_id%s' % (secret_key, api_key, order_id, product_id, quantity, server_id, timestamp, user_id, transaction_id)
    #print 'sign_str :: %s' % sign_str
    sign_str = md5(sign_str) 
    amount = 0
    remark = ''
    #print 'sign:::%s, %s' % (sign, sign_str)
    if sign == sign_str:
        try:
            if my_server_id != '':
                my_server_id = int(my_server_id)
            amount = float(quantity)
            remark = transaction_id
            result_code = '<!--recv=ok-->'
        except:
            result_code = 'unknow error'
    
    
    return {'order_id':order_id,'server_id':my_server_id,'open_id': user_id,'user_type':user_type,'amount':amount,'remark':remark,'result_msg':result_code}
