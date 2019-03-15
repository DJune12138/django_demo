# -*- coding: utf-8 -*-

from services.views import md5


def confirm_lemon_get_link_id(request):
    return request.GET.get('item',request.POST.get('item',''))


def confirm_lemon(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','d72fc4301b5b851d')
    keys = ['appid','serverid','uid','amount','orderid','item','actual_amount','payext','signature']
    appid,serverid,uid,amount,orderid,item,actual_amount,payext,signature = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]

    sign_str = u'%s%s%s%s%s%s%s%s%s'%(appid,serverid,uid,amount,orderid,item,actual_amount,payext,app_key)
    sign_str = md5(sign_str)
    print '-' * 40
    print [ appid,serverid,uid,amount,orderid,item,actual_amount,payext,signature ]
    print 'item %s' % item
    print (sign_str,signature)
    account = msg = ''
    pay_amount = 0
    server_id = player_id = openid = 0
    result_msg = '{"result":1,"msg":"Fail"}'
    user_type = int(pay_channel.get_config_value('user_type',84))
    if signature.encode('utf-8') == sign_str:
        try:
            
            
            if item:
                msg = '%s,%s' % (actual_amount,amount)
                pay_amount = 1
            else:
                pay_amount = float(actual_amount)
            server_id = int(serverid)
            openid = int(uid)
            result_msg =  '{"result":0,"msg":"success"}' #成功：CP方订单ID
        except Exception,e:
            result_msg = 'server_id,player_id  error'
            print('confirm lemon has error',e)
    else:
        result_msg = '{"result":-1,"msg":"sign_error"}'
       
    _r = {'server_id':server_id,'user_type':user_type,'open_id':openid,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r


