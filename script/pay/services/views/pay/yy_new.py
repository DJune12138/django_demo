#coding=utf-8

from services.views import md5
from services.views import query_player
from django.shortcuts import render_to_response
import json

def confirm_yy_get_link_id(request):
    return request.GET.get('type', '')

def confirm_yy_new(request, pay_channel):
    rg = request.GET

    account = rg.get('account', '')
    orderid = rg.get('orderid', '')
    rmb = rg.get('rmb', '')
    num = rg.get('num', '')
    rtype = rg.get('type', '')
    time = rg.get('time', '')
    game = rg.get('game', '')
    server = rg.get('server', '')
    role = rg.get('role', '')
    itemid = rg.get('itemid', '')
    price = rg.get('price', '')
    itemname = rg.get('itemname', '')
    cparam = rg.get('cparam', '')
    sign =rg.get('sign', '')

    server_id = 0
    open_id = 0
    order_id = ''
    remark = ''
    pay_amount = 0
    result_msg = ''
    user_type = int(pay_channel.get_config_value('user_type', 46))

    #sign = account + orderid + rmb + num + rtype + time + game + server + role + itemid + price + itemname + cparam + sign

    try:
        app_key = pay_channel.get_config_value('app_key', 'dpmoFiT05iTvMYGrvvuokwybDz0n0Jja')
        check_sign = md5('%s%s%s%s%s%s%s%s%s%s%s%s%s%s' %
                         (account, orderid, rmb, num, rtype, time, game, server, role, itemid, price, itemname, cparam, app_key))
        server_list = pay_channel.get_config_value('server_list', {})
        server_id = int(server_list.get(str(server), server))
        print "##### %s #####" % {'in_sign':sign, 'local_sign':check_sign}

        if check_sign == sign:
            pay_amount = float(rmb)
            open_id = account
            order_id = orderid
            result_msg = json.dumps({"code":1, "data":{"orderid":order_id, "rmb":pay_amount, "account":int(account)}})
        else:
            remark = 'sign error'
            result_msg = json.dumps({"code":-19, "data":None})
    except Exception, e:
        print e

    return {'server_id':server_id, 'open_id':open_id, 'user_type':user_type, 'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}


def query_yy(request):
    g = request.GET
    account = g.get('account', '')
    time = g.get('time', '')
    game = g.get('game', '')
    server = g.get('server', '')
    sign = g.get('sign', '')

    code = -1

    s_sign = md5('%s%s%s%s%s' % (account, game, server, time, 'dpmoFiT05iTvMYGrvvuokwybDz0n0Jja'))

    player = {'user_id':0, 'player_id':0, 'player_name':'', 'level':0, 'server_id':0}
    sign = sign.lower()
    if sign != s_sign:
        return render_to_response('client/yy/player_info.html', {'player':player, 'code':code})

    try:
        server = int(server)
        player = query_player(46, account, server)
        code = 0
    except Exception, ex:
        print 'query yy error:', ex

    return render_to_response('client/yy/player_info.html', {'player':player, 'code':code})