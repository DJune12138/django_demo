# -*- coding: utf-8 -*-
# GET  http://127.0.0.1:8002/service/confirm/douzhen?serverId=14&callbackInfo=14&openId=14680065&orderId=120507224627804959449D&orderStatus=1&payType=2&amount=10&remark=hello&sign=db651e40d456c8b0972f5447173329d1
# 测试地址
# http://127.0.0.1:8002/service/confirm/douzhen?orderId=1000000316407512&postTime=1500381300&uId=458456&playerId=2097437&sdkSimpleName=apple_douzhen&custom=6%235%23xxx&goodsName=300灵玉&currency=CNY&goodsId=com.xigua.mhtx.300&queryId=20170718204500122533AC61&remoteIp=14.23.124.148&serverSign=72c52e76dc2abbddbf4f1112b53cc997&serverId=2&gameSimpleName=mhtx_ios&payTime=1500381349&payAmount=648.0
from services.views import md5
import hashlib
from models.log import DictDefine
import hashlib
from services.views.pay import Log


def to_md5(sign_str):
    return hashlib.md5(sign_str).hexdigest()


# 方法里不涉及数据库操作,包括参数处理,验证签名,返回json对象:user_type,openid,server_id,player_id,pay_amount,result_msg

def confirm_douzhen_get_link_id(request):
    return request.POST.get('payType', '')


def confirm_douzhen(request, pay_channel):
    result_msg = 'FAILURE'
    if not pay_channel:
        return {'result_msg': "pay_channel Error"}

    app_key = ""
    try:
        app_key = pay_channel.get_config_value('app_key', '')
    except Exception, e:
        print 'confirm douzhen has Error:', e

    if not app_key:
        return {'result_msg': "app_key Error"}

    charge = request.POST.get('private_data', '')
    charge = charge.split("#")
    charge_id, charge_type, extra,appsflyer_id,advertising_idfa = 0, 0,"","",""
    try:
        charge_id = int(charge[0])
        charge_type = int(charge[1])
        extra = str(charge[2])
        # appsflyer_id = str(charge[3])
        # advertising_idfa = str(charge[4])

    except Exception as e:
        print "get charge_id error", e


    # 支付的金额 cny
    amount = request.POST.get('amount', 0)
    channel_number = request.POST.get('channel_number','')
    channel_order_id = request.POST.get('channel_order_id','')
    channel_product_id = request.POST.get('channel_product_id','')
    game_id = request.POST.get('game_id','')
    order_id = request.POST.get('order_id','')
    order_type = request.POST.get('order_type','')
    pay_status = request.POST.get('pay_status','')
    pay_time = request.POST.get('pay_time','')
    private_data = request.POST.get('private_data','')
    product_count = request.POST.get('product_count','')
    plugin_id = request.POST.get('plugin_id','')
    product_id = request.POST.get('product_id','')
    product_name = request.POST.get('product_name','')
    server_id = request.POST.get('server_id','')
    user_id = request.POST.get('user_id','')
    source = request.POST.get('source','')
    enhanced_sign = request.POST.get('enhanced_sign','')
    sign = request.POST.get('sign','')
    currency = "TWD"
    game_user_id = request.POST.get('game_user_id','')

    # 支付通道
    payType = ""

    chargeType = DictDefine.get_dict_for_key("charge_id_money")
    if chargeType and amount and charge_id:
        need_amount = int(chargeType[str(charge_id)])
        if need_amount != int(amount):
            charge_id = 999

    val = "%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s"%(amount,channel_number,channel_order_id,channel_product_id,
                                                  enhanced_sign,game_id,game_user_id,order_id,order_type,pay_status,
                                                  pay_time,plugin_id,private_data,product_count,product_id,product_name,
                                                  server_id,source,user_id)



    #校验
    if pay_status != "1":
        return {"result_msg":"faill01"}

    #添加sdk包不同的appkey(临时)
    if game_id =="20001":
        app_key="a6034a6c43fe33db13b16afa40b4e548"

    if game_id =="11001":
        app_key="7bd22b8b8dba907fd4b814539783d3b1"

    if game_id =="10001":
        app_key="e2e6cdc38f25be9f88d30eeb47eb59b6"


    print 'okkkkkkkkkkkkkk',to_md5(to_md5(val)+app_key)
    if sign != to_md5(to_md5(val)+app_key):
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
               # "appsflyer_id":appsflyer_id,
               # "advertising_id":advertising_idfa
               }
    print _result
    return _result








