# -*- coding: utf-8 -*-
from services.http import http_post
import urllib, json
def confirm_so_cayenne(request, pay_channel={}):          
    g = lambda x,y:request.GET.get(x, request.POST.get(x, y))
    server_id = int(g('serverID', 0))
    player_id = int(g('playerID', 0))
    result_list = []
    orderID = g('orderID', '')
    print 'get param server_id:%d'% server_id
    print 'get param player_id:%d'% player_id
    
    print 'get request:%s'% request
    request_url = 'http://gameapi.wasabiiapps.com.tw/gameserver/query_consume.json'
    print 'start post'
    print orderID
    print 'end get orders'
    orders = [{}]
    orders[0]['order-id'] = orderID
#    orders_str = '%s'% orders
    orders_str = 'orders[0][order-id]'
#    return result_list
#    result = http_post(request_url, '&orders=%s&order-id=%s' % (urllib.quote_plus(orders, ''), urllib.quote_plus(order_id, '')) )
    print 'request_url is %s'% request_url
    print 'orders_str is %s'% orders_str 
#    result = http_post(request_url, '%s' % (urllib.quote_plus(orders_str, '')) )
    result = http_post(request_url, '&%s=%s' % (urllib.quote_plus(orders_str, ''), orderID) )
    print 'get post:%s'% result
    order_list = get_order_list(result)

    currency = 0
    amount = 0
    remark = ''
    result_msg = ''
    if type(order_list) == int:
        result_msg = '%s'% order_list
    else:
        for item in order_list:
            order_id = item.get('order-id')
            amount = int(item.get('consume-point'), 10) / 5.0
#            amount = item.get('item-amount', '')
            remark = ''
            result_msg = 0
            result_list.append({'server_id':server_id, 'currency':currency, 'player_id':player_id, 'order_id':order_id, 'amount':amount, 'remark':remark, 'result_msg':result_msg})
    
    return result_list

#     result_code = j("result-code", '')
#     orders = j("orders", '')
#     query_result_code = j("query-result-code", '')
#     query_result_desc = j("query-result-desc", '')
#     order_id = j("order-id", '')
#     game_id = j("game-id", '')
#     item_id = j("item-id", '')
#     item_amount = j("item-amount", '')
#     consume_point = j("consume-point", '')
#     transaction_datetime = j("transaction-datetime", '')
#     status = j("status", '')
#     user_platform_id = j("user-platform-id", '')
    
def get_order_list(data):
    data = json.loads(data)
    
    state = data.get('result-code', 0)
    if 200 != state:
        return int(state)
    
    order_list = data.get('orders')
    
    return order_list

def confirm_so_cayenne_get_link_id(request):
    return ''
    
    
