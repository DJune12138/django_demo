#coding=utf-8

import hashlib, json, urllib


def md5(s):
    signStr=hashlib.md5()
    signStr.update(s.encode('utf-8'))
    return signStr.hexdigest()


def confirm_a9133_get_link_id(request):
    return ''


def confirm_a9133(request, pay_channel):
    rg = request.GET
    serverId = rg.get('serverId','')
    callbackInfo = rg.get('callbackInfo','')
    openId = rg.get('openId','')
    orderId = rg.get('orderId','')
    orderStatus = rg.get('orderStatus','')
    amount = rg.get('amount','')
    remark = rg.get('remark','')
    sign = rg.get('sign','')
    payType = rg.get('payType','')

    app_server_key = pay_channel.get_config_value('app_server_key', '297afbd4810774a6ba417216ca83fecb')

    order_id = ''
    server_id = link_id = 0
    player_id = 0
    #amount = 0
    #remark = ''
    result_msg = ''

    sign_str = '%s'*9 %(serverId,callbackInfo,openId,orderId,orderStatus,payType,amount,remark,app_server_key)
    sign_str = md5(sign_str)
    print "#"*40
    print (sign,sign_str)

    try:
        if sign_str == sign:
            order_id = orderId
            amount = float(amount)
            result_msg = 'success'
            s_p_l = callbackInfo.split('_')
            server_id = int(s_p_l[0])
            player_id = int(s_p_l[1])
            link_id = '_'.join(s_p_l[2:-1])
            remark = orderStatus

        else:
            result_msg = 'fail'
            print result_msg

    except Exception,e:
        print e

    _r =  {"link_id":link_id, "server_id":server_id, "player_id":player_id, "order_id":order_id,"amount":amount, "remark":remark, "result_msg":result_msg}
    print _r
    return _r






