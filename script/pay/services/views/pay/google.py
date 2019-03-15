# -*- coding: utf-8 -*-
import json

def pay_google(payAction,pay_channel={},host_ip='service.fytxonline.com'):
    return (1,payAction.id) 

def confirm_google_get_link_id(request):
    return None
    


def confirm_google(request, pay_channel={}):
    from services.alipay import check_with_rsa_google
    result_code = 0
    
    data = request.POST.get('signeddata','')#{"nonce":-256672790544269643,"orders":[{"notificationId":"3717168370285472128","orderId":"505917752127512","packageName":"com.mango.sanguo15.tw.hd","productId":"fuhd_01_01_000060_0","purchaseTime":1347614452000,"purchaseState":0}]}'
    
    sign = request.POST.get('signature','')# "AykKpxSwBoEnvUuL7UeuOye6xcxv++5+v7eYQthBLf5To4VZcvFzEV6zumT3QS8+Z7r9AwxFuZGX6uxSZKdig4DZ9WjoJPzWHc7rZlVaBsOdrYsTpu4tBUkRCIJR4leWngOSGUnP+f+jSn/dnYzN1/ifczTbktlxO+tH+dGBcQJGArOvNR+mSFVLGFmYTMeTNHKAk1qo38Ep4vrNbYcoAYVzdRoAggwww1sJaIwpeaELJwN9dh4jwlR/VHsjz9X/QjOOYIFxStIxXIU4qbNewqhaq2oLAnfczVvP+rUdBWk3v7/vhqz3zu6g/SUst9YQHnojoYq6wQY6TCkd/TObew=="
    
    result_list = []
    
    if check_with_rsa_google(data,sign):
        print('google sign ok')
#        if True:
        try:
            orders = json.loads(data)['orders']
            for pay_data in orders:
                link_id = pay_data['productId']   
                order_id = pay_data['orderId'] 
                server_id,pay_user = pay_data['developerPayload'].split(',')
                
                try:
                    server_id = int(server_id)
                    pay_user = int(pay_user)
                except:
                    continue    
                if pay_user>0:
                     
                    if pay_data['purchaseState']==0:
                        pay_amount = 1
                    else:
                        pay_amount = 0
                        
                    result_code = 1
                else:
                    result_code = 3
                
                result_item = {'server_id':server_id, 'link_id':link_id, 'player_id':pay_user, 'order_id':order_id,'amount':pay_amount,'remark':'','result_msg':result_code}
                result_list.append(result_item)
                
        except Exception,e:
            result_code = -1
            print('confirm google has error',e)
    else:
        print('sign error')
        
    return result_list

 

#def confirm_google(request):
#    from services.alipay import check_with_rsa_google
#    result_code = 0
#    
#    data = request.POST.get('signeddata','')#{"nonce":-256672790544269643,"orders":[{"notificationId":"3717168370285472128","orderId":"505917752127512","packageName":"com.mango.sanguo15.tw.hd","productId":"fuhd_01_01_000060_0","purchaseTime":1347614452000,"purchaseState":0}]}'
#    
#    sign = request.POST.get('signature','')# "AykKpxSwBoEnvUuL7UeuOye6xcxv++5+v7eYQthBLf5To4VZcvFzEV6zumT3QS8+Z7r9AwxFuZGX6uxSZKdig4DZ9WjoJPzWHc7rZlVaBsOdrYsTpu4tBUkRCIJR4leWngOSGUnP+f+jSn/dnYzN1/ifczTbktlxO+tH+dGBcQJGArOvNR+mSFVLGFmYTMeTNHKAk1qo38Ep4vrNbYcoAYVzdRoAggwww1sJaIwpeaELJwN9dh4jwlR/VHsjz9X/QjOOYIFxStIxXIU4qbNewqhaq2oLAnfczVvP+rUdBWk3v7/vhqz3zu6g/SUst9YQHnojoYq6wQY6TCkd/TObew=="
#
#    if check_with_rsa_google(data,sign):
#        print('google sign ok')
##        if True:
#        try:
#            orders = json.loads(data)['orders']
#            for pay_data in orders:
#                productId = pay_data['productId']
#                pay_channels = PayChannel.objects.using('read').filter(func_name='google',link_id=productId)
#                if len(pay_channels)>0:
#                    pay_channel = pay_channels[0]
#                    pay_config = json.loads(pay_channel.pay_config)
#                    order_id = pay_data['orderId']
#                    list_pay = PayAction.objects.using('write').filter(order_id=order_id,pay_type=pay_channel.id)
#                    if len(list_pay)==0 :
#                        server_id,pay_user = pay_data['developerPayload'].split(',')
#                        try:
#                            server_id = int(server_id)
#                            pay_user = int(pay_user)
#                        except:
#                            continue    
#                        if pay_user>0:
#                            the_action = PayAction()
#                            the_action.pay_type = pay_channel.id
#                            the_action.channel_key = pay_channel.channel_key
#                            the_action.server_id = server_id
#                            the_action.order_id = order_id
#                            the_action.pay_user = pay_user
#                            the_action.query_id = the_action.get_query_id()
#                            the_action.post_amount = pay_config.get('amount',1)
#                            if pay_data['purchaseState']==0:
#                                the_action.pay_amount = the_action.post_amount
#                                the_action.pay_gold = pay_config.get('gold',60)
#                                the_action.pay_status = 2
#                            else:
#                                the_action.pay_status = -2
#                            the_action.pay_ip = request.META.get('REMOTE_ADDR','')
#                            the_action.safe_save()
#                            result_code = 1
#                        else:
#                            result_code = 3
#                    else:
#                        result_code = 4
#                else:
#                    result_code = 2
#        except Exception,e:
#            result_code = -1
#            print('confirm google has error',e)
#    else:
#        print('sign error')
#        result_code = -2
#        
#    return render_to_response('pay/pay_post.html',{'pay_status':result_code})