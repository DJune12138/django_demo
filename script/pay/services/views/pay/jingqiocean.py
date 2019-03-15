# -*- coding: utf-8 -*-
#GET  http://127.0.0.1:8002/service/confirm/jingqi?serverId=14&callbackInfo=14&openId=14680065&orderId=120507224627804959449D&orderStatus=1&payType=2&amount=10&remark=hello&sign=db651e40d456c8b0972f5447173329d1
# 测试地址
# http://127.0.0.1:8002/service/confirm/jingqi?orderId=1000000316407512&postTime=1500381300&uId=458456&playerId=2097437&sdkSimpleName=apple_xingwan&custom=6%235%23xxx&goodsName=300灵玉&currency=CNY&goodsId=com.xigua.mhtx.300&queryId=20170718204500122533AC61&remoteIp=14.23.124.148&serverSign=72c52e76dc2abbddbf4f1112b53cc997&serverId=2&gameSimpleName=mhtx_ios&payTime=1500381349&payAmount=648.0
from services.views import md5
import hashlib
from models.log import DictDefine


#方法里不涉及数据库操作,包括参数处理,验证签名,返回json对象:user_type,openid,server_id,player_id,pay_amount,result_msg

def to_md5(sign_str):
    return hashlib.md5(sign_str).hexdigest()


def confirm_jingqiocean_get_link_id(request):
    return request.POST.get('payType', '')


def confirm_jingqiocean(request, pay_channel):
    result_msg = 'FAILURE'
    if not pay_channel:
        return {'result_msg': "pay_channel Error"}

    app_key = ""
    try:
        app_key = pay_channel.get_config_value('app_key', '')
    except Exception, e:
        print 'confirm jingqiocean has Error:', e

    if not app_key:
        return {'result_msg': "app_key Error"}



    # 支付的金额 cny
    game_id = request.POST.get('appId','')
    order_id = request.POST.get('orderId','')
    uid = request.POST.get('uid','')
    amount = request.POST.get('amount', 0)
    server_id = request.POST.get('serverId', '')
    extraInfo = request.POST.get('extraInfo','')
    test = request.POST.get('test','')
    pay_time = request.POST.get('orderTime','')
    product_num = request.POST.get('billno','')

    sign = request.POST.get('sign','')
    currency = "USD"

    charge = extraInfo
    charge = charge.split("#")
    charge_id,charge_type,extra,user_id = 0, 0,"",""
    try:
        charge_id = int(charge[0])
        charge_type = int(charge[1])
        extra = str(charge[2])
        user_id =str(charge[3])

    except Exception as e:
        print "get charge_id error", e

    # 支付通道
    payType = ""

    chargeType = DictDefine.get_dict_for_key("charge_id_money")
    print '00000000000',chargeType
    if chargeType and amount and charge_id:
        need_amount = float(chargeType[str(charge_id)])
        print 'vvvvvvvvvvvvvv', chargeType,need_amount
        if need_amount != float(amount):
            charge_id = 999

    val = "amount%sappId%sbillno%sextraInfo%sorderId%sorderTime%sserverId%stest%suid%s"%(amount,game_id,product_num,extraInfo,order_id,pay_time,server_id,test,uid)

    print 'kkkkkkkkkkkkkk',to_md5(val+app_key)
    if sign != to_md5(val+app_key).lower():
        return {"result_msg":"check faill02"}
    print val, sign
    game_user_id = user_id

    result_msg = "SUCCESS"
    _result = {"result_msg": result_msg,
               "query_id": order_id,
               "order_id": order_id,
               "amount": float(amount),
               "charge_id": charge_id,
               "charge_type": charge_type,
               "server_id": server_id,
               "player_id": game_user_id,
               "payType": payType,
               "currency": currency,
               "extra": extra,
               }
    print "鲸齐结果：",_result
    return _result
        
        
        
        
        
        
        