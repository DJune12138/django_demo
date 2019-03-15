# -*- coding: utf-8 -*-
#台湾-松岗
from services.views.pay import confirm
from services.views import md5
from services.http import http_post
from django.http import HttpResponseRedirect, HttpResponse
import urllib,urllib2
import traceback

'''
廠商編號--13121601
MD5 Key： sx#Ud#S4YR6t5P6*st
MD5 Key (Testing Stage)： jqvX$vV4-U6k5S6zjk


'''
pay_type = 75
def confirm_songgang_get_link_id(request):
    return request.POST.get('itemCode','')
    
    
    
def convert_songgong_response(response_str):
    '''TRANSACTIONID=XXXXXXX,TRANSACTIONSTATUS=XXXXX,TRANSACTIONMSG=XXXXXXXX 
       TRANSACTIONSTATUS=0 交易成功
    '''
    _r = {}
    try:
        for kv in  response_str.split(','):
            k,v = kv.split('=',2)
            _r[k.strip()] = v
    except:
        print response_str
        traceback.print_exc()
    return _r
    
def query_songgang(request):
    '''客户端给的充值成功消息
    /service/query/songgang?orderId=502_526385358_1404200092771&transId=PPK237301685&itemChange=fal
se&payName=%E9%87%91%E5%B8%81&amount=60.0&paymentID=38&serverId=502&playerId=526385358
    CHECKCODE規則：MD5(TransactionKey+”*”+SHOPID+”*”+ORDERID+”*”+TransactionKey)
    '''
    check_url = 'http://www.pay168.com.tw/purepay/online/CheckTransStatus.aspx'
    app_key = 'sx#Ud#S4YR6t5P6*st'
    request.POST._mutable = True #
    request.GET._mutable = True  #可以是使用reuqest.GET.setlist('key',value)方法
    SHOPID = 13121601
    rq = request.REQUEST
    
    ORDERID = rq.get('orderId','')
    transId = rq.get('transId','')
    itemChange = rq.get('itemChange','')
    payName = rq.get('payName','')
    amount = rq.get('amount','')
    paymentID = rq.get('paymentID','')
    serverId = rq.get('serverId','')
    playerId = rq.get('playerId','')
    
    CHECKCODE = md5('%s*%s*%s*%s'%(app_key,SHOPID,ORDERID,app_key))
    query_data = 'SHOPID=%s&ORDERID=%s&CHECKCODE=%s' % (SHOPID,ORDERID,CHECKCODE)
    check_url = '%s?%s' % (check_url,query_data)
    response = http_post(check_url,query_data)
    r = convert_songgong_response(response)
    print r
    if r.get('TRANSACTIONSTATUS','') == '0' and serverId and playerId :#设置回调的参数
        transactionID = r.get('TRANSACTIONID','')
        
        request.POST.setlist('payName',[payName])
        request.POST.setlist('payDesc',['%s_%s' % (serverId,playerId)])
        request.POST.setlist('itemCode',[''])
        request.POST.setlist('money',[amount])
        request.POST.setlist('orderId',[ORDERID])
        request.POST.setlist('transactionID',[transactionID])
        request.POST.setlist('itemChange',[itemChange])
        sign = md5('%s%s%s' % (transactionID,app_key,amount))
        request.POST.setlist('Sig',[sign])
        return confirm(request,'songgang')
    return HttpResponse('0')

def confirm_songgang(request,pay_channel):
    app_key = pay_channel.get_config_value('app_key','')
    user_type = pay_channel.get_config_value('user_type', 114)

    rq = request.POST
    print rq
    payName = rq.get('payName','')
    payDesc = rq.get('payDesc','')
    itemCode = rq.get('itemCode','')
    money = rq.get('money','')
    orderId = rq.get('orderId','')
    transactionID = rq.get('transactionID','')
    itemChange = rq.get('itemChange','')
    Sig = rq.get('Sig','').encode('utf-8')
    
    sign = md5('%s%s%s' % (transactionID,app_key,money))
    order_id = ''
    pay_amount = 0
    remark = ''
    result_msg = '0|Fail'
    server_id = player_id = ''
    
    try:
        if sign == Sig:
            order_id = transactionID
            pay_amount = float(money)
            server_id,player_id = payDesc.split('_')[:2]
            server_id = int(server_id)
            player_id = int(player_id)
            remark = payName
            result_msg = '1|Success'
        else:
            result_msg = '0|Sgin Error'
    except Exception,e:
        print('confirm songgang has an error:',e)

    _r = {'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        
    print _r
    return  _r




'''
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