# -*- coding: utf-8 -*-
#GET  http://127.0.0.1:8002/service/confirm/youai?serverId=14&callbackInfo=14&openId=14680065&orderId=120507224627804959449D&orderStatus=1&payType=2&amount=10&remark=hello&sign=db651e40d456c8b0972f5447173329d1
import hashlib

def confirm_keno_get_link_id(request):
    return request.POST.get('payType','')

def confirm_keno(request,pay_channel):
    result_msg = 'FAILURE'
    server_id = request.POST.get('serverId','')
    callbackInfo = request.POST.get('merchantDesc','')
    player_id = request.POST.get('userId','')
    order_id = request.POST.get('orderId','')
    order_status = request.POST.get('respCode','')
    pay_type = request.POST.get('payType','')
    amount = request.POST.get('merchantOrderAmt','')
    create_time = request.POST.get('orderCreateTime','')
    remark = request.POST.get('respDesc','')
    sign = request.POST.get('sign','')
    
    app_key = ''
    my_server_id = ''
    game_id = 0
    try:
        app_key = pay_channel.get_config_value('app_key','13ce7e16f530205aa86b3493be3fa8b10d5603de')
        game_id = pay_channel.get_config_value('game_id',1011)
    except Exception,e:
        print('confirm keno has error0',e)
                #$orderId, $userId, $gameId, $merchantOrderAmt, $merchantDesc, $payType, $orderCreateTime, $respCode, $respDesc
    sign_str = '%s%s%s%s%s%s%s%s%s'%(order_id,player_id,game_id,amount,callbackInfo,pay_type,create_time,order_status,remark)
#    print(sign_str)
    sign_str = hmac_sign(app_key,sign_str)
    print(sign_str,sign)
    
    pay_amount = 0
    the_server_id = 0

    if sign==sign_str:
        try:
            if server_id!='' and server_id!='0':
                if my_server_id != '':
                    the_server_id = int(my_server_id)
                else:
                    the_server_id = int(server_id)
            else:
                the_server_id = int(callbackInfo)
            
            player_id = int(player_id)
            
            if int(order_status)==0:
                pay_amount = float(amount)
            else:
                pay_amount = 0
            result_msg =  'success'
        except Exception,e:
            print('confirm keno has error1',e)
    else:
        result_msg = 'ErrorSign'
    
    return {'server_id':the_server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        

        
        
def hmac_sign(key,value):
    k_ipad = bytearray('a'*64,'utf-8')
    k_opad = bytearray('b'*64,'utf-8')
    
    value= bytearray(value,'utf-8')
    keyb = bytearray(key,'utf-8')
    
    
    for i in range(64-len(keyb),64):
        k_ipad[i]= 54
    for i in range(64-len(keyb),64):
        k_opad[i]= 92
    
    for i in range(0,len(keyb)):
        k_ipad[i]=keyb[i] ^ 0x36
        k_opad[i]= keyb[i] ^ 0x5c
    
    md = hashlib.md5()
    md.update(unicode(k_ipad).encode('utf-8'))
    md.update(value.decode('utf-8').encode('utf-8'))
    dg=md.digest()


    md1 = hashlib.md5()
    md1.update(unicode(k_opad).encode('utf-8'));
    md1.update(dg[:16])
    
    
    dg=md1.digest()
    strd = md1.hexdigest()

    return strd
        
        
        
        
        
        