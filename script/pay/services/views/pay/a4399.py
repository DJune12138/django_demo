# -*- coding: utf-8 -*-
from services.views import md5
#已测  POST  http://127.0.0.1:8002/service/confirm/a4399?order_id=120507224627804959449D&account=123&pay_way=&amount=100&callback_info=14&order_status=S&failed_des=hello&sign=b8feb85a974182857de10ed7da49327e
def confirm_a4399_get_link_id(request):
    return request.POST.get('pay_way','')


def confirm_a4399(request, pay_channel={}):
    result_code = '-1'
    server_id = 0
     
    app_secret = pay_channel.get_config_value('app_secret','7a6cf796456b6d7c4c2b')
    game_id = int(pay_channel.get_config_value('game_id', 1))
    pay_server_id = int(pay_channel.get_config_value('pay_server_id', 1))
    user_type = pay_channel.get_config_value('user_type',9)
    
    order_id = request.POST.get('order_id','')
    account = request.POST.get('uid','')
    pay_way = request.POST.get('pay_way','')
    amount = request.POST.get('amount','')
    callback_info = request.POST.get('callback_info','')
    order_status = request.POST.get('order_status','')
    failed_desc = request.POST.get('failed_desc','')
    sign = request.POST.get('sign','')
    
    pay_amount = 0
    sign_str = u'%s%s%s%s%s%s%s%s%s%s'%(order_id,game_id,pay_server_id,account,pay_way,amount,callback_info,order_status,failed_desc,app_secret)
    sign_str = md5(sign_str)
    print sign_str
    if sign_str == sign:
        try:
            
            server_id = int(callback_info)
            if order_status=='S':
                pay_amount = float(amount)
            else:
                pay_amount = 0
            result_code = '1'

        except Exception,e:
            result_code = '-5'
            print('confirm 4399 has error',e)
    else:
        result_code = '-2'
    #raise Exception, order_id
    return {'server_id':server_id,'user_type':user_type,'open_id':account,'order_id':order_id,'amount':pay_amount,'remark':failed_desc,'result_msg':result_code}



#def __confirm_4399(request, pay_channel):
#    result_code = -1
#    game_id = 1
#    server_id = 1
#    app_secret='7a6cf796456b6d7c4c2b'
#    order_id = request.POST.get('order_id','')
#    account = request.POST.get('uid','')
#    pay_way = request.POST.get('pay_way','')
#    amount = request.POST.get('amount','')
#    callback_info = request.POST.get('callback_info','')
#    order_status = request.POST.get('order_status','')
#    failed_desc = request.POST.get('failed_desc','')
#    sign = request.POST.get('sign','')
#    
#    sign_str = u'%s%s%s%s%s%s%s%s%s%s'%(order_id,game_id,server_id,account,pay_way,amount,callback_info,order_status,failed_desc,app_secret)
#    sign_str = md5(sign_str)
#    if sign_str == sign:
##        if True:
#        try:
#            pay_channels = PayChannel.objects.using('read').filter(func_name='4399',link_id=pay_way)
#            if len(pay_channels)>0:
#                pay_channel = pay_channels[0]
#            else:
#                pay_channel = PayChannel.objects.using('read').get(func_name='4399',link_id='0')
#                
#            list_pay = PayAction.objects.using('write').filter(order_id=order_id,pay_type=pay_channel.id)
#            if len(list_pay)==0 :
#                #验证账号存在
#                server_id = int(callback_info)
#                pay_user = 0
#                if server_id > 0:
#                    try:
#                        conn = getConn(server_id)
#                        query_sql = "select player_id from player_%d where user_type=%d and link_key='%s'"%(server_id,9,account)
#                        cursor = conn.cursor()
#                        cursor.execute(query_sql)
#                        pay_user_record = cursor.fetchone()
#                        if pay_user_record!=None:
#                            pay_user = int(pay_user_record[0])
#                        conn.close()
#                    except:
#                        print('confirm 4399 has error:数据库链接出错!')
#                    
#                if pay_user>0:
#                    the_action = PayAction()
#                    the_action.pay_type = pay_channel.id
#                    the_action.channel_key = pay_channel.channel_key
#                    the_action.server_id = server_id
#                    the_action.order_id = order_id
#                    the_action.pay_user = pay_user
#                    the_action.query_id = the_action.get_query_id()
#                    the_action.post_amount = float(amount)
#                    if order_status=='S':
#                        the_action.pay_amount = the_action.post_amount
#                        the_action.pay_gold = the_action.pay_amount * pay_channel.exchange_rate
#                        the_action.pay_status = 2
#                    else:
#                        the_action.remark = failed_desc
#                        the_action.pay_status = -2
#                    the_action.pay_ip = request.META.get('REMOTE_ADDR','')
#                    the_action.safe_save()
#                    result_code = 1
#                else:
#                    result_code = -3
#            else:
#                result_code = 2
#        except Exception,e:
#            result_code = -5
#            print('confirm 4399 has error',e)
#    else:
#        result_code = -2
#        
#    return render_to_response('pay/pay_post.html',{'pay_status':result_code})



