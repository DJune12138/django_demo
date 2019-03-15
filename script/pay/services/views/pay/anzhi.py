# -*- coding: utf-8 -*-
from services.views import md5
import base64

def confirm_anzhi_get_link_id(request):
    return request.GET.get('payType', '')

def confirm_anzhi(request,pay_channel={}):
    app_id = pay_channel.get_config_value('app_id', 'Q7e0IzD391IFYi4mauITNkX5')
    app_key = pay_channel.get_config_value('app_key', 'F02MvdK92yN3z11zkHwGD94V')
    
    pay_amount = request.POST.get('amount', 0)
    orderId = request.POST.get('orderId', '')#安智平台订单
    payResult = request.POST.get('payResult', -1)
    ext = request.POST.get('ext', '')
    msg = request.POST.get('msg', '')
    signStr = request.POST.get('signStr', '')
    
    server_sign = '%s%s%s%s%s%s%s' % (app_id, pay_amount, orderId, payResult, ext, msg, app_key)
    print server_sign
    server_sign = md5(server_sign)
    server_sign = server_sign.upper()
    print (signStr, server_sign)
    
    orderid = ''
    amount = 0
    remark = ''
    result_code = ''
    server_id = 0
    player_id = 0
    if signStr == server_sign:
        try:
            result_code = 'success'
            orderid = orderId
            ext = base64.decodestring(ext)
            print 'ext is ::::::::::', ext
            server_id, player_id = ext.split('_')
            server_id = int(server_id)
            player_id = int(player_id)
            payResult = int(payResult)
            if 200 == payResult:
                amount = float(pay_amount)
        except Exception, ex:
            result_code = 'internal error'
            print 'anzhi error'
            print ex
    else:
        remark = 'sign error'
        result_code = 'sign error'
    
    
    return {'server_id':server_id, 'player_id':player_id ,'order_id':orderid,'amount':amount,'remark':remark,'result_msg':result_code}


    
