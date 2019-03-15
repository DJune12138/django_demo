# -*- coding: utf-8 -*-
 
from services.http import http_post
from xml.dom import minidom

def pay_feiliu(pay_action,pay_channel = {},host_ip='service.fytxonline.com'):
    from services.alipay import encrypt_with_rsa_feiliu,getNodeTextByTagName
    product_id = '100003'
    company_id = '100004'
    channel_list = {'0000840000':'100002',
                    '0000990000':'100003',
                    '0001000000':'100004',
                    '0001010000':'100005',
                    '0001020000':'100006',
                    "0001650000":"100661",
                    "0001660000":"100662",
                    "0001670000":"100663",
                    "0001680000":"100664",
                    "0001690000":"100665"
    }
    channel_id = channel_list.get(pay_action.channel_key, pay_channel.get_config_value(pay_action.channel_key, '100002'))               
    '''
    pay_channel.link_id = 103
    pay_action.query_id = '10000410000001'
    pay_action.post_amount = 10
    pay_action.pay_amount = 100
    pay_action.card_no = '12295150269929492'
    pay_action.card_pwd = '151728418901161405'
    '''
    custom = ''
    
    #OrderId|ProductId|CompanyId|ChannelId|OrderType|Denomination|CardNO|CardPwd|Amount|MerPriv
    sign_str = u'%s|%s|%s|%s|%s|%s|%s|%s|%s|%s'%(pay_action.query_id,product_id,company_id,channel_id,pay_channel.link_id,pay_action.post_amount,pay_action.card_no,pay_action.card_pwd,pay_action.post_amount*100,custom)
    
    sign = encrypt_with_rsa_feiliu(sign_str.encode('utf-8'))
    #print(sign_str,sign)
    post_data = '''<Request>
                        <OrderId>%s</OrderId>
                        <ProductId>%s</ProductId>
                        <CompanyId>%s</CompanyId>
                        <ChannelId>%s</ChannelId>
                        <OrderType>%s</OrderType>
                        <Denomination>%s</Denomination>
                        <CardNO>%s</CardNO>
                        <CardPwd>%s</CardPwd>
                        <Amount>%s</Amount>
                        <MerPriv>%s</MerPriv>
                        <VerifyString>%s</VerifyString>
                    </Request>'''%(pay_action.query_id,product_id,company_id,channel_id,pay_channel.link_id,pay_action.post_amount,pay_action.card_no,pay_action.card_pwd,pay_action.post_amount*100,custom,sign)
    #print(post_data)
    pay_url = 'http://pay.feiliu.com/order/billinterfacepython'
    result_code = 0
    result_msg = ''
#    if True:
    try:
        result = http_post(pay_url,post_data,'xml')

        if result != '':
            xml_dom = minidom.parseString(result)
            xml_root = xml_dom.documentElement
            return_code = getNodeTextByTagName(xml_root,'Ret')
            if return_code == '0':
                result_code = 1
            else:
                result_code = 0
            result_msg = getNodeTextByTagName(xml_root,'RetMsg')
    except Exception,e:
        print('pay feiliu has error',e)
    #print(result_code,result_msg)
    return (result_code,result_msg)



def confirm_feiliu_get_link_id(request):
    return ''


