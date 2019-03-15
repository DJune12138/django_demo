# -*- coding: utf-8 -*-

from services.views import md5


def confirm_duoyou_get_link_id(request):
    return ''


def confirm_duoyou(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','fengyunduogame')
    keys = ['UserID','UserAccount','PayChannelID','PayChannelName','price','OrderID','PayCode','PayResultMeg','Hash','ext_param']
    UserID,UserAccount,PayChannelID,PayChannelName,price,OrderID,PayCode,PayResultMeg,Hash,ext_param = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]

    sign_str = u'UserID=%s&PayChannelID=%s&price=%s&OrderID=%s&PayCode=%s&appkey=%s' \
    %(UserID,PayChannelID,price,OrderID,PayCode,app_key)
    sign_str = md5(sign_str)
    print '-' * 40
    print [ UserID,UserAccount,PayChannelID,PayChannelName,price,OrderID,PayCode,PayResultMeg,Hash,ext_param ]
    print (sign_str,Hash)
    msg = orderid = ''
    pay_amount = 0
    server_id = player_id = 0
    result_msg = 'error'
    if Hash.encode('utf-8')==sign_str:
        try:
            if int(PayCode)==9999:
                pay_amount = float(price)
                orderid = OrderID
                player_id,server_id = [ int(i) for i in ext_param.split('_')]
                player_id = int(player_id)
                server_id = int(server_id)
                result_msg =  'success'  #成功：CP方订单ID
            msg = PayResultMeg
                
        except Exception,e:
            print('confirm_duoyou',e)
    else:
        result_msg = 'sign_error'
       
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r
'''
回调参数：uid=49APP用户UID&amount=金额（RMB，INT整数）&orderid=订单号&serverid=游戏服务器ID&extrainfo=扩展参数&sign=签名

sign签名组合
订单号 + 用户UID + 服务器ID + 金额 + 扩展参数 + APPKEY

请求方式：HTTP GET
'''
