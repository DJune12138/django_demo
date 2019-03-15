# -*- coding: utf-8 -*-
#已测   GET  http://127.0.0.1:8002/service/confirm/ledou?user_type=6&extraInfo=14&orderId=120507224627804959449D&openid=14680065&actualAmount=20&success=0&msg=msg&sign=9ddee7b220304f259b01bd99180c8f6c
from services.views import md5


def confirm_ledou_get_link_id(request):
    return ''


def confirm_ledou(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','33c0604d8c4625a00c46')
    user_type = pay_channel.get_config_value('user_type',6)
    
    custom = request.GET.get('extraInfo','')
    order_id = request.GET.get('orderId','')
    open_id = request.GET.get('openid','')
    post_amount = request.GET.get('amount','')
    pay_amount = request.GET.get('actualAmount','')
    result = request.GET.get('success','')
    remark = request.GET.get('msg','')
    sign = request.GET.get('sign','')

    sign_str = u'orderId=%s&openid=%s&amount=%s&actualAmount=%s&success=%s&secret=%s'%(order_id,open_id,post_amount,pay_amount,result,app_key)
    sign_str = md5(sign_str)
    result_msg = 'failure'
    
    server_id = 0
    print(sign_str)
    amount = 0
    if sign==sign_str:
        try:
            if int(result)==0:
                amount = float(pay_amount)
            server_id = int(custom.replace('&',''))
            result_msg =  'ok'
        except Exception,e:
            print('confirm ledou has error',e)
    else:
        pay_amount = 0
        result_msg = 'sign_error'
        
    return {'server_id':server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg}



