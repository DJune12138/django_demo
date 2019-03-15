# -*- coding: utf-8 -*-
from services.views import md5
import urllib
#沈阳林科             联通接入
def confirm_linktech_get_link_id(request):
    return request.POST.get('paytype', '')

def confirm_linktech(request,pay_channel):
    app_id = pay_channel.get_config_value('app_id', '')
    app_key = pay_channel.get_config_value('app_key','')
    
    g = lambda x,y:request.POST.get(x,y)
    
    result = g('result','')    #int    4    调用结果 0 用户购买成功。 1 用户购买失败。购买失败时只有errorstr有值。
    paymentid = g('paymentid', '')   #String    订单id    字符串，唯一值，长度不定，100字符限制
    errorstr = g('errorstr', '')   #String    UTF（限制100汉字）    执行订购内容为空  失败：失败原因 返回参数为URLEncoder.encode(errorstr, "UTF-8");需解码
    company  = g('company', '')  #String    UTF（限制24个英文字符，12汉字）    公司名称（成功则不为空）返回参数为URLEncoder.encode(company, "UTF-8");需解码
    channelid = g('channelid', '')   #String    UTF（3位字符）    游戏厂商自己的各渠道号id
    softgood = g('softgood','')   #String    UTF（限制24个英文字符，12汉字）    商品名（成功则不为空）返回参数为URLEncoder.encode(softgood, "UTF-8");需解码
    customer = g('customer', '')   #String    UTF（限制待定）    用户在软件的注册id。（成功则不为空）返回参数为URLEncoder.encode(customer, "UTF-8");需解码
    money = g('money', '')   #String    UTF（限制待定）    商品价格，单位：分
    softserver = g('softserver','')   #String    UTF（限制待定）    服务器区名（主要用于网游，没有则为空）返回参数为URLEncoder.encode(softserver, "UTF-8");需解码
    playername = g('playername', '')   #String    UTF（限制待定）    该服务器上的用户所选人物名（主要用于网游，没有则为空）返回参数为URLEncoder.encode(playername, "UTF-8");需解码
    date = g('date', '')   #String    UTF    yyyy-MM-dd HH:mm:ss
    pkey = g('pkey', '')   #String    UTF    用于数据校验  gamecode + keys + money + result + paymentid + customer +serverkey的md5值
    paytype = g('paytype', '')   #String    UTF（3位字符）    支付方式: （成功则不为空）目前包括神州付：SZF， 短代：SMS 支付宝：ZFB
    customorderno = g('customorderno', '')#String    UTF(16位字符）    自定义订单号
    gamecode = g('gamecode', '')   #String    UTF UTF（6英文字符）    游戏id

    
    
    server_sign = u'%s%s%s%s%s%s%s' % (gamecode ,app_id, money, result, paymentid, customer, app_key)
    server_sign = md5(server_sign)
    
    pay_amount = 0
    player_id = 0
    server_id = 0 
    order_id = ''
    remark = ''
    result_msg = '0'
    
    if pkey == server_sign:
        result_msg = '1'
        try: 
            amount = float(money)/100
            order_id = paymentid
            tmp = customorderno.split('_')
            server_id = int(tmp[0])
            player_id = int(tmp[1])
            if amount > 0 and int(result) == 0:
                result_msg = 'success'
                pay_amount = amount
        except Exception ,ex:
            result_msg = 'error'
            remark = 'comfrim guguo error:', ex
    else:
        result_msg = 'errorSign'
        remark = 'sign error'
    
    return {'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}
     
    
    
    