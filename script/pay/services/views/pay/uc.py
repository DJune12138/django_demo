# -*- coding: utf-8 -*-

from services.views import md5
import json


def confirm_uc_get_link_id(request):
    post_json = json.loads(request.raw_post_data)
    return post_json['data']['payWay']

        
def confirm_uc(request,pay_channel={}):
    pay_status = 'FAILURE'
    post_json = {}
    try:
        post_json = json.loads(request.raw_post_data)
    except Exception,e:
        print('confirm uc error:',e)
#    else:
#        post_json = json.loads('{"data": {"orderId": "20120425200351171292", "gameId": "43233", "failedDesc": "", "payWay": "1", "amount": "50.0", "orderStatus": "S", "ucid": "56920", "callbackInfo": "", "serverId": "876"}, "sign": "a38a09fb38ec3110f036b3b4b203ceff"}')

    sign = post_json.get('sign','').encode('utf-8')
    data = post_json.get('data',{})
    
    cpId = pay_channel.get_config_value('cpId',686)
    gameId = pay_channel.get_config_value('gameId',64026)
#    channelId = pay_channel.get_config_value('channelId',2)
    serverId = pay_channel.get_config_value('serverId',951)
    apiKey = pay_channel.get_config_value('apiKey','40deb8c3b1c5596569842e2b5e407bc7')
    
    ''''
    cpId = 673
    gameId = 43233
    channelId = 2
    serverId = 876
    apiKey = '772c6ef159853310318733399c8cb9f0'
    '''
    #print(data['amount'],data['callbackInfo'],data['failedDesc'],gameId,data['orderId'],data['orderStatus'],data['payWay'],serverId,data['ucid'],apiKey)
    sign_str = u'%damount=%scallbackInfo=%sfailedDesc=%sgameId=%dorderId=%sorderStatus=%spayWay=%sserverId=%ducid=%s%s'%(cpId,data.get('amount',''),data.get('callbackInfo',''),data.get('failedDesc',''),gameId,data.get('orderId',''),data.get('orderStatus',''),data.get('payWay',''),serverId,data.get('ucid',''),apiKey)
    sign_str = md5(sign_str)
    
    print(sign_str==sign)
    pay_amount = 0
    user_type = 2
    open_id = ''
    server_id = 0
    order_id = ''
    remark = ''
    if sign_str == sign:
        try:
            open_id = data.get('ucid','')
            server_id = int(request.GET.get('s','0'))
            
            if server_id == 0:
                server_id = int(data.get('callbackInfo',server_id))
            
            order_id = data.get('orderId','')
            remark = data.get('failedDesc','')        
    
            if data.get('orderStatus','')=='S':
                pay_amount =  float(data.get('amount','0'))
                        
            pay_status = 'SUCCESS'
        except Exception,e:
            print('confirm uc:',e)
    else:
        print('sign error:')

    return {'server_id':server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':pay_status}

