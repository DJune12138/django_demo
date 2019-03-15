# -*- coding: utf-8 -*-
import json
def confirm_wdj_get_link_id(request):
    return ''


def confirm_wdj(request, pay_channel={}):

    content_str = request.POST.get('content', '{}')
    signType = request.POST.get('signType', '')
    sign = request.POST.get('sign', '')
    
    # 在订单支付成功后会立即以POST 方式回调
    pay_amount = 0
    order_id = ''
    server_id = 0
    player_id = 0
    result_msg = 'SYSTEM_ERROR'
    remark = ''
    valid = False
    
    timeStamp = ''
    orderId = ''
    money = '0'#单位是（分）
    chargeType = ''#支付类型
    appKeyId = ''
    buyerId = ''#购买人账号
    out_trade_no = ''#开发者订单号
    cardNo = ''#充值卡Id
    try:
        content = json.loads(content_str)
        timeStamp = content.get('timeStamp', '')
        orderId = content.get('orderId', '')
        money = content.get('money', '0')
        chargeType = content.get('chargeType', '')
        appKeyId = content.get('appKeyId', '')
        buyerId = content.get('buyerId', '')
        out_trade_no = content.get('out_trade_no', '')
        cardNo = content.get('cardNo', '')
        valid = check_sign(content_str, sign)
    except Exception, ex:
        valid = False
        print ex
    
    if valid:
        result_msg = 'SUCCESS'
        try:
            money = float(money)
            if money > 0:
                order_id = orderId
                pay_amount = money / 100
                server_id, player_id, timestamp = out_trade_no.split('_')
                server_id = int(server_id)
                player_id = int(player_id)
                print 'confirm wdj [info] order_id:', order_id
        except Exception, ex:
            print ex
    else:
        result_msg = 'ILLEGAL_SIGN_EMPTY'
        remark = 'sign error'
   
    
    return {'server_id':server_id, 'player_id':player_id ,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}


def check_sign(content, sign):
    from services.alipay import get_key
    from services.alipay import check_with_rsa
    key = get_key('rsa_public_key_wdj')
    return check_with_rsa(content, sign, key)
    

