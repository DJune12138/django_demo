# -*- coding: utf-8 -*-
from services.views import md5
 

def confirm_xdwan_get_link_id(request):
    return ''

def confirm_xdwan(request, pay_channel={}):
    app_key = pay_channel.get_config_value('app_key', 'FY010-XDWPAY-LEDOU-VN8KL7J-jawd-29468-KY54SG')
    user_type = int(pay_channel.get_config_value('user_type', 38))
    orderStatus = request.GET.get('orderStatus', '')#0-成功； 1订单号重复  2 签名错误3 服务器繁忙  4 角色不存在 9 未知错 
    
    userid = request.GET.get('userid', '')#平台用户ID(唯一标识)
    serverid = request.GET.get('serverid', '')#游戏区服(s1、s2、s3...)
    orderid = request.GET.get('orderid', '')#平台订单号
    tstamp = request.GET.get('tstamp', '')
    payType = request.GET.get('payType', '')#支付类型，如：神州行、电信卡等(可选)
    amount = request.GET.get('amount', '')#单位(RMB元)
    sign = request.GET.get('sign', '')
    
    #Sign=md5(userId+serverid+orderid+tstamp+amount+key)
    
    server_sign = '%s%s%s%s%s%s' % (userid, serverid, orderid, tstamp, amount, app_key)
    print server_sign
    server_sign = md5(server_sign)
    print (sign, server_sign)
    
    remark = ''
    result_msg = ''
    pay_amount = 0
    server_id = 0
    order_id = ''
    open_id = ''
    #err_map = {"1":"订单号重复", "2":"签名错误", "3": "服务器繁忙" , "4": "角色不存在","9": "未知错 "}
    
    if sign == server_sign:
        result_msg = '0'
        try:
            #status_code = str(orderStatus).strip()
            #if status_code == '0':
            pay_amount = float(amount)
            server_id = int(serverid)
            order_id = orderid
            open_id = userid 
            #else:
                #remark = err_map.get(status_code, '未知错误')
                
        except Exception, ex:
            print 'xdwan error :', ex 
    else:
        remark = '签名错误'
    
    return {"amount":pay_amount, "order_id":order_id ,"open_id":open_id, "user_type":user_type,"server_id":server_id,  "remark":remark, "result_msg":result_msg}