def confirm_feiliu(request, pay_channel={}):
    from services.alipay import decrypt_with_rsa_feiliu,getNodeTextByTagName
    #print(request.GET,request.raw_post_data)
    product_id = ''
    result_msg = 0
    if request.method != 'POST':
        result_msg = '<?xml version="1.0" encoding="utf-8"?><Response><Ret>%d</Ret></Response>'%result_msg        
        return {'amount':0, 'result_msg':result_msg}
    else:
        post_data = request.raw_post_data
    
    try:
        product_id = pay_channel.get_config_value('product_id', '100003')
    except:
        result_msg = -1
    
    status = {'0':'销卡成功，订单成功','1':'销卡成功，订单失败','7':'卡号卡密或卡面额不符合规则','1002':'本张卡密您提交过于频繁，请您稍后再试','1003':'不支持的卡类型（比如电信地方卡）','1004':'密码错误或充值卡无效','1006':'充值卡无效','1007':'卡内余额不足','1008':'余额卡过期（有效期1个月）','1010':'此卡正在处理中','10000':'未知错误','2005':'此卡已使用','2006':'卡密在系统处理中','2007':'该卡为假卡','2008':'该卡种正在维护','2009':'浙江省移动维护','2010':'江苏省移动维护','2011':'福建省移动维护','2012':'辽宁省移动维护','2013':'该卡已被锁定','2014':'系统繁忙，请稍后再试','3001':'卡不存在','3002':'卡已使用过','3003':'卡已作废','3004':'卡已冻结','3005':'卡未激活','3006':'密码不正确','3007':'卡正在处理中','3101':'系统错误','3102':'卡已过期'}
    
    xml_dom = minidom.parseString(post_data)
    root_dom = xml_dom.getElementsByTagName("Request")[0]
    
    order_id = getNodeTextByTagName(root_dom,'FLOrderId')
    query_id = getNodeTextByTagName(root_dom,'OrderId')
    #product_id = getNodeTextByTagName(root_dom,'ProductId')
    card_no = getNodeTextByTagName(root_dom,'CardNO')
    amount = getNodeTextByTagName(root_dom,'Amount')
    result = getNodeTextByTagName(root_dom,'Ret')
    result_code = getNodeTextByTagName(root_dom,'CardStatus')
    custom = getNodeTextByTagName(root_dom,'MerPriv')
    sign = getNodeTextByTagName(root_dom,'VerifyString')
 
    sign_str = '%s|%s|%s|%s|%s|%s|%s|%s'%(order_id,query_id,product_id,card_no,amount,result,result_code,custom)
    
    sign_str_src = decrypt_with_rsa_feiliu(sign)
    print(sign_str,sign_str_src)

    pay_amount = 0
    remark = ''
    if sign_str==sign_str:
        try:
            
            if int(result)==1:
                pay_amount = float(amount)/100
            else:
                pay_amount = 0 
                remark =  status.get(result_code,'未知错误') 
                
            result_msg = 1  
        except Exception,e:
            result_msg = -1
            print('confirm feiliu has error',e)
    result_msg = '<?xml version="1.0" encoding="utf-8"?><Response><Ret>%d</Ret></Response>'%result_msg        
    return {'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}














#
#def confirm_feiliu(request):
#    from services.alipay import decrypt_with_rsa_feiliu,getNodeTextByTagName
#    print(request.GET,request.raw_post_data)
#    product_id = '100003'
#    result_msg = 0
#    if request.method != 'POST':
#        result_msg = '<?xml version="1.0" encoding="utf-8"?><Response><Ret>%d</Ret></Response>'%result_msg        
#        return render_to_response('pay/pay_post.html',{'pay_status':result_msg})
#    else:
#        post_data = request.raw_post_data
#        
#    status = {'0':'销卡成功，订单成功','1':'销卡成功，订单失败','7':'卡号卡密或卡面额不符合规则','1002':'本张卡密您提交过于频繁，请您稍后再试','1003':'不支持的卡类型（比如电信地方卡）','1004':'密码错误或充值卡无效','1006':'充值卡无效','1007':'卡内余额不足','1008':'余额卡过期（有效期1个月）','1010':'此卡正在处理中','10000':'未知错误','2005':'此卡已使用','2006':'卡密在系统处理中','2007':'该卡为假卡','2008':'该卡种正在维护','2009':'浙江省移动维护','2010':'江苏省移动维护','2011':'福建省移动维护','2012':'辽宁省移动维护','2013':'该卡已被锁定','2014':'系统繁忙，请稍后再试','3001':'卡不存在','3002':'卡已使用过','3003':'卡已作废','3004':'卡已冻结','3005':'卡未激活','3006':'密码不正确','3007':'卡正在处理中','3101':'系统错误','3102':'卡已过期'}
#    
#    xml_dom = minidom.parseString(post_data)
#    root_dom = xml_dom.getElementsByTagName("Request")[0]
#    
#    feiliu_order_id = getNodeTextByTagName(root_dom,'FLOrderId')
#    order_id = getNodeTextByTagName(root_dom,'OrderId')
#    #product_id = getNodeTextByTagName(root_dom,'ProductId')
#    card_no = getNodeTextByTagName(root_dom,'CardNO')
#    amount = getNodeTextByTagName(root_dom,'Amount')
#    result = getNodeTextByTagName(root_dom,'Ret')
#    result_code = getNodeTextByTagName(root_dom,'CardStatus')
#    custom = getNodeTextByTagName(root_dom,'MerPriv')
#    sign = getNodeTextByTagName(root_dom,'VerifyString')
#
##    feiliu_order_id = '133761617309'
##    order_id = '10000410000001'
##    product_id = '100003'
##    card_no = '12295150269929492'
##    amount = '100'
##    result = '2'
##    result_code = '1008'
##    custom = 'testinformation'
##    sign = 'ijpgw1lxAcktAJ/vlqWboIcjLyiazyugyKk5eK5cPclCSEuFK0XdH4Mm+rI+IM7rOJ9p1rwKX5hqrLntBOKFQZjBeBXbHjSSiqqx7aUrjsuME5kn7kmz62l3B2Xmgzmz0OooV1DgzcV7nfQ56rP2OBCRjI8knUVFWSzbrLhYQxY='
##    #FLOrderId|OrderId|ProductId|CardNO|Amount|Ret|CardStatus|custom
#    
#    sign_str = '%s|%s|%s|%s|%s|%s|%s|%s'%(feiliu_order_id,order_id,product_id,card_no,amount,result,result_code,custom)
##    print(sign_str)
#    sign_str_src = decrypt_with_rsa_feiliu(sign)
#    print(sign_str,sign_str_src)
#    
#    if sign_str==sign_str:
#        try:
#            list_action = PayAction.objects.using('write').filter(query_id=order_id)
#            if len(list_action)>0 :
#                the_action = list_action[0]
#                pay_channel = PayChannel.objects.using('read').get(id=the_action.pay_type)
#                if the_action.pay_status < 2:
#                    the_action.order_id = feiliu_order_id
#                    the_action.post_amount = float(amount)/100
#                    if int(result)==1:
#                        the_action.pay_amount = the_action.post_amount
#                        the_action.pay_gold = the_action.pay_amount * pay_channel.exchange_rate
#                        the_action.pay_status = 2
#                    else:
#                        the_action.remark = status.get(result_code,'未知错误')
#                        the_action.pay_status = -2
#                    the_action.save(using='write')
#                    result_msg = 1
#                else:
#                    result_msg = 2
#            else:
#                result_msg = 0
#        except Exception,e:
#            result_msg = -1
#            print('confirm feiliu has error',e)
#    result_msg = '<?xml version="1.0" encoding="utf-8"?><Response><Ret>%d</Ret></Response>'%result_msg        
#    return render_to_response('pay/pay_post.html',{'pay_status':result_msg})



