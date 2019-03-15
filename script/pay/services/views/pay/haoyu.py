# -*- coding: utf-8 -*-
# GET  http://127.0.0.1:8002/service/confirm/haoyu?serverId=14&callbackInfo=14&openId=14680065&orderId=120507224627804959449D&orderStatus=1&payType=2&amount=10&remark=hello&sign=db651e40d456c8b0972f5447173329d1
# 测试地址
# http://127.0.0.1:8002/service/confirm/haoyu?orderId=1000000316407512&postTime=1500381300&uId=458456&playerId=2097437&sdkSimpleName=apple_haoyu&custom=6%235%23xxx&goodsName=300灵玉&currency=CNY&goodsId=com.xigua.mhtx.300&queryId=20170718204500122533AC61&remoteIp=14.23.124.148&serverSign=72c52e76dc2abbddbf4f1112b53cc997&serverId=2&gameSimpleName=mhtx_ios&payTime=1500381349&payAmount=648.0
from services.views import md5
import hashlib
from models.log import DictDefine


# 方法里不涉及数据库操作,包括参数处理,验证签名,返回json对象:user_type,openid,server_id,player_id,pay_amount,result_msg

def confirm_haoyu_get_link_id(request):
    return request.GET.get('payType', '')


def confirm_haoyu(request, pay_channel):
    result_msg = 'FAILURE'
    if not pay_channel:
        return {'result_msg': "pay_channel Error"}

    app_key = ""
    try:
        app_key = pay_channel.get_config_value('app_key', '')
    except Exception, e:
        print 'confirm haoyu has Error:', e

    if not app_key:
        return {'result_msg': "app_key Error"}

    charge = request.GET.get('custom', '')
    charge = charge.split("#")
    charge_id, charge_type, extra = 0, 0, ""
    try:
        charge_id = int(charge[0])
        charge_type = int(charge[1])
        extra = str(charge[2]) if len(charge) >= 3 else ""
    except Exception as e:
        print "get charge_id error", e

    query_id = request.GET.get('queryId', '')

    serverSign = request.GET.get('serverSign', '')

    # 支付的金额 cny
    amount = float(request.GET.get('payAmount', 0))
    order_id = request.GET.get("orderId", '')
    server_id = request.GET.get('serverId', '')
    player_id = int(request.GET.get('playerId', 0))
    currency = request.GET.get('currency')

    # 支付通道 
    payType = request.GET.get("payType", '')

    chargeType = DictDefine.get_dict_for_key("charge_id_money")
    if chargeType and amount and charge_id:
        need_amount = int(chargeType[str(charge_id)])
        if need_amount != int(amount):
            charge_id = 999

    _sign = "serverId=%s&playerId=%s&orderId=%s&gameAppKey=%s" % (server_id,
                                                                  player_id, order_id, app_key)

    _sign = md5(_sign)
    print _sign, serverSign
    if serverSign == _sign:
        result_msg = "SUCCESS"
        _result = {"result_msg": result_msg,
                   "query_id": query_id,
                   "order_id": order_id,
                   "amount": amount,
                   "charge_id": charge_id,
                   "charge_type": charge_type,
                   "server_id": server_id,
                   "player_id": player_id,
                   "payType": payType,
                   "currency": currency,
                   "extra": extra}
        print _result
        return _result
    else:
        return {"result_msg": "sign Error"}  







