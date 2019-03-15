#coding=utf-8

from services.views import md5

def confirm_downjoy_new_get_link_id(request):
    return ''

def confirm_downjoy_new(request, pay_channel):
    rg = request.GET

    result = rg.get('result', '')
    money = rg.get('money', '')
    order = rg.get('order', '')
    mid = rg.get('mid', '')
    time = rg.get('time', '')
    ext = rg.get('ext', '')
    signature = rg.get('signature', '')

    payment_key = pay_channel.get_config_value('merchantKey', 'PE2KzkaO63W6')
    ext_info = ext.split('_')

    order_id = ''
    server_id = 0
    player_id = 0
    amount = 0
    remark = ''
    result_msg = ''

    try:
        sign_str = 'order=%s&money=%s&mid=%s&time=%s&result=%s&ext=%s&key=%s' % (order, money, mid, time, result, ext, payment_key)
        sign_md5 = md5(sign_str)

        print '-----', sign_str
        print '=====', {'in_sign':signature, 'local_sign': sign_md5}

        if sign_md5 == signature and int(result) == 1:
            order_id = order
            player_id = int(ext_info[0])
            server_id = int(ext_info[1])
            amount = float(money)
            result_msg = 'success'
        else:
            result_msg = 'error'
            remark = 'sign error'
    except Exception,e:
        print e

    return {"server_id":server_id, "player_id":player_id, "order_id":order_id, "amount":amount, "remark":remark, "result_msg":result_msg}
