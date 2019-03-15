# -*- coding: utf-8 -*-
from services.views import md5,getConn
import json


def pay_baidu(the_action , pay_channel = {} , host_ip='service.fytxonline.com'):
    
    client_id = pay_channel.get_config_value('client_id','443a533492ed342ea2e29671bd54f2cc')
    game_id = pay_channel.get_config_value('game_id','112')
    session_secret = pay_channel.get_config_value('session_secret','5845d760f622b7e2c9094b466589a179')
    Aid = the_action.query_id
    pay_url = pay_channel.get_config_value('pay_url','http://api.m.duoku.com/openapi/client/duokoo_card_recharge') #http://duokoo.baidu.com/openapi/client/duokoo_card_recharge
    access_token = ''
    result_code = 0
    result_msg = ''
    try:
        conn = getConn(the_action.server_id)
        query_sql = "select other from player_%d where user_type=%d and player_id='%s'"%(the_action.server_id,12,the_action.pay_user)
#        print(query_sql)
        cursor = conn.cursor()
        cursor.execute(query_sql)
        pay_user_record = cursor.fetchone()
        if pay_user_record!=None:
            access_token = pay_user_record[0]
        conn.close()
    except:
        print('confirm baidu has error: db connection error!')
#    if True:
    try:
#access_token值+client_id值+card_num值+ card_pwd 值+ card_type值+ pay_num 值+session_secret值(计算时无+号)
        sign_str = '%s%s%s%s%s%d%s'%(access_token,client_id,the_action.card_no,the_action.card_pwd,pay_channel.link_id,int(the_action.post_amount),session_secret)
        #print(sign_str)
        client_secret = md5(sign_str)
        query_url = '%s?client_id=%s&game_id=%s&aid=%s&access_token=%s&card_num=%s&card_pwd=%s&card_type=%s&pay_num=%d&client_secret=%s'%(pay_url,client_id,game_id,Aid,access_token,the_action.card_no,the_action.card_pwd,pay_channel.link_id,int(the_action.post_amount),client_secret)
        #print(query_url)

        from urllib2 import urlopen
#        print(query_url)
        result = ""
        try:
            result = urlopen(query_url,timeout=10).read()
            result = json.loads(result)
        except Exception,e:
            print('pay baidu has error',e)
#        result = http_post(query_url)
        
        print(result)
        if result.get('order_id',None)!=None:
            the_action.order_id=result['order_id']
            the_action.pay_status = 1
            result_code = 1
        else:
            result_msg = result.get('error_msg','')
            the_action.remark = result_msg
            
        the_action.save(using='write')
    except Exception,e:
        result_code = -1
        print('pay baidu has error',e)
        
    return (result_code,result_msg)


def confirm_baidu_get_link_id(request):
    return request.GET.get('cardtype','')
    
    
def confirm_baidu(request,pay_channel={}):
    
    result_code = 'ERROR_SIGN'
    session_secret = ''
    
    try:
        session_secret = pay_channel.get_config_value('session_secret', '5845d760f622b7e2c9094b466589a179')
    except:
        result_code = 'ERROR_PAY_CONFIG'
    
    result_msg_list = {'0':'充值已提交','1':'充值成功','2':'充值失败','3':'查询失败'}

    query_id = request.GET.get('aid','')
    pay_amount = request.GET.get('amount','')
    cardtype = request.GET.get('cardtype','')
    orderid = request.GET.get('orderid','')
    result = request.GET.get('result','')
    timestamp = request.GET.get('timetamp','')
    client_secret = request.GET.get('client_secret','')
    #client_id值+ game_id值+ Aid值+ order_id值+session_secret值(计算时无+号)
    sign_str = '%s%s%s%s%s%s%s'%(pay_amount,cardtype,orderid,result,timestamp,session_secret,query_id)
    #print(pay_amount,cardtype,orderid,result,timestamp,session_secret,query_id,sign_str)
    sign_str = md5(sign_str)
    #print(client_secret,sign_str)
    amount = 0
    remark = ''

    if client_secret == sign_str:
        try:
            if result=='1':
                amount = float(pay_amount)
            
            remark = result_msg_list.get(result,'')
            result_code = 'SUCCESS' 
            
        except Exception,e:
            result_code = -1
            print('pay baidu has error',e)
    
    
    return {'query_id':query_id,'order_id':orderid,'amount':amount,'remark':remark,'result_msg':result_code}





#
#
#def confirm_baidu(request,pay_channel):
#    
#    session_secret = '5845d760f622b7e2c9094b466589a179'
#    
#    result_code = 'ERROR_SIGN'
#    
#    result_msg_list = {'0':'充值已提交','1':'充值成功','2':'充值失败','3':'查询失败'}
#
#    
#    pay_amount = request.GET.get('amount','')
#    cardtype = request.GET.get('cardtype','')
#    orderid = request.GET.get('orderid','')
#    result = request.GET.get('result','')
#    timestamp = request.GET.get('timetamp','')
#    client_secret = request.GET.get('client_secret','')
#    
#    sign_str = '%s%s%s%s%s%s'%(pay_amount,cardtype,orderid,result,timestamp,session_secret)
##    print(sign_str)
#    sign_str = md5(sign_str)
##    print(sign_str,client_secret)
#    if client_secret == sign_str:
#        try:
#            pay_channel = PayChannel.objects.using('read').get(func_name='baidu',link_id=cardtype)
#            list_pay = PayAction.objects.using('write').filter(order_id=orderid,pay_type=pay_channel.id)
#            if len(list_pay)>0:
#                pay_action = list_pay[0]
#                if abs(pay_action.pay_status)<2:
#                    pay_amount = float(pay_amount)
#                    
#                    if result=='1':
#                        pay_action.pay_amount = pay_amount
#                        pay_action.pay_gold = pay_action.pay_amount * pay_channel.exchange_rate
#                        pay_action.pay_status = 2
#                    else:
#                        pay_action.pay_status = -2
#                    
#                    pay_action.remark = result_msg_list.get(result,'')
#                    pay_action.save(using='write')
#                    result_code = 'SUCCESS'
#                else:
#                    result_code = 'ERROR_REPEAT'
#            else:
#                result_code = 'ERROR_ORDER'
#            
#        except Exception,e:
#            result_code = -1
#            print('pay baidu has error',e)
#    
#    
#    return render_to_response('pay/pay_post.html',{'pay_status':result_code})