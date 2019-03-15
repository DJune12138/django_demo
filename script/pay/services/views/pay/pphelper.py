# -*- coding: utf-8 -*-
#已测  POST  http://127.0.0.1:8002/service/confirm/pphelper?order_id=120507224627804959449D&billno=14_14680065_252_12&account=123123&amount=10&status=0&app_id=1&uuid=1&zone=1&roleid=1&sign=88af229c83a14a6b093ecbfd950580b1
from services.views import md5

def confirm_pphelper_get_link_id(request):
    return ''
    
def confirm_pphelper(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','310bb9c0c89f3b5cf9f421d0691c59e0')
    
    pay_status = 'fail'
    order_id = request.POST.get('order_id','')
    query_id = request.POST.get('billno','')
    account = request.POST.get('account','')
    amount = request.POST.get('amount','')
    status = request.POST.get('status','')
    app_id = request.POST.get('app_id','')
    
    uuid = request.POST.get('uuid','')
    zone = request.POST.get('zone','')
    roleid = request.POST.get('roleid','')
    sign = request.POST.get('sign','')

    sign_str = md5('%s|%s|%s|%s|%s|%s|%s|%s|%s'%(order_id,query_id,account,status,app_id,uuid,zone,roleid,app_key))
    pay_amount = 0
    server_id,player_id,pay_type = (0,0,0)
    try:
        print sign_str
        if sign == sign_str and query_id != '':
            server_id,player_id,pay_type,roleid = query_id.split('_')
            
            server_id = int(server_id)
            player_id = int(player_id)
            
            if status == '0':
                pay_amount = float(amount)
   
            pay_status = 'success'
        
    except Exception,e:
        print('confirm pphelper has error:%s'%e)


    return {'server_id':server_id,'player_id':player_id,'query_id':query_id,'pay_type':pay_type,'order_id':order_id,'amount':pay_amount,'result_msg':pay_status}

