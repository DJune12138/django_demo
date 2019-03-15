# -*- coding: utf-8 -*-

from django.utils.http import urlquote
import urllib2

def pay_alipay_new(pay_action,pay_channel={},host_ip='service.fytxonline.com'):
    from services.alipay import sign_with_rsa
#    partner = '2088701709437219'#'2088002040001775'#2088801536938559
#    seller = 'gzfeiyin2012@126.com'#'work@hucn.com'
    partner = pay_channel.get_config_value('partner','2088801536938559')
    seller = pay_channel.get_config_value('seller','gzyouaiwlcompany@163.com')
    private_key = pay_channel.get_config_value('private_key', '''-----BEGIN RSA PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBANQR95kNNrHo4glxvmdEn1Bma5U24NgOLl1EMF+4Ciw4fOC8TZzjw7rXqgRgI6NWXdDOmN2B140LNjXBly7Beq3qKOHhrWinzseRONkGU3wPeJO5VNjnCWU1m8fXilMhQHaHfdjvAh4aiZV1QZVewmjG7qs6iUaM1UxvprhzraKRAgMBAAECgYEAmROnD7k0A9PAZWTPNaeY/+YOPhTw08PYv8XazR0Bas4Thf0mYNsfi5zkwmfLEbnj2jdmrG1u9AZlyQPGZx+Ntu6ukzQk4NfKWLfKyOIB4OJ+rNeGZBiSir5j8C5+iMjOZQBAzdEJOwCx9B13bwP5RWHUmUZ8dLvdxt7+6djDSAECQQD5LviTQ9xP3bSchPVyjvhkz152PAlwC7uR4y46+xb2feaN0qu+zhXx18jSmNwojMWn24s1eu68ujrI0jCoKxxBAkEA2d8XmpXPP6XqUzPLF0lUyiBSB2lQp9JMSOlCAbKvS+Tk/NR/ufy0JmqfNrjkAnvv4lBKoqzPGpwLYYJS9UUyUQJAAm0Aon5goK5p2bQ5p3nY1TJnmwMOnHagxtTNWGmlWZT0L6FDZsIe2JHfNJ2kVwi3y+CJRGYD+PZfKCFTs+9ngQJAI0TC/Go9527DVP6wZK+hQysiPELnJJOdd7wSzFWRnPaLvwXjO0dWHlXqOiCKAIDxnzAiNN1GlWcnTHydU0kFUQJAa54pvMY6XYQoSbsFfjL2v5Xl1NyqJRTekThpzrm+GDHh592PWvkupppNHAezvaassfgb2/iJTk+foMFfPC6Szw==
-----BEGIN RSA PRIVATE KEY-----''')
    subject = pay_channel.get_config_value('subject',u'风云天下')
    body = pay_channel.get_config_value('body',u'金币充值')
    notify_url = u'http://%s/service/confirm/alipay_new'%host_ip
    notify_url = urllib2.quote(notify_url)
#    notify_url = repr(notify_url).replace(r'\x', '%')
    sign_url = u'partner="%s"&seller="%s"&out_trade_no="%s"&subject="%s"&body="%s"&total_fee="%s"&notify_url="%s"'%(partner,seller,pay_action.query_id,subject,body,'%.2f'%pay_action.post_amount,notify_url)
    #print(sign_url)
    sign = sign_with_rsa(sign_url.encode('utf-8'), private_key)
    
    pay_url = '%s&sign_type="RSA"&sign="%s"'%(sign_url,urlquote(sign))
    
    return (0,pay_url)



def confirm_alipay_new_get_link_id(request):
    return None

def confirm_alipay_new(request,pay_channel={}):
    from services.alipay import check_with_rsa,parse_notify_data
    result_msg = 'fail'
    public_key = pay_channel.get_config_value('public_key', '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCrCaD8EHqEXy+++qCWwv4q76eSTOw9UXVcHyonx5s4QQGdrzPLg7oOCmvLcsCkRhr9mstRKFEb7L3+C1MfPJH9ylbDn+HjchU6pVfVksMvFeTWMAs9U5/+Ob+wCjsnponUuFIUun5HzKabtXIFkwpGLyVkRQjQoSfdPO3S3LVFOQIDAQAB
-----END PUBLIC KEY-----''')
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
    if check_with_rsa(sign_str, sign, public_key):
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
            print('confirm alipay_new has an error:',e)
    

    return {'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

