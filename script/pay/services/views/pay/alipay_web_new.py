# -*- coding: utf-8 -*-

from services.http import http_post
import json,time,urllib2,re


def pay_alipay_web_new(pay_action,pay_channel={},host_ip='service.fytxonline.com'):
    from services.alipay import sign_with_rsa,decrypt_with_rsa
    pay_url = ''
    
    private_key = pay_channel.get_config_value('private_key', '''-----BEGIN RSA PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBANQR95kNNrHo4glxvmdEn1Bma5U24NgOLl1EMF+4Ciw4fOC8TZzjw7rXqgRgI6NWXdDOmN2B140LNjXBly7Beq3qKOHhrWinzseRONkGU3wPeJO5VNjnCWU1m8fXilMhQHaHfdjvAh4aiZV1QZVewmjG7qs6iUaM1UxvprhzraKRAgMBAAECgYEAmROnD7k0A9PAZWTPNaeY/+YOPhTw08PYv8XazR0Bas4Thf0mYNsfi5zkwmfLEbnj2jdmrG1u9AZlyQPGZx+Ntu6ukzQk4NfKWLfKyOIB4OJ+rNeGZBiSir5j8C5+iMjOZQBAzdEJOwCx9B13bwP5RWHUmUZ8dLvdxt7+6djDSAECQQD5LviTQ9xP3bSchPVyjvhkz152PAlwC7uR4y46+xb2feaN0qu+zhXx18jSmNwojMWn24s1eu68ujrI0jCoKxxBAkEA2d8XmpXPP6XqUzPLF0lUyiBSB2lQp9JMSOlCAbKvS+Tk/NR/ufy0JmqfNrjkAnvv4lBKoqzPGpwLYYJS9UUyUQJAAm0Aon5goK5p2bQ5p3nY1TJnmwMOnHagxtTNWGmlWZT0L6FDZsIe2JHfNJ2kVwi3y+CJRGYD+PZfKCFTs+9ngQJAI0TC/Go9527DVP6wZK+hQysiPELnJJOdd7wSzFWRnPaLvwXjO0dWHlXqOiCKAIDxnzAiNN1GlWcnTHydU0kFUQJAa54pvMY6XYQoSbsFfjL2v5Xl1NyqJRTekThpzrm+GDHh592PWvkupppNHAezvaassfgb2/iJTk+foMFfPC6Szw==
-----BEGIN RSA PRIVATE KEY-----''')
    partner = pay_channel.get_config_value('partner','2088801536938559')
    seller = pay_channel.get_config_value('seller','gzyouaiwlcompany@163.com')

    subject = pay_channel.get_config_value('subject','风云天下金币充值')
    
    req_data='''<direct_trade_create_req><subject>%s</subject><out_trade_no>%s</out_trade_no><total_fee>%d</total_fee><seller_account_name>%s</seller_account_name><call_back_url>http://%s/service/callback/alipay_web_new</call_back_url><notify_url>http://%s/service/confirm/alipay_web_new</notify_url><out_user>%d</out_user></direct_trade_create_req>'''%(subject,pay_action.query_id,pay_action.post_amount,seller,host_ip,host_ip,pay_action.pay_user)
    
    post_data = 'format=xml&partner=%s&req_data=%s&req_id=%d&sec_id=0001&service=alipay.wap.trade.create.direct&v=2.0'%(partner,req_data,int(time.time()*10))

    sign = sign_with_rsa(post_data, private_key)
    sign = urllib2.quote(sign)
    post_data = '%s&sign=%s'%(post_data,sign)

    query_url = 'http://wappaygw.alipay.com/service/rest.htm'
    
    result = http_post(query_url,post_data)
#    print(post_data,result)
    if result.find('res_error')==-1:
        result = ('{"%s"}'%result).replace('=','":"').replace('&','","')
        result = json.loads(result).get('res_data','')

        result = urllib2.unquote(result)
        result = decrypt_with_rsa(result,private_key)
        print(result)
        reb = re.compile('<[^<]+>')
        result = reb.sub('',result)
        print(result)
        
        req_data = '<auth_and_execute_req><request_token>%s</request_token></auth_and_execute_req>'%result
        
        post_data = 'format=xml&partner=%s&req_data=%s&sec_id=0001&service=alipay.wap.auth.authAndExecute&v=2.0'%(partner,req_data)

        sign = sign_with_rsa(post_data, private_key)
        sign = urllib2.quote(sign)
        post_data = '%s&sign=%s'%(post_data,sign)
        pay_url = '%s?%s'%(query_url,post_data)
    else:
        pass
    return (0,pay_url)



def confirm_alipay_web_new_get_link_id(request):
    return ''

def confirm_alipay_web_new(request,pay_channel={}):
#    print(request.POST)
    from services.alipay import check_with_rsa,decrypt_with_rsa,parse_notify_data
    result_msg = 'fail'

    public_key = pay_channel.get_config_value('public_key', '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCrCaD8EHqEXy+++qCWwv4q76eSTOw9UXVcHyonx5s4QQGdrzPLg7oOCmvLcsCkRhr9mstRKFEb7L3+C1MfPJH9ylbDn+HjchU6pVfVksMvFeTWMAs9U5/+Ob+wCjsnponUuFIUun5HzKabtXIFkwpGLyVkRQjQoSfdPO3S3LVFOQIDAQAB
-----END PUBLIC KEY-----''')
    notify_data = request.POST.get('notify_data','')#.encode('utf-8')
    sign  = request.POST.get('sign','').encode('utf-8')
    notify_data = decrypt_with_rsa(notify_data, public_key)
    service = request.POST.get('service','')#.encode('utf-8')
    ver = request.POST.get('v','')#.encode('utf-8')
    sec_id = request.POST.get('sec_id','')#.encode('utf-8')
    notify_data = notify_data.decode('utf-8')
    sign_str = u'service=%s&v=%s&sec_id=%s&notify_data=%s'%(service,ver,sec_id,notify_data)
    sign_str = sign_str.encode('utf-8')
    #print(sign_str)
    pay_amount = 0
    query_id = ''
    order_id = ''
    remark = ''
    if check_with_rsa(sign_str, sign, public_key):
        try:
            notify_data = notify_data.encode('utf-8')
            print(notify_data)
            notify_data = parse_notify_data(notify_data)
 
            if notify_data!=None:
                result_msg = 'success'

                if notify_data.trade_status == "TRADE_FINISHED" or notify_data.trade_status == "TRADE_SUCCESS":
                    pay_amount = float(notify_data.total_fee)
                    query_id = notify_data.out_trade_no
                    order_id = notify_data.trade_no
                remark = notify_data.trade_status
        except Exception,e:
            print('confirm alipay_web_new has an error:',e)
    else:
        result_msg = 'error sign'

    return {'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

