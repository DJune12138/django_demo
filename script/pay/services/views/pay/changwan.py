# -*- coding: utf-8 -*-
#GET  http://127.0.0.1service/confirm/changwan?serverid=36&custominfo=36&openid=1355907735456214087428906&ordernum=20121219204119-10011858834-4386814279&status=-1&paytype=5&amount=0&errdesc=7&paytime=20121219204120&sign=891b124353869c8ad4520af1709aa685
from services.views import md5
#http://test.fytxonline.com/service/confirm/changwan?serverid=28&custominfo=28&openid=1355907735456214087428906&ordernum=20121219213340-10011858834-5426485353&status=-1&paytype=3&amount=0&errdesc=7&paytime=20121219213341&sign=f78463884e1009e5732d5dcdd35135e7
def confirm_changwan_get_link_id(request):
    return request.GET.get('paytype','')

def confirm_changwan(request,pay_channel):
    result_msg = '103'
    server_id = request.GET.get('serverid','')
    callbackInfo = request.GET.get('custominfo','')
    open_id = request.GET.get('openid','')
    order_id = request.GET.get('ordernum','')
    order_status = request.GET.get('status','')
    pay_type = request.GET.get('paytype','')
    amount = request.GET.get('amount','')
    pay_time = request.GET.get('paytime','')
    remark = request.GET.get('errdesc','')
    sign = request.GET.get('sign','')
    
    app_key = ''
    user_type = 0

    try:
        app_key = pay_channel.get_config_value('app_key','XxRyX5jJhhwJSSXx')
        user_type = pay_channel.get_config_value('user_type',21)
    except Exception,e:
        print('confirm changwan has error0',e)
    
    sign_str = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s'%(server_id,callbackInfo,open_id,order_id,order_status,pay_type,amount,remark,pay_time,app_key)
    print(sign_str)
    sign_str = md5(sign_str)
    print(sign_str,sign)
    
    pay_amount = 0
    the_server_id = 0

    if sign==sign_str:
        try:
            if server_id!='':
                the_server_id = int(server_id)
            else:
                the_server_id = int(callbackInfo)
        
            if int(order_status)==1:
                pay_amount = float(amount)/100
            else:
                pay_amount = 0
            result_msg =  '1'
        except Exception,e:
            print('confirm youai has error',e)
    else:
        result_msg = '102'
    
#    print({'server_id':the_server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg})
    return {'server_id':the_server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        

        
        
        
        
        
        
        
        
        