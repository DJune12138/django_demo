# -*- coding: utf-8 -*-

from services.http import http_post
import urllib

def confirm_paypal_get_link_id(request):
    return ''

def confirm_paypal(request, pay_channel={}):
    pp_url = pay_channel.get_config_value('pp_url','https://www.sandbox.paypal.com/cgi-bin/webscr')
    #print(request.POST)
    newparams={}
    for key in request.POST.keys():
        newparams[key]=request.POST.get(key,'').encode('utf-8')

    newparams["cmd"]="_notify-validate"
    print(newparams)
    params = urllib.urlencode(newparams)
    result_msg = 'fail'
    
#    print(params)
    pay_amount = 0
    server_id,player_id = (0,0)
    order_id = ''
    try:
        ret = http_post(pp_url, params)
        print('response',ret)
        
        server_id,player_id = newparams.get('custom','').split('-')
        
        server_id = int(server_id)
        player_id = int(player_id)
        
        order_id = newparams.get('txn_id','')
        if ret != "VERIFIED":
            
            print(" verified send back ok\n")
    
            if newparams.get('payment_status','')=='Completed':
                pay_amount = float(newparams.get('mc_gross','0'))
            
            result_msg = '200 OK'        
    
        else:
            print(" ERROR did not verify\n")
    except Exception,e:
        print('confirm paypal has error',e)

    return {'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'result_msg':result_msg}
