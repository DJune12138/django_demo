# -*- coding: utf-8 -*-

from django.utils.http import urlquote
import urllib2

def pay_alipay(pay_action,pay_channel={},host_ip='service.fytxonline.com'):
    from services.alipay import sign_with_rsa_ali
#    partner = '2088701709437219'#'2088002040001775'#2088801536938559
#    seller = 'gzfeiyin2012@126.com'#'work@hucn.com'
    partner = pay_channel.get_config_value('partner','2088801536938559')
    seller = pay_channel.get_config_value('seller','gzyouaiwlcompany@163.com')

    subject = pay_channel.get_config_value('subject',u'风云天下')
    body = pay_channel.get_config_value('body',u'金币充值')
    notify_url = u'http://%s/service/confirm/alipay'%host_ip
    notify_url = urllib2.quote(notify_url)
#    notify_url = repr(notify_url).replace(r'\x', '%')
    sign_url = u'partner="%s"&seller="%s"&out_trade_no="%s"&subject="%s"&body="%s"&total_fee="%s"&notify_url="%s"'%(partner,seller,pay_action.query_id,subject,body,'%.2f'%pay_action.post_amount,notify_url)
    #print(sign_url)
    sign = sign_with_rsa_ali(sign_url.encode('utf-8'))
    
    pay_url = '%s&sign_type="RSA"&sign="%s"'%(sign_url,urlquote(sign))
    
    return (0,pay_url)



def confirm_alipay_get_link_id(request):
    return None

def confirm_alipay(request,pay_channel={}):
    from services.alipay import check_with_rsa_ali,parse_notify_data
    result_msg = 'fail'
    
    notify_data = request.POST.get('notify_data','')
    sign  = request.POST.get('sign','').encode('utf-8')
    
    sign_str = u'notify_data=%s'%notify_data
    sign_str = sign_str.encode('utf-8')
    notify_data = notify_data.encode('utf-8')
    #print(sign_str,sign)
    query_id = ''
    order_id = ''
    pay_amount = 0
    remark = ''
    if check_with_rsa_ali(sign_str, sign):
        try:
#            print(notify_data)
            notify_data = parse_notify_data(notify_data)
            if notify_data!=None:
                result_msg = 'success'

                if notify_data.trade_status == "TRADE_FINISHED" or notify_data.trade_status == "TRADE_SUCCESS":
                    query_id = notify_data.out_trade_no
                    order_id = notify_data.trade_no
                    pay_amount = float(notify_data.total_fee)
                remark = notify_data.trade_status

        except Exception,e:
            print('confirm alipay has an error:',e)
    

    return {'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

