#coding=utf-8

from services.views import md5
from django.http import HttpResponse

def confirm_yaya_get_link_id(request):
    return ''

def confirm_yaya(request, pay_channel):
    appkey = pay_channel.get_config_value("payment_key", "")

    rp = request.POST
    print "=====",rp
    status = rp.get("status", "")
    money = rp.get("money", 0)
    uid = rp.get("uid", 0)
    username = rp.get("username", "")
    transnum = rp.get("transnum", "")
    orderid = rp.get("orderid", "")
    ext = rp.get("ext", "")
    time = rp.get("time", "")
    sign = rp.get("sign", "")

    server_id = 0
    player_id = 0
    order_id = 0
    pay_amount = 0
    remark = ""
    result_msg = ""

    try:
        if status == "succeed":
            str_sign = "%s%s%s%s%s%s" % (orderid, transnum, username, money, status, appkey)
            print "-----", str_sign
            md5_sign = md5(str_sign).lower()
            print "-----",(md5_sign, sign)
            if md5_sign == sign:
                server_id,player_id = ext.split("_")
                order_id = orderid
                pay_amount = int(money) / 100
                result_msg = HttpResponse(status=200)
            else:
                remark = "sign error"
                result_msg = HttpResponse(status=402)
    except Exception,e:
        pass

    return {"server_id":int(server_id), "player_id":int(player_id), "order_id":order_id, "amount":pay_amount, "remark":remark, "result_msg":result_msg}




