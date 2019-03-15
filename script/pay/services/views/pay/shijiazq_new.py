#coding=utf-8

from services.views import md5

def confirm_shijiazq_new_get_link_id(request):
    return ''


def confirm_shijiazq_new(request, pay_channel):
    rp = request.POST
    orderId = rp.get("orderId")
    uid = rp.get("uid")
    amount = rp.get("amount")
    extraInfo = rp.get("extrainfo")
    sign = rp.get("sign")
    serverId = rp.get("serverId")

    print "-----",rp
    app_key = pay_channel.get_config_value("app_key", "7728a436fd1411e39e36ac220bb906f8")
    # orderId + uid + serverId + amount  + extraInfo + Appkey

    order_id = ''
    server_id = 0
    player_id = 0
    pay_amount = 0
    result_msg = ''
    remark= ''
    try:
        make_sign = "%s%s%s%s%s%s" % (orderId, uid, serverId, amount, extraInfo, app_key)
        md5_sign = md5(make_sign)
        print "======",(md5_sign, sign)

        if md5_sign == sign:
            order_id = orderId
            server_id = int(serverId)
            player_id = int(extraInfo)
            pay_amount = int(amount)
            result_msg = "success"
        else:
            result_msg = 'fail'
            remark = 'sign error'
    except Exception, e:
        print e

    return {"server_id":server_id, "player_id":player_id, "order_id":order_id, "amount":pay_amount, "remark":remark, "result_msg":result_msg}

