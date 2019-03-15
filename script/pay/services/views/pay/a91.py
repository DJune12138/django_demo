# -*- coding: utf-8 -*-
#已测  GET  http://127.0.0.1:8002/service/confirm/a91?Act=123&ProductName=123&ConsumeStreamId=120507224627804959449D&CooOrderSerial=120507224627804959449D&Uin=123&GoodsId=1&GoodsInfo=123&GoodsCount=1&OriginalMoney=100&OrderMoney=2&Note=111&PayStatus=1&CreateTime=2012-08-01&Sign=e915fde079009d03e38a639c609a6b8c
from services.views import md5

def pay_a91(the_action , pay_channel = {} , host_ip='service.fytxonline.com'):
    return (1,the_action.query_id)

def confirm_a91_get_link_id(request):
    return ''

def confirm_a91(request,pay_channel={}):
    result_msg = ''
     
    
    app_id = int(pay_channel.get_config_value('app_id', 108263))
    app_key = pay_channel.get_config_value('app_key','d4e37e979a598b60cbaf3524d6b832cf2a15a70229f090c6')

    Act = request.GET.get('Act','')
    ProductName = request.GET.get('ProductName','')
    ConsumeStreamId = request.GET.get('ConsumeStreamId','')
    CooOrderSerial = request.GET.get('CooOrderSerial','')
    Uin = request.GET.get('Uin','')
    GoodsId = request.GET.get('GoodsId','')
    GoodsInfo = request.GET.get('GoodsInfo','')
    GoodsCount = request.GET.get('GoodsCount','')
    OriginalMoney = request.GET.get('OriginalMoney','')
    OrderMoney = request.GET.get('OrderMoney','')
    Note = request.GET.get('Note','')
    PayStatus = request.GET.get('PayStatus','')
    CreateTime = request.GET.get('CreateTime','')
    Sign = request.GET.get('Sign','')
    
    result_code = 0
    
    query_id = ''
    order_id = ''
    remark = ''
    amount = 0
    server_id = 0
    player_id = 0
    
    try:
        sign_str = '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s'%(app_id,Act,ProductName,ConsumeStreamId,CooOrderSerial,Uin,GoodsId,GoodsInfo,GoodsCount,OriginalMoney,OrderMoney,Note,PayStatus,CreateTime,app_key)
        sign_str = md5(sign_str)
        print 'sign_str', sign_str
        print 'Sign', Sign
        #print(sign_str,Sign)
        result_code = 0
        if sign_str == Sign: 
            
            if PayStatus == '1':
                amount = float(OrderMoney)
                remark = GoodsInfo
                query_id = CooOrderSerial
                order_id = ConsumeStreamId
                server_id,player_id = CooOrderSerial.split('_')[:2]
                server_id = int(server_id)
                player_id = int(player_id)
            else:
                amount = 0 
                remark = Note
            result_code = 1
            result_msg = 'success'
        else:
            result_code = 5
            #签名错误
         
    except Exception,e:
        print('confirm 91 error:',e)
        result_msg = e
        result_code = 0

    result_msg = '{"ErrorCode":"%s","ErrorDesc":"%s"}' % (result_code, result_msg)
    
    
    return {'order_id':order_id,'query_id':query_id,'server_id':server_id,'player_id':player_id,'amount':amount,'remark':remark,'result_msg':result_msg}






#def confirm_91(request):
#    app_id = 108263
#    app_key = 'd4e37e979a598b60cbaf3524d6b832cf2a15a70229f090c6'
#    AppId = request.GET.get('AppId','')
#    Act = request.GET.get('Act','')
#    ProductName = request.GET.get('ProductName','')
#    ConsumeStreamId = request.GET.get('ConsumeStreamId','')
#    CooOrderSerial = request.GET.get('CooOrderSerial','')
#    Uin = request.GET.get('Uin','')
#    GoodsId = request.GET.get('GoodsId','')
#    GoodsInfo = request.GET.get('GoodsInfo','')
#    GoodsCount = request.GET.get('GoodsCount','')
#    OriginalMoney = request.GET.get('OriginalMoney','')
#    OrderMoney = request.GET.get('OrderMoney','')
#    Note = request.GET.get('Note','')
#    PayStatus = request.GET.get('PayStatus','')
#    CreateTime = request.GET.get('CreateTime','')
#    Sign = request.GET.get('Sign','')
#    
#    try:
##        if True:
#        list_pay = PayAction.objects.using('write').filter(query_id=CooOrderSerial)
#        if len(list_pay)>0:
#            the_action = list_pay[0]
#
#            if abs(the_action.pay_status) < 2:
#                pay_channel = PayChannel.objects.using('read').get(id=the_action.pay_type)
#                if pay_channel.pay_config!='':
#                    pay_config = json.loads(pay_channel.pay_config)
#                    app_id = pay_config.get('app_id',0)
#                    app_key = pay_config.get('app_key','')
#                
#                sign_str = '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s'%(app_id,Act,ProductName,ConsumeStreamId,CooOrderSerial,Uin,GoodsId,GoodsInfo,GoodsCount,OriginalMoney,OrderMoney,Note,PayStatus,CreateTime,app_key)
#                sign_str = md5(sign_str)
#                #print(sign_str,Sign)
#                result_code = 0
#                if sign_str == Sign:
#                    the_action.pay_type = pay_channel.id
#                    the_action.order_id = ConsumeStreamId
#                    if PayStatus == '1':
#                        the_action.pay_amount = float(OrderMoney)
#                        the_action.pay_gold = the_action.pay_amount * pay_channel.exchange_rate
#                        the_action.pay_status = 2
#                        the_action.remark = '{"GoodsId":%d,"GoodsInfo":"%s","GoodsCount":%d}'%(int(GoodsId),GoodsInfo,int(GoodsCount))
#                    else:
#                        the_action.pay_amount = 0
#                        the_action.pay_gold = 0
#                        the_action.pay_status = -2
#                        the_action.remark = Note
#                    the_action.last_time = datetime.datetime.now()
#                    the_action.save(using='write')
#                    result_code = 1
#                    result_msg = 'success'
#                else:
#                    result_code = 5
#                    #签名错误
#            else:
#                #repeat order
#                result_code = 2
#                result_msg = 'success'
#        else:
#            result_code = 4
#            result_msg = 'order error'
#    except Exception,e:
#        print('confirm 91 error:',e)
#        result_msg = e
#        result_code = 0
#
#
#    return render_to_response('pay/pay_result_91.html',locals()) 