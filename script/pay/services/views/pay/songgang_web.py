# -*- coding: utf-8 -*-
#台湾-松岗-web
from services.views.pay import confirm
from services.views import md5 
from services.http import http_post 
from django.http import HttpResponseRedirect, HttpResponse
import urllib,urllib2
import traceback

def confirm_songgang_web_get_link_id(request):
    return request.POST.get('itemCode','')

def confirm_songgang_web(request,pay_channel):
    app_key = pay_channel.get_config_value('app_key','Zo#@dwk@s p%')
    user_type = pay_channel.get_config_value('user_type', 114)

    rq = request.REQUEST
    print rq
    gameid = rq.get('gameid','')
    orderid  = rq.get('orderid','')
    uid = rq.get('uid','')
    serverid = rq.get('serverid','')
    amount = rq.get('amount','')
    sig = rq.get('sig','')  #md5(orderid + uid + serverid + amount + key)
    sign_str = '%s%s%s%s%s' % (orderid,uid,serverid,amount,app_key)
    sign = md5(sign_str)
    print (sign,sig,sign_str)
    order_id = ''
    pay_amount = 0
    remark = ''
    result_msg = 'E999'
    server_id = player_id = openid =''
    
    try:
        if sign.encode('utf-8') == sig:
            order_id = orderid
            pay_amount = float(amount)
            server_id = int(serverid)
            openid = uid
            remark = gameid
            result_msg = 'E000'
        else:
            result_msg = 'E007'
    except Exception,e:
        result_msg = 'E999'
        print('confirm songgang_web has an error:',e)

    _r = {'server_id':server_id,'user_type':user_type,'open_id':openid,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg,'link_id':'web'}
    print _r
    return _r



'''
廠商端處理完成回應內容
E000    交易成功
E001    廠商端登入遊戲的帳號錯誤
E002    遊戲伺服器代碼錯誤
E003    儲值的遊戲幣數量錯誤
E004    此筆交易代碼已儲值成功
E005    IP位置不在服務範圍內
E006    遊戲角色資料錯誤
E007    Sig驗證失敗
E999    其它交易失敗
'''