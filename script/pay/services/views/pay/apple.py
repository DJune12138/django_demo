# -*- coding: utf-8 -*-

from services.http import http_post
import json

def confirm_apple_get_link_id(reqeust):
    return None

def confirm_apple(request,pay_channel={}):
    player_id = int(request.POST.get('player_id','0'))
    server_id = int(request.POST.get('server_id','0'))
    is_test = request.REQUEST.get('test','')
    receipt_data = request.POST.get('receipt-data','')
    if is_test or server_id==177:
        post_url = 'https://sandbox.itunes.apple.com/verifyReceipt'
    else:
        post_url = 'https://buy.itunes.apple.com/verifyReceipt'
        
    post_data = '{"receipt-data":"%s"}'%receipt_data
    result_code = 0
    pay_amount = 0
    order_id = ''
    product_id = ''
    try:
        result = http_post(post_url,post_data,'json')
        print(result)
        result = json.loads(result)
        if result.get('status',-1)==0:
            pay_amount = int(result['receipt']['quantity'])
            product_id = result['receipt']['product_id']
          
            order_id = result['receipt'].get('transaction_id','')
            result_code = 1

    except Exception,e:
        result_code = -1
        print('confirm apple has error',e)
    
    print(result_code)
    return {'server_id':server_id,'player_id':player_id,'link_id':product_id,'order_id':order_id,'amount':pay_amount,'result_msg':result_code}

