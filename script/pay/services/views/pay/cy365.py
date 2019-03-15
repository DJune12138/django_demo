# -*- coding: utf-8 -*-
#禅游365充值

from services.views import md5


def confirm_cy365_get_link_id(request):
    return ''


def confirm_cy365(request,pay_channel={}):
    Appid = 31020   
    channel = '365you.fytx'
    app_key = pay_channel.get_config_value('app_key','5f59e50d07465cc328132f91bc67f486')
    user_type = pay_channel.get_config_value('user_type',103)
    keys = ['OrderId','GameId','UserId','Money','GoodsId','GoodsCount','Note','PayStatus','sign']
    OrderId,GameId,UserId,Money,GoodsId,GoodsCount,Note,PayStatus,sign = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]

    sign_str = ('%s' * 7 )%(OrderId,GameId,UserId,Money,GoodsId,GoodsCount,app_key)
    sign_str = md5(sign_str)
    print '-' * 40
    print [ OrderId,GameId,UserId,Money,GoodsId,GoodsCount,Note,PayStatus,sign ]
    print (sign_str,sign)
    account = msg = orderid = ''
    pay_amount = 0
    server_id = player_id = 0
    if sign.encode('utf-8') == sign_str:
        try:
            if int(PayStatus) == 1:
                pay_amount = float(Money)
                account = UserId
                orderid = OrderId
                server_id,player_id = [ int(i) for i in Note.split('_')]
                result_msg =  'success'
        except Exception,e:
            result_msg = 'error'
            print('confirm cy365 has error',e)
    else:
        result_msg = 'sign_error'
    #'user_type':user_type,'open_id':account,
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r
