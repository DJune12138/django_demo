# -*- coding: utf-8 -*-
from services.views import md5,getConn
import base64, re

def pay_baoruan(the_action,pay_channel={},host_ip='service.fytxonline.com'):
    notify_url = 'http://%s/service/confirm/baoruan/?s=%s'%(host_ip,the_action.server_id)
    app_id = pay_channel.get_config_value('app_id','828')
    app_key = pay_channel.get_config_value('app_key','f70562807b9b4030bf26702cd5cbc680')
    user_type = pay_channel.get_config_value('user_type',20)
    pay_type_str = 'fytx'
    baoruan_user = ''
    try:
        conn = getConn(the_action.server_id)
        query_sql = "select link_key from player_%d where user_type=%d and player_id=%d"%(the_action.server_id,user_type,the_action.pay_user)
        print(query_sql)
        cursor = conn.cursor()
        cursor.execute(query_sql)
        pay_user_record = cursor.fetchone()
        if pay_user_record!=None:
            baoruan_user = pay_user_record[0]
        conn.close()
    except Exception,e:
        print('pay baoruan db has error:%s'%e)
    
    if baoruan_user == '':
        return (1,'error user')
    
    token = md5('%s%s%s%s'%(app_id,baoruan_user,pay_type_str,app_key))
    notify_url = base64.encodestring(notify_url)
    #try:
        #notify_url = re.sub('\s+','',notify_url)
    #except Exception, ex:
        #print 'baoruan error:::'
        #print ex
    query_url = 'http://www.baoruan.com/nested/account/login?cid=%s&uid=%s&type=%s&token=%s&notify_url=%s'%(app_id,baoruan_user,pay_type_str,token,notify_url)
    
    return (0,query_url)


def confirm_baoruan_get_link_id(request):
    return ''


def confirm_baoruan(request,pay_channel={}):
#    app_id = request.POST.get('cid','')
    openid = request.POST.get('uid','')
    order_id = request.POST.get('order_id','')
    amount = request.POST.get('amount','')
    sign = request.POST.get('verifystring','')
    server_id = int(request.GET.get('s', 4))
    
    pay_amount = 0
    result_msg =  ''
    
    app_id = ''
    app_key = ''
    user_type = 20
    try:
        app_id = pay_channel.get_config_value('app_id','828')
        app_key = pay_channel.get_config_value('app_key','f70562807b9b4030bf26702cd5cbc680')
        user_type = int(pay_channel.get_config_value('user_type',20))
    except:
        result_msg =  'error_pay_conf'
    
    try:  
        sign_str = '%s%s%s%s%s'%(app_id,openid,order_id,amount,app_key)
        sign_str = md5(sign_str)
        print sign_str
        if sign == sign_str:
            pay_amount = float(amount)
            result_msg = '1'
        else:
            result_msg =  'errorSign'
 
    except Exception,e:
        result_msg = 'unknow error'
        print('confirm baoruan has error',e)

    return {'server_id':server_id,'user_type':user_type,'open_id':openid,'order_id':order_id,'amount':pay_amount,'remark':'','result_msg':result_msg}
 


#
#def confirm_baoruan(request,server_id=4,pay_way='baoruan'):
##    app_id = request.POST.get('cid','')
#    openid = request.POST.get('uid','')
#    order_id = request.POST.get('order_id','')
#    amount = request.POST.get('amount','')
#    sign = request.POST.get('verifystring','')
#    server_id = int(server_id)
#    try:
#        pay_channels = PayChannel.objects.using('read').filter(func_name=pay_way)
#        if len(pay_channels) > 0:
#            pay_channel = pay_channels[0]
#            app_id = pay_channel.get_config_value('app_id','828')
#            app_key = pay_channel.get_config_value('app_key','f70562807b9b4030bf26702cd5cbc680')
#            user_type = pay_channel.get_config_value('user_type',20)
#            
#            sign_str = '%s%s%s%s%s'%(app_id,openid,order_id,amount,app_key)
#            sign_str = md5(sign_str)
#            
#            if sign == sign_str:
#                pay_user = 0
#                if server_id > 0:
#                    try:
#                        conn = getConn(server_id)
#                        query_sql = "select player_id from player_%d where user_type=%d and link_key='%s'"%(server_id,user_type,openid)
#                        cursor = conn.cursor()
#                        cursor.execute(query_sql)
#                        pay_user_record = cursor.fetchone()
#                        if pay_user_record!=None:
#                            pay_user = int(pay_user_record[0])
#                        conn.close()
#                    except Exception,e:
#                        print('confirm baoruan db has error:%s'%e)
#                        
#                if pay_user>0:
#                    pay_actions = PayAction.objects.filter(order_id=order_id)
#                    if len(pay_actions)==0:
#                        the_action = PayAction()
#                        the_action.pay_type = pay_channel.id
#                        the_action.order_id = order_id
#                        the_action.server_id = server_id
#                        the_action.pay_user = pay_user
#                        the_action.post_amount = float(amount)
#                        if the_action.post_amount > 0:
#                            the_action.pay_amount = the_action.post_amount
#                            the_action.pay_gold = pay_channel.get_gold(the_action.pay_amount)
#                            the_action.extra = pay_channel.get_extra_amount(the_action.pay_amount)
#                            the_action.pay_status = 2
#                        else:
#                            the_action.pay_status = -2
#                        the_action.remark = ''
#                        the_action.pay_ip = request.META.get('REMOTE_ADDR','')
#                        the_action.query_id = the_action.get_query_id()
#                        the_action.safe_save()
#                        result_msg =  '1'
#                    else:
#                        result_msg =  'errorRepeat'
#                else:
#                    result_msg =  'errorUser'
#            else:
#                result_msg =  'errorSign'
#        else:
#            result_msg =  'errorChannel'
#    except Exception,e:
#        result_msg = 'unknow error'
#        print('confirm baoruan has error',e)
#
#    return render_to_response('pay/pay_post.html',{'pay_status':result_msg})
#    