# -*- coding: utf-8 -*-
from services.views import md5
import json

def confirm_simeitong_v5_get_link_id(request):
    return ''
    
    
def confirm_simeitong_v5(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key', '')
    
    post_data = request.raw_post_data
    post_data = json.loads(post_data)
    
    exorderno = post_data.get('exorderno', '')
    transid = post_data.get('transid', '')
    waresid = post_data.get('waresid', '')
    chargepoint = post_data.get('chargepoint', '')
    feetype = post_data.get('feetype', '')
    money = float(post_data.get('money', 0))
    count = post_data.get('count', '')
    result = int(post_data.get('result', 1))
    transtype = post_data.get('transtype', '')
    transtime = post_data.get('transtime' , '')
    sign = post_data.get('sign', '')
    
    # exorderno + transid + waresid + chargepoint + feetype + money + count + result + transtype + transtime + cpkey
    server_sign = '%s%s%s%s%s%s%s%s%s%s%s' % (exorderno, transid, waresid, chargepoint, feetype, money, count, result, transtype, transtime, app_key)
    server_sign = md5(server_sign)
    
    print (sign, server_sign)
    
    amount = 0
    orderid = ''
    remark = ''
    result_code = 'error'
    if sign == server_sign:
        query_id = exorderno
        orderid = transid
        result_code = 'SUCCESS'
        if 0 == result and 0 < money:
            amount = money / 100
            remark = 'SUCCESS'
    else:
        remark = 'sign error'
    
    
    return {'query_id':query_id,'order_id':orderid,'amount':amount,'remark':remark,'result_msg':result_code}


