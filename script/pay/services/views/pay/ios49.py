# -*- coding: utf-8 -*-

from services.views import md5


def confirm_ios49_get_link_id(request):
    return ''


def confirm_ios49(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','115bea0008adecd35dc87d460f038dbf')
    keys = ['uid','amount','orderid','serverid','extrainfo','sign']
    uid,amount,orderid,serverid,extrainfo,sign = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]

    sign_str = u'%s%s%s%s%s%s'%(orderid,uid,serverid,amount,extrainfo,app_key)
    sign_str = md5(sign_str)
    print '-' * 40
    print [ uid,amount,orderid,serverid,extrainfo,sign ]
    print (sign_str,sign)
    account = msg = ''
    pay_amount = 0
    server_id = player_id = 0
    if sign.encode('utf-8') == sign_str:
        try:
            pay_amount = float(amount)
            account = uid
            server_id,player_id = [ int(i) for i in extrainfo.split('_')]
            result_msg =  orderid #成功：CP方订单ID
        except Exception,e:
            result_msg = 'server_id,player_id  error'
            print('confirm ios49 has error',e)
    else:
        amount = 0
        result_msg = '-1 sign_error'
       
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r
'''
回调参数：uid=49APP用户UID&amount=金额（RMB，INT整数）&orderid=订单号&serverid=游戏服务器ID&extrainfo=扩展参数&sign=签名

sign签名组合
订单号 + 用户UID + 服务器ID + 金额 + 扩展参数 + APPKEY

请求方式：HTTP GET
'''
