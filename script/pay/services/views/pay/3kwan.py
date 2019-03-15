# -*- coding: utf-8 -*-
#
from services.views import md5

#方法里不涉及数据库操作,包括参数处理,验证签名,返回json对象:user_type,openid,server_id,player_id,pay_amount,result_msg

def confirm_3kwan_get_link_id(request):
    return request.GET.get('type','')

def confirm_3kwan(request,pay_channel):
    result_msg = 'FAILURE'
    server_id = request.GET.get('area_id','')
    callbackInfo = request.GET.get('callback_info','')
    open_id = request.GET.get('uid','')
    order_id = request.GET.get('order_id','')
    order_status = request.GET.get('status','')
    pay_type = request.GET.get('payType','')
    amount = request.GET.get('fee','')
    player_id = int(request.GET.get('role_id','0'))
    timestamp = request.GET.get('timestamp','')
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
        print('confirm 3kwan has error0',e)
    
    sign_str = '%s%s%s%s%s%s%s%s' % (open_id,amount,server_id,order_id,player_id,callbackInfo,timestamp,app_key)
    print '-' * 40
    print sign_str
    sign_str = md5(sign_str)
    print(sign_str,sign)
    
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
            print('confirm 3kwan has error',e)
    else:
        result_msg = 'ErrorSign'
    
    _r = {'server_id':the_server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        
    if player_id:
        _r = {'server_id':the_server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        
    return _r
   
        
        
        
        
        
        
        
        
        
