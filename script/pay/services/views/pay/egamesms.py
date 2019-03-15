# -*- coding: utf-8 -*-
from services.models import PayAction

def pay_egamesms(the_action,pay_channel = {},service_url='service.fytxonline.com'):
    return 1,the_action.id
    

def confirm_egamesms_get_link_id(request):
    smscontent = request.GET.get('smscontent', '')
    if '' == smscontent:
        return ''
    link_id = '' 
    try:
        link_id = smscontent[10:22]
    except Exception, ex:
        print 'egame get link id error :', ex
        return ''
    
    return link_id
    
    
def confirm_egamesms(request,pay_channel={}):
    ip = ''
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):  
        ip =  request.META['HTTP_X_FORWARDED_FOR']  
    else:  
        ip = request.META['REMOTE_ADDR']
    
    remove_ip = pay_channel.get_config_value('ip', '202.102.39.')
    
    my_cpcode = pay_channel.get_config_value('app_id', 'C09141')
    
    resultcode = request.GET.get('resultcode', '')
    resultmsg = request.GET.get('resultmsg', '')
    smscontent = request.GET.get('smscontent', '')
    
    print '*********** egame sms confirm *********'
    print 'smscontent'
    print smscontent
    print 'resultcode'
    print resultcode
    
    
    t_query_id = resultcode[0:7]
    t_order_id = resultcode[7:12]
    status_code = resultcode[12:14]
    
    amount = smscontent[0:2]
    
    pay_amount = 0
    query_id = 0
    server_id = 0
    player_id = 0
    order_id = ''
    result_msg = ''
    remark = ''
    headers = {}
    is_new = request.REQUEST.get('payType','') == 'isagSmsPay'
    if is_new:# 新的回调参数:
        status_code = request.GET.get('resultCode')
        
    if 0 == ip.find(remove_ip): 
        result_msg = 'success'
        try: 
            if  status_code == '00':
                if is_new:
                    the_action_id = request.GET.get('cpparam',0)
                    t_order_id = the_action_id
                    amount = request.GET.get('cost',0)
                    result_msg = "ResultCode:%s<br />CpParam:%s"%(status_code,the_action_id)
                    print result_msg
                else:
                    the_action_id = int(t_query_id, 16)
                the_action = PayAction.objects.get(id = the_action_id)
                if None != the_action:
                    print 'the_action.post_amoutn:'
                    print (the_action.post_amount, int(amount))
                    if int(the_action.post_amount) == int(amount):
                        pay_amount = amount
                        server_id = the_action.server_id
                        player_id = the_action.pay_user
                        order_id = t_order_id
                        query_id = the_action.id
                        headers["cpparam"] = the_action_id
                else:
                    remark = 'the_action is none, id:%s' % the_action_id
            else:
                remark = resultmsg
        except Exception, ex:
            remark = 'internal error'
            pay_amount = 0
            print 'confirm egame sms error', ex
        
    else:
        remark = '违法ip'
    
    _r = {"server_id": server_id, "player_id":player_id, "query_id":query_id, "order_id":order_id, "amount": pay_amount, "result_msg":result_msg, "remark":remark,"headers":headers}
    print _r
    return _r
#***************************以下暂时不用， 需要  更新  pay/__ini__py 才能使用  目前大陆后台版本不能正常使用     以下方式是使用 返回 pay_action id 
#def confirm_egamesms_new(request,pay_channel={}):
#    ip = ''
#    if request.META.has_key('HTTP_X_FORWARDED_FOR'):  
#        ip =  request.META['HTTP_X_FORWARDED_FOR']  
#    else:  
#        ip = request.META['REMOTE_ADDR']
#    
#    remove_ip = pay_channel.get_config_value('ip', '202.102.39.')
#    
#    my_cpcode = pay_channel.get_config_value('app_id', 'C09141')
#    
#    resultcode = request.GET.get('resultcode', '')
#    resultmsg = request.GET.get('resultmsg', '')
#    smscontent = request.GET.get('smscontent', '')
#    
#    print '*********** egame sms confirm *********'
#    print 'smscontent'
#    print smscontent
#    print 'resultcode'
#    print resultcode
#    
#    
#    t_query_id = resultcode[0:7]
#    t_order_id = resultcode[7:12]
#    status_code = resultcode[12:14]
#    
#    amount = smscontent[0:2]
#    print (int(t_query_id, 16), t_order_id, status_code, amount)
#    pay_amount = 0
#    order_id = ''
#    result_msg = ''
#    remark = ''
#    if 0 != ip.find(remove_ip) or True: 
#        result_msg = 'success'
#        try: 
#            amount = float(amount)
#            if  status_code == '00' and amount > 0:
#                the_action_id = int(t_query_id, 16) 
#                pay_amount = float(amount)
#                order_id = t_order_id
#            else:
#                remark = resultmsg
#        except Exception, ex:
#            remark = 'internal error'
#            pay_amount = 0
#            print 'confirm egame sms error', ex
#    else:
#        remark = '违法ip'
#    
#    return {"pay_action_id":the_action_id, "order_id":order_id, "amount": pay_amount, "result_msg":result_msg, "remark":remark}
