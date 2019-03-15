#encoding:utf-8

import urllib
from services.views import md5

def confirm_xy_get_link_id(request):
    return request.POST.get('amount')

def confirm_xy(request, pay_channel):
    rp = lambda x,y='' : request.POST.get(x, y)
    print request.POST
    params_dict = {
        "orderid" : rp("orderid"),
        "uid" : rp("uid"),
        "serverid" : rp("serverid"),
        "amount" : rp("amount"),
        "extra" : rp("extra"),
        "ts" : rp("ts"),
    }
    sign = urllib.unquote(rp("sign"))
    app_key = pay_channel.get_config_value("app_key", "")

    server_id = player_id = amount = 0
    order_id = remark = result_msg = ""

    try:
        sign_con = app_key + "&".join(["%s=%s" % (k, params_dict[k]) for k in sorted(params_dict.keys())])
        print "=== xy ===", sign_con
        sign_md5 = md5(sign_con)
        print (sign, sign_md5)
        if sign == sign_md5:
            order_id = params_dict["orderid"]
            server_id = int(params_dict["serverid"])
            player_id = int(params_dict["extra"])
            amount = float(params_dict["amount"])
            result_msg = "success"
        else:
            result_msg = "fail"
    except Exception,e:
        print e

    return {"server_id":server_id, "player_id":player_id, "order_id":order_id, "amount":amount, "remark":remark, "result_msg":result_msg}
