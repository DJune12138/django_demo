# -*- coding: utf-8 -*-
#已测   GET  http://127.0.0.1:8002/service/confirm/youai?serverId=14&callbackInfo=14&openId=14680065&orderId=120507224627804959449D&orderStatus=1&payType=2&amount=10&remark=hello&sign=db651e40d456c8b0972f5447173329d1
from services.views import md5

#方法里不涉及数据库操作,包括参数处理,验证签名,返回json对象:user_type,openid,server_id,player_id,pay_amount,result_msg

def confirm_3kwanios_get_link_id(request):
    return request.GET.get('payType','')

def confirm_3kwanios(request,pay_channel):
    result_msg = 'FAILURE'
    server_id = request.GET.get('serverId','')
    callbackInfo = request.GET.get('callbackInfo','')
    open_id = request.GET.get('openId','')
    order_id = request.GET.get('orderId','')
    order_status = request.GET.get('orderStatus','')
    pay_type = request.GET.get('payType','')
    amount = request.GET.get('amount','')
    player_id = int(request.GET.get('roleId','0'))

    remark = request.GET.get('remark','')
    sign = request.GET.get('sign','')
    
    app_key = ''
    user_type = 0
    my_server_id = ''

    try:
        app_key = pay_channel.get_config_value('app_key','')
        user_type = pay_channel.get_config_value('user_type',0)
        server_list = pay_channel.get_config_value('server_list',None)
        if server_list != None and server_id!='':
            my_server_id = server_list.get(server_id,server_id)
    except Exception,e:
        print('confirm 3kwanios has error0',e)
    
    sign_str = '%s%s%s%s%s%s%s%s%s'%(server_id,callbackInfo,open_id,order_id,order_status,pay_type,amount,remark,app_key)
    print '-' * 40
    print sign_str
#    print(sign_str)
    sign_str = md5(sign_str)
#    print(sign_str,sign)
    
    pay_amount = 0
    the_server_id = 0

    if sign==sign_str:
        try:
            if server_id!='':
                if my_server_id != '':
                    the_server_id = int(my_server_id)
                else:
                    the_server_id = int(server_id)
            else:
                the_server_id = int(callbackInfo)
        
            if int(order_status)==1:
                pay_amount = float(amount)
            else:
                pay_amount = 0
            result_msg =  'SUCCESS'
        except Exception,e:
            print('confirm youai has error',e)
    else:
        result_msg = 'ErrorSign'
    
    _r = {'server_id':the_server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        
    if player_id:
    	_r = {'server_id':the_server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        
    return _r
   
        
        
        
        
        
        
        
        
        
