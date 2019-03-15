#coding=utf-8

import urllib
from services.views import md5
# from services.models.pay import PayAction

def confirm_rockhippo_get_link_id(request):
    return ''


def confirm_rockhippo(request, pay_channel):
    rg = request.GET

    print "*** %s ***" % rg

    postData = rg.get('postData', '')
    query_dict = urldecode(postData.split('&'))

    orderid = query_dict.get('orderId', '')
    amount = query_dict.get('amount', 0)
    paynum = query_dict.get('payNum', '')
    resultcode = query_dict.get('resultCode', 1)
    paytime = query_dict.get('payTime', '')
    failure = query_dict.get('failure', '')
    faildesc = query_dict.get('failDesc', '')
    reserved1 = query_dict.get('reserved1', 0)
    reserved2 = query_dict.get('reserved2', 0)
    reserved3 = query_dict.get('reserved3', '')
    sign = query_dict.get('signMsg', '')

    server_id = 0
    player_id = 0
    pay_amount = 0
    order_id = ''
    remark = ''
    result_msg = ''

    app_key = pay_channel.get_config_value('app_key', 'rockhippo.net from 10002')

    try:
        server_list = pay_channel.get_config_value('server_list', {})
        server_id = int(server_list.get(str(reserved1), reserved1))

        faildesc_url = urllib.urlencode({"failDesc":faildesc})
        local_sign = "orderId=%s&amount=%s&payNum=%s&resultCode=%s&payTime=%s&failure=%s&%s&reserved1=%s&reserved2=%s" \
                     "&reserved3=%s&appKey=%s" % (orderid, amount, paynum, resultcode, paytime, failure, faildesc_url,
                                                  reserved1, reserved2, reserved3, app_key)
        print '--- %s ---' % local_sign
        local_sign = md5(local_sign).upper()

        print '###', {'in_sign':sign, 'local_sign':local_sign}

        if local_sign == sign:
            player_id = int(reserved2)
            pay_amount = int(amount)/100
            order_id = orderid
            result_msg = "result=1"
        else:
            result_msg = 'result=0'
    except Exception,e:
        print e

    return {'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}


def urldecode(param_list):
    dec_list = {}
    for i in param_list:
        key,value = i.split("=")
        if key == 'failDesc':
            value = urllib.unquote(value)
        dec_list[key] = value
    return dec_list

# def query_rockhippo(request):
#     appId = '10002'
#     appKey = 'rockhippo.net from 10002'
#     userId = request.GET.get('userId', 0)
#     appName = '风云天下OL'
#     price = request.GET.get('price', 0)
#     gameType = 2
#     productName = request.GET.get('productName', '')
#     reserved1 = request.GET.get('serverId', 0)
#     reserved2 = request.GET.get('roleId', 0)
#     reserved3 = ''
#     postUrl = ''
#
#     the_pay_action = PayAction()
#     the_pay_action.set_query_id()
#     the_pay_action.pay_user = userId
#     the_pay_action.pay_status = 0
#     the_pay_action.save(using='write')
#
#     orderId = the_pay_action.query_id
#
#     signMsg = 'appId=%s&orderId=%s&postUrl=%s&appName=%s&price=%s&gameType=%s&productName=%s&reserved1=%s&reserved2=%s&reserved3=%s&appKey=%s'\
#               %(appId, orderId, postUrl, appName, price, gameType, productName, reserved1, reserved2, reserved3, appKey)
#     md5_sign = md5(signMsg)
#
#     ret_str = 'appId=%s&orderId=%s&postUrl=%s&appName=%s&price=%s&gameType=%s&productName=%s&reserved1=%s&reserved2=%s&reserved3=%s&signMsg=%s'\
#               %(appId, orderId, postUrl, appName, price, gameType, productName, reserved1, reserved2, reserved3, md5_sign)
#
#     return ret_str