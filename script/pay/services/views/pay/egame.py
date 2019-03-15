# -*- coding: utf-8 -*-
from services.views import md5
from services.models import PayAction
 

def confirm_egame_get_link_id(request):
    return ''

def confirm_egame(request, pay_channel={}):
    #app_id = pay_channel.get_config_value('app_id', '')
    
    serialno = request.GET.get('serialno', '')
    resultCode = request.GET.get('resultCode', '')
    resultMsg = request.GET.get('resultMsg', '')
    gameUserId = request.GET.get('gameUserId', '')
    gameGold = request.GET.get('gameGold', '')#单位元
    validatecode = request.GET.get('validatecode', '')#MD5(serialNo + gameUserId)
    payType = request.GET.get('payType', '')
    
    gameId = request.GET.get("gameId", '')
    
    requestTime = request.GET.get('requestTime', '')#请求时间
    responseTime = request.GET.get('responseTime', '')#反馈时间
    
    
    order_id = ''
    ip = ''
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):  
        ip =  request.META['HTTP_X_FORWARDED_FOR']  
    else:  
        ip = request.META['REMOTE_ADDR']
    
    remove_ip = pay_channel.get_config_value('ip', '202.102.39.')
    server_sign = md5('%s%s' % (serialno, gameUserId))
    print (validatecode, server_sign)
    
    remark = ''
    result_msg = ''
    pay_amount = 0
    server_id = 0
    player_id = 0
    
    if 0 == ip.find(remove_ip):
        if validatecode == server_sign:
            result_msg = serialno
            if str(resultCode) == "120":
                pay_amount = float(gameGold)
                the_action = PayAction.objects.get(id = int(gameUserId))
                if None != the_action:
                    server_id = the_action.server_id
                    player_id = the_action.pay_user
                    order_id = serialno
                else:
                    remark = 'the_action is none, id:%s' % gameUserId
            else:
                remark = '充值失败'
        else:
            remark = '签名错误'
    else:
        remark = '违法ip'
        
    return {"server_id":server_id, "player_id": player_id, "order_id":order_id ,"amount": pay_amount, "result_msg":result_msg,"remark":remark ,"header":{"serialno":serialno}}

    