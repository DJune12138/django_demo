# -*- coding: utf-8 -*-

from services.views import md5
import json

def confirm_miaobo_get_link_id(request):
    post_json = {}
    try:
        post_json = json.loads(request.raw_post_data)
    except:
        pass
    return post_json.get('payWay','')

def confirm_miaobo(request,pay_channel={}):
    app_id = pay_channel.get_config_value('app_id','GZFY-6')
    app_key = pay_channel.get_config_value('app_key','35KNSK681XkBDAQws4hQ')
    user_type = pay_channel.get_config_value('user_type',15)
    sign = request.GET.get('checksum','')
    #print(sign) #8a707127d015fbcb7299edc98f157e78
    pay_status = 'FAILURE'
    post_json = None
    post_json_str = ''
    if request.method == 'POST':
        try:
            post_json_str = request.raw_post_data
            post_json = json.loads(post_json_str)
        except Exception,e:
            print('confirm miaobo error:',e)
#    else:
#        post_json_str = '{"orderID":"407-1356599268570-6294","amount":"200","userID":"407","gameID":"GZFY-6-SLG-1","serverID":"36","chargeID":"","payWay":"","callbackInfo":""}'
#        post_json = json.loads(post_json_str)

    sign_str = md5('%s%s%s'%(app_id,post_json_str,app_key))
    
    pay_amount = 0
    server_id = 0
    open_id = ''
    order_id = ''
    remark = ''
    if sign_str == sign:
        try:
            server_id = int(post_json['serverID'])
            open_id = post_json['userID']
            
            order_id=post_json['orderID']
            
            remark = post_json.get('failedDesc','')
           
            if post_json.get('orderStatus','S')=='S':
                pay_amount = float(post_json.get('amount','0')) / 100
            
            pay_status = 'SUCCESS'
        except Exception,e:
            print('confirm has miaobo error:',e)
            pay_status = 'UnknowError'

    else:
        pay_status = 'ErrSign'
        print('sign error:',sign_str,sign)

    return {'server_id':server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':pay_status}





