# -*- coding: utf-8 -*-
from services.views import md5

def confirm_taiwanmimigigi_get_link_id(request):
    return ''

def confirm_taiwanmimigigi(request,pay_channel={}):
    
    g = lambda x,y:request.POST.get(x,request.GET.get(x,y))
    app_key = pay_channel.get_config_value('app_key','woxianzaihaibuzhidao')
    
    Result = g('result', '')
    Imei = g('imei', '')
    uid = g('uid', '')
    error_msg = g('error_msg', '')
    orderid = g('orderId', '')
    paytype = g('paytype', '')
    price = g('price', '')
    timestamp = g('timeStamp', '')
    token = g('token', '')
    
#    print 'Result:%s'% Result
#    print 'app_key:%s'% app_key
#    print 'uid:%s'% uid
#    print 'timestamp:%s'% timestamp
#    print 'orderid:%s'% orderid
#    print 'paytype:%s'% paytype
#    print 'price:%s'% price
#    print 'token:%s'% token
     
    sign_str = '%s%s%s%s%s%s'% (app_key, uid, timestamp, orderid, paytype, price)
#    print 'sign_str%s'% sign_str
    
    remark = ''
    result_msg = ''
    order_id = ''
    server_id = 0
    player_id = 0
    amount = 0
    
    if token == md5(sign_str):
#        print 'enter token == md5(sign_str'
        if Result == 'success':
#            print 'enter Result == success'
            try:                
                server_id = int(g('server_id', 0))
                player_id = int(g('player_id', 0))
                amount = int(price)
                order_id = orderid
                result_msg = 'Success'
                print 'player_id:%s'% player_id
                print 'server_id:%s'% server_id
            except Exception, ex:
                print 'Urecharge_Id error'
        else:
            result_msg = 'wrong ret'            
    else:
#        print 'enter sign error'
        result_msg = 'sign error'
    
    print 'enter return'
    return {'server_id':server_id,'player_id':player_id, 'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg}

