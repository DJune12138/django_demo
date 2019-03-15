# -*- coding: utf-8 -*-
from django.utils.http import urlquote
from services.models.pay import PayChannel
from services.http import http_post
import hmac


def pay_yeepay(pay_action,pay_channel={},host_ip='service.fytxonline.com'):
#    merchant_id = 10011733833
#    merchant_key = 'GL257oHr34C5QM6o1Yf79sj56Cak907F5IMUy945IM832NvEj0D82B6qe83N'
    merchant_id = pay_channel.get_config_value('merchant_id',10011847951)
    merchant_key = pay_channel.get_config_value('merchant_key','Z4eahK78Vz41418G3k7b26psaY23QGW29K5121W43Q00p5TLIANc4QcI283q')
    merchant_key = merchant_key.encode('ascii')
    product_name = pay_channel.get_config_value('product_name','gold')
    pay_type_key = pay_channel.get_config_value('pay_type_key','yeepay')
    confirm_url = '%s/service/confirm/%s'%(host_ip,pay_type_key)
    status = {'-1':'签名较验失败或未知错误','1':'提交成功','2':'卡密成功处理过或者提交卡号过于频繁','5':'卡数量过多，目前最多支持10张卡','11':'订单号重复','66':'支付金额有误','95':'支付方式未开通','112':'业务状态不可用，未开通此类卡业务','8001':'卡面额组填写错误','8002':'卡号密码为空或者数量不相等'}
    
    if pay_channel==None:
        pay_channel = PayChannel.objects.using('read').get(id=pay_action.pay_type) 


    data=[
    '',
    ('p0_Cmd','ChargeCardDirect'),
    ('p1_MerId',merchant_id),
    ('p2_Order',pay_action.query_id),
    ('p3_Amt','%.2f'%pay_action.post_amount),
    ('p4_verifyAmt','false'),
    ('p5_Pid',product_name),
    ('p6_Pcat',''),
    ('p7_Pdesc',''),
    ('p8_Url',confirm_url),
    ('pa_MP','None'),
    
    ('pa7_cardAmt','%.2f'%pay_action.post_amount),
    ('pa8_cardNo',pay_action.card_no),
    ('pa9_cardPwd',pay_action.card_pwd),
    ('pd_FrpId',pay_channel.link_id),
    ('pr_NeedResponse','1')
    ]
    #print(data)
    origin_str=reduce(lambda x,y:"%s%s"%(x,urlquote(y[1])),data)
    
    origin_str = origin_str.encode("GBK")
    #print(origin_str)
    mac=hmac.new(merchant_key)
    mac.update(origin_str)
    sign_str = mac.hexdigest()
    query= "".join(["https://www.yeepay.com/app-merchant-proxy/command.action?",reduce(lambda x,y:"%s&%s=%s"%(x,y[0],urlquote(y[1])),data).lstrip("&"),"&hmac=",sign_str])
    
    query=query.encode("GBK")
    result_code = 0
    result = ''
    try:
        result = http_post(query)
        for item in result.split('\n'):
            if item.split('=')[0]=='r1_Code':
                result_code = item.split('=')[1]
                break
        result = status.get(result_code,'')
        result_code = int(result_code)
        print(query,result_code,result)
    except Exception,e:
        print('pay yeepay error:',e)
    return (result_code,result)


def confirm_yeepay_get_link_id(request):
    return ''
    
def confirm_yeepay(request,pay_channel={}):
    merchant_key = pay_channel.get_config_value('merchant_key','Z4eahK78Vz41418G3k7b26psaY23QGW29K5121W43Q00p5TLIANc4QcI283q')
    merchant_key = merchant_key.encode('ascii')
    status = {'0':'销卡成功，订单成功','1':'销卡成功，订单失败','7':'卡号卡密或卡面额不符合规则','1002':'本张卡密您提交过于频繁，请您稍后再试','1003':'不支持的卡类型（比如电信地方卡）','1004':'密码错误或充值卡无效','1006':'充值卡无效','1007':'卡内余额不足','1008':'余额卡过期（有效期1个月）','1010':'此卡正在处理中','10000':'未知错误','2005':'此卡已使用','2006':'卡密在系统处理中','2007':'该卡为假卡','2008':'该卡种正在维护','2009':'浙江省移动维护','2010':'江苏省移动维护','2011':'福建省移动维护','2012':'辽宁省移动维护','2013':'该卡已被锁定','2014':'系统繁忙，请稍后再试','3001':'卡不存在','3002':'卡已使用过','3003':'卡已作废','3004':'卡已冻结','3005':'卡未激活','3006':'密码不正确','3007':'卡正在处理中','3101':'系统错误','3102':'卡已过期'}
    
    keys = ['r0_Cmd','r1_Code','p1_MerId','p2_Order','p3_Amt','p4_FrpId','p5_CardNo','p6_confirmAmount','p7_realAmount','p8_cardStatus','p9_MP','pb_BalanceAmt','pc_BalanceAct']
     
    try:
        print 'yeepay request GET::::::'
        print request.GET
        print 'end for yeepay request GET '
    except Exception, ex:
        print 'pring yeepay log file error'
        print ex
    
    
    sign = request.GET.get('hmac','')
    origin_str = reduce(lambda x,y:"%s%s"%(x,y),[request.GET.get(k,'') for k in keys])  
    
    mac=hmac.new(merchant_key)
    mac.update(origin_str)
    sign_str = mac.hexdigest()
    pay_amount = 0
    query_id = ''
    remark = ''
    if sign==sign_str:
        try:
            query_id = request.GET.get('p2_Order','')
            if request.GET.get('r1_Code','') == '1':
                pay_amount = float(request.GET.get('p3_Amt','0.00'))
            else:
                pay_amount = 0
               
            remark = status.get(request.GET.get('p8_cardStatus','0'))
                    
            result_msg = 'success'
        except Exception,e:
            print('confirm yeepay has error',e)
    else:
        result_msg = 'sign error'

    return {'query_id':query_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

