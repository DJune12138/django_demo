# -*- coding: utf-8 -*-
from services.views import md5

def confirm_tapjoy_get_link_id(request):
    return ''

def confirm_tapjoy(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','')
    
    #{id}:#{snuid}:#{currency}:#{secret_key}
    _id = request.GET.get('id', '')
    snuid = request.GET.get('snuid', '')
    currency = request.GET.get('currency', '')
    mac_address = request.GET.get('mac_address', '')
    verifier = request.GET.get('verifier', '')
    
    server_sign = '%s:%s:%s:%s' % (_id, snuid, currency, app_key)
    
    print server_sign
    server_sign = md5(server_sign)
    print (verifier, server_sign)
    
    pay_amount = 0
    server_id = 0
    player_id = 0
    order_id = ''
    remark = mac_address
    pay_status = 'success'
    
    if verifier == server_sign:
        try:
            currency = float(currency)
            if currency > 0:
                pay_amount = currency
                server_id, player_id = snuid.split('_')
                order_id = _id
        except Exception, ex:
            print ex
    
    
    return {'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':pay_status}