# -*- coding: utf-8 -*-
#已测  POST http://127.0.0.1:8002/service/confirm/mrp?tradetype=1&tradeid=120507224627804959449D&realamount=10&complatetime=2012-08-01&tradecode=14_14680065_12&tradetitle=hello&sign=408e936ff82246ee229df9fc65bfcb15
from services.views import md5


def confirm_mrp_get_link_id(request):
    return request.POST.get('tradetype','')
    
#冒泡充值通知    
def confirm_mrp(request,pay_channel={}):
#    app_id = 6000250
    app_key = pay_channel.get_config_value('app_key','1560ca8d1a098f416e4b')
    
    pay_status = 'false'
    order_id = request.POST.get('tradeid','')
    amount = request.POST.get('realamount','')
    pay_result = request.POST.get('tradestatus','')
    pay_time = request.POST.get('complatetime','')
    pay_type = request.POST.get('tradetype','')
    query_id = request.POST.get('tradecode','')
    remark = request.POST.get('tradetitle','')
#    print(remark)
    sign = request.POST.get('sign','')
    
    sign_str = u'complatetime=%s&realamount=%s&tradecode=%s&tradeid=%s&tradestatus=%s&tradetitle=%s&tradetype=%s&save=%s'%(pay_time,amount,query_id,order_id,pay_result,remark,pay_type,app_key)
#    print(sign_str)
    sign_str = md5(sign_str)
    print(sign_str,sign);
    
    pay_amount = 0
    server_id = 0
    player_id = 0
    
    if sign == sign_str:
        server_id,player_id,sign = query_id.split('_')
        
        server_id = int(server_id)
        player_id = int(player_id)
        
        if pay_result == '1':
            pay_amount = float(amount) / 100

        pay_status = 'true'
    else:
        pay_status = 'error sign'
            
    return {'server_id':server_id,'player_id':player_id,'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':pay_status}
