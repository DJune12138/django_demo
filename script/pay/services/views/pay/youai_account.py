# -*- coding: utf-8 -*-


import urllib,hashlib
import traceback

def confirm_youai_account_get_link_id(request):
    return ''

def urldecode(rq,key):
    return urllib.unquote_plus(rq.get(key,'').encode('utf-8'))

def md5(sign_str):
    return hashlib.new('md5',sign_str).hexdigest()

def confirm_youai_account(request,pay_channel):
    result_msg = 'error'
    print request.REQUEST
    rq = request.REQUEST

    serverId = urldecode(rq,'serverId')#游戏服务器ID
    callbackInfo = urldecode(rq,'callbackInfo')#CP透传参数
    openId = urldecode(rq,'openId')#平台账号ID
    orderId = urldecode(rq,'orderId')#平台订单号
    orderStatus = urldecode(rq,'orderStatus')#订单状态
    amount = urldecode(rq,'amount')#平台币
    remark = urldecode(rq,'remark')#备注
    payType = urldecode(rq,'payType')#充值通标识
    sign = urldecode(rq,'sign')#验证串
    
    the_server_id = player_id = pay_amount = 0
    link_id = ''
    try:
        app_server_key = pay_channel.get_config_value('app_server_key','1996d389785c2ea8adf76b8fc8bb83d7').encode('utf-8')

        sign_str = '%s'*9 %\
        (serverId,callbackInfo,openId,orderId ,orderStatus,payType,amount,remark,app_server_key)
        my_sign = md5(sign_str)
        
        print (sign_str,my_sign,app_server_key)
        if sign==my_sign:
            if int(orderStatus)==1:
                the_server_id = int(serverId)
                p_l = callbackInfo.split('_')
                link_id = int(p_l[-1])
                player_id = int(p_l[0])
                pay_amount = float(amount) / 100
                result_msg = 'success'

        else:
            result_msg = 'errorSign'
    except Exception,e:
        traceback.print_exc()
        print('confirm youai_account has error',e)
        
    return {'server_id':the_server_id,'player_id':player_id,'link_id':link_id,'order_id':orderId,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

        
        
        
        
        
        
        
        
        