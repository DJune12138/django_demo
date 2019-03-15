# -*- coding: utf-8 -*-
import hmac

def confirm_yinlian_get_link_id(request):
    return ''

def confirm_yinlian(request, pay_channel={}):
     
    app_key = pay_channel.get_config_value('app_key', '')
    
    transType = request.POST.get('transType', '')
    merchantId = request.POST.get('merchantId', '')
    merchantOrderId = request.POST.get('merchantOrderId', '')
    merchantOrderAmt = request.POST.get('merchantOrderAmt', '')
    settleDate = request.POST.get('settleDate', '')
    setlAmt = request.POST.get('setlAmt', '')
    setlCurrency = request.POST.get('setlCurrency', '')
    converRate = request.POST.get('converRate', '')
    cupsQid = request.POST.get('cupsQid', '')
    cupsTraceNum = request.POST.get('cupsTraceNum', '')
    cupsTraceTime = request.POST.get('cupsTraceTime', '')
    cupsRespCode = request.POST.get('cupsRespCode', '')
    cupsRespDesc = request.POST.get('cupsRespDesc', '')
    respCode = request.POST.get('respCode', '')
    MerchantDesc = request.POST.get('MerchantDesc', '')
    sign = request.POST.get('sign', '')
    
    server_sign = ''
    
    mac=hmac.new(app_key)
    mac.update(server_sign)
    server_sign = mac.hexdigest()
    
   
    server_sign = '%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % (
                                                    transType, merchantId, merchantOrderId, merchantOrderAmt, settleDate,
                                                    setlAmt, setlCurrency, converRate, cupsQid, cupsTraceNum, cupsTraceTime,
                                                    cupsRespCode, cupsRespDesc, respCode, MerchantDesc)
    
    print server_sign
    
    mac=hmac.new(app_key)
    mac.update(server_sign)
    server_sign = mac.hexdigest()
    
    print (sign, server_sign)
    
    remark = ''
    query_id = ''
    pay_amount = 0
    result_code = 'failure'
    if sign == server_sign:
        if '01' ==  transType:
            if '00' == cupsRespCode:
                query_id = MerchantDesc
                order_id = merchantOrderId
                print 'setlCurrency:', setlCurrency
                try:
                    pay_amount = float(setlAmt) / 100
                    result_code = 'success'
                except Exception, ex:
                    remark = '内部错误'
                    print 'yin lian error: ', setlAmt , ex
                
            else:
                remark = '订单状态,失败 ' 
        else:
            remark = '消费撤销,或退货'
    else:
        remark = 'sign error'
            
    
    return {'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_code}


