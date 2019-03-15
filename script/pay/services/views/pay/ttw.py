#coding=utf-8

import urllib
from services.views import md5

def confirm_ttw_get_link_id(request):
    return request.GET.get('paytype', '')

def confirm_ttw(request, pay_channel):
    rp = request.POST

    orderid = rp.get('orderid', '')
    username = rp.get('username', '')
    gameid = rp.get('gameid', '')
    roleid = rp.get('roleid', '')
    serverid = rp.get('serverid', '')
    paytype = rp.get('paytype', '')
    amount = rp.get('amount', '')
    productname = rp.get('productname', '').encode("utf-8")
    paytime = rp.get('paytime', '')
    attach = rp.get('attach', '')
    sign = rp.get('sign', '')

    server_id = 0
    order_id = ''
    pay_amount = 0
    remark = ''
    open_id = 0
    result_msg = ''
    user_type = pay_channel.get_config_value('user_type', 107)
    if user_type != '':
        user_type = int(user_type)

    orderid_url = urlencode("orderid", orderid)
    username_url = urlencode("username", username)
    roleid_url = urlencode("roleid", roleid)
    productname_url = urlencode("productname", productname)
    paytype_url = urlencode("paytype", paytype)
    attach_url = urlencode("attach", attach)

    try:
        app_key = pay_channel.get_config_value('app_key', '288ec75d9347f4d7d73c9d8a741b43c0')
        server_list = pay_channel.get_config_value('server_list', {})
        server_id = int(server_list.get(str(serverid), serverid))

        local_sign = "%s&%s&gameid=%s&%s&serverid=%s&%s&amount=%s&%s&paytime=%s&%s&appkey=%s" \
                     % (orderid_url, username_url, gameid, roleid_url, serverid, paytype_url, amount, productname_url,
                        paytime, attach_url, app_key)
        print local_sign
        local_sign = md5(local_sign)

        print {"in_sign":sign, "local_sign": local_sign}

        if sign == local_sign:
            order_id = orderid
            pay_amount = int(amount)
            open_id = username
            result_msg = 'success'
        else:
            result_msg = 'errorSign'
            remark = 'sign error'
    except Exception,e:
        print e

    return {"server_id":server_id, "open_id":open_id, "order_id":order_id, "user_type":user_type, "amount":pay_amount, "remark":remark, "result_msg":result_msg}


def urlencode(key, value):
    return urllib.urlencode({key:value})