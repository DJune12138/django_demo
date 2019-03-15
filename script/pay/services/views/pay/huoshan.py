# -*- coding: utf-8 -*-
from services.views import md5


def confirm_huoshan_get_link_id(request):
    return ''
#搜狐火山
def confirm_huoshan(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','atcfqeeac6#t5titqffbhhs3')
    #for k in request.POST:
        #v = request.POST.get(k)
        #print 'key:%s value:%s' % (k, v.decode('utf-8'))
    
    #
#    merId  商户 id  String   商户在支付平台的编号 
    #pid  商品编号  String    应用平台的商品变化 
    #payMoney  支付金额  String   订单的支付金额(单位为 分) 
    #orderno  订单号  String    商户的订单号(必须保证唯一) 
    #result  支付结果  String   订单的支付结果(-1 支付失败 1 支付成功) 
    #verifyType  签名类型  String   签名类型 1为 MD5 
    #sign 
    #
    
    
    merId = request.POST.get('merId','')
    pid = request.POST.get('pid','')
    payMoney = request.POST.get('payMoney','')
    orderno = request.POST.get('orderno','')
    result = request.POST.get('result','')
    
    verifyType = request.POST.get('verifyType','')
    sign = request.POST.get('sign','')
    
    result_msg = '0'
    pay_amount = 0
    server_id = 0
    player_id = 0
    remark= ''
    
    payId = ''
    timestamp = ''
    try:
        server_id, player_id, cid, payId, timestamp = orderno.split('_')
    except Exception, ex:
        print ex
    
    sign_str = 'merId=%s&pid=%s&payMoney=%s&orderno=%s&result=%s&verifyType=%s%s' % (merId, pid, payMoney, orderno, result, verifyType, app_key)
    
    sign_str = md5(sign_str)
    print (sign_str, sign)
    
    #print sign_str
    if sign==sign_str:
        try:
            server_id = int(server_id)
            player_id = int(player_id)
            if int(result)==1:
                pay_amount = float(payMoney) / 100
    
            result_msg =  'SUCCESS'   
        except Exception,e:
            print('confirm hucn has error',e)
    else:
        result_msg = 'Sign error'
    
    return {'server_id':server_id,'player_id':player_id,'order_id':orderno,'amount':pay_amount,'remark':remark,'result_msg':result_msg}



