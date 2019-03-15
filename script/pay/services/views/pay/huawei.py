# -*- coding: utf-8 -*-
def confirm_huawei_get_link_id(request):
    return ''


def confirm_huawei(request, pay_channel={}):

    result = request.POST.get('result')
    userName = request.POST.get('userName')
    productName = request.POST.get('productName')
    payType = request.POST.get('payType')
    amount = request.POST.get('amount')#商品支付金额  (格式为：元.角分，最小金额为分，  例如：20.00) 
    orderId = request.POST.get('orderId')
    notifyTime = request.POST.get('notifyTime')
    requestId = request.POST.get('requestId')
    bankId = request.POST.get('bankId')
    orderTime = request.POST.get('orderTime')
    tradeTime = request.POST.get('tradeTime')
    accessMode = request.POST.get('accessMode')
    spending = request.POST.get('spending')
    
    
    pay_amount = 0
    order_id = ''
    server_id = 0
    player_id = 0
    result_msg = '{"result":1}'
    remark = ''
    
    valid = False
    
    try:
        valid = check_sign(request)
    except Exception, ex:
        print ex
        result_msg = '{"result":94}'
    print 'check_sign:', valid
    if valid:
        if result == "0":
            try:
                order_id = orderId
                server_id, player_id, qd = requestId.split('_')
                server_id = int(server_id)
                player_id = int(player_id)
                amount = float(amount)
                if amount > 0:
                    pay_amount = amount
                result_msg = '{"result":0}'
            except Exception, ex:
                print ex
                result_msg = '{"result":94}'
    else:
        remark = 'sign error'
   
    
    return {'server_id':server_id, 'player_id':player_id ,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}


def check_sign(request):
    from services.alipay import check_with_rsa_huawei
    keys = request.POST
    keys = [tuple(item) for item in keys.items()]
    keys.sort()
    sign_str = []
    sign = ''
    for item in keys:
        if item[0]=='sign':
            sign = item[1]
        else:
            sign_str.append('%s=%s'%(item[0],item[1]))
            
    sign_str = '&'.join(sign_str)
    #print 'sign_str:', sign_str
    sign_str = sign_str.encode('utf-8')
    #print sign_str
    #print '------------------------'
    return check_with_rsa_huawei(sign_str, sign)

#    keys = ['result', 'userName', 'productName', 'payType', 'amount', 'orderId', 'notifyTime', 'requestId', 'bankId', 'orderTime', 'tradeTime', 'accessMode', 'spending']
#    keys.sort()
#    sign_str = []
#    sign = ''
#    for item in keys:
#        value = request.POST.get(item, '')
#        if item=='sign':
#            sign = value
#        else:
#            sign_str.append('%s=%s'%(item,value))
#            
#    sign_str = '&'.join(sign_str)
#    print sign_str

#1: 验签失败, 
#2: 超时, 
#3: 业务信息错误，比
#94: 系统错误, 
#95: IO 错误, 
#96: 错误的url, 
#97: 错误的响应, 
#98: 参数错误, 
#99: 其他错误 
