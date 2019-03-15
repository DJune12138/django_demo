# -*- coding: utf-8 -*-
from services.views import md5

def confirm_baidu_yueyu_get_link_id(request):
    return ''
    
    
def confirm_baidu_yueyu(request,pay_channel={}):
    
    result_code = 'ERROR_SIGN'
    api_key = ''
    secret_key = ''
    user_type = -1
    try:
        api_key = pay_channel.get_config_value('api_key', '3cfb9266013d3b6743a8411f1017deee')
        secret_key = pay_channel.get_config_value('secret_key', '8a97a7b23cfb9266013d1017deee4120')
        user_type = pay_channel.get_config_value('user_type', -1)
    except:
        result_code = 'ERROR_PAY_CONFIG'
    
    user_id = request.POST.get('user_id', '')#玩家登陆游戏时向厂商传入的user_id
    server_id = request.POST.get('server_id', '')#百度游戏开放平台分配给合作商户游戏的服务器编号
    timestamp = request.POST.get('timestamp', '')#服务请求时间戳，格式yyyy-MM-dd hh:mm:ss
    order_id = request.POST.get('order_id', '')#百度游戏平台对应商户订单号（厂商与百度对账时使用）
    wanba_oid = request.POST.get('wanba_oid', '')#百度游戏平台对应支付订单号
    amount = request.POST.get('amount', '')#金额（单位元）
    currency = request.POST.get('currency', '')#币种（目前只有人民币）
    result = request.POST.get('result', '')
    
    back_send = request.POST.get('back_send', '')#后台通知（Y）、前台通知（N）
    
    sign = request.POST.get('sign', '')
    sign = sign.lower()
    
    my_server_id = 0
    server_list = pay_channel.get_config_value('server_list',None)
    if server_list != None and server_id!='':
        my_server_id = server_list.get(str(server_id),server_id)
    #print 'my_server_id:%s' % my_server_id
    
    
    #sign=md5(secret_key+”amount”+amount+“api_key”+api_key+”back_send”+back_send+”currency”+currency+”order_id”+order_id+”result”+result
    #“server_id”+server_id+“timestamp”+timestamp+“user_id”+user_id+”wanba_oid”+ wanba_oid)
    
    sign_str = '%samount%s' % (secret_key, amount)
    sign_str += 'api_key' + api_key
    sign_str += 'back_send' + back_send
    sign_str += 'currency' + currency
    sign_str += 'order_id' + order_id
    sign_str += 'result' + result
    sign_str += 'server_id' + server_id
    sign_str += 'timestamp' + timestamp
    sign_str += 'user_id' + user_id
    sign_str += 'wanba_oid' + wanba_oid
    
    #print 'sign_str :: %s' % sign_str
    sign_str = md5(sign_str) 
    pay_amount = 0
    remark = ''
    #print 'sign:::%s, %s' % (sign, sign_str)
    if sign == sign_str:
        try:
            if my_server_id != '':
                my_server_id = int(my_server_id)
            if 1 == int(result):
                pay_amount = float(amount)
                remark = wanba_oid
                result_code = '<!--recv=ok-->'
        except:
            result_code = 'unknow error'
    
    
    return {'order_id':order_id,'server_id':my_server_id,'open_id': user_id,'user_type':user_type,'amount':pay_amount,'remark':remark,'result_msg':result_code}
