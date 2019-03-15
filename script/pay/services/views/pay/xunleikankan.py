# -*- coding: utf-8 -*-
from django.http import HttpResponse
from services.views import md5
import datetime, time

def confirm_xunleikankan_get_link_id(request):
    return ''


def confirm_xunleikankan(request, pay_channel={}):
    #MchID    
    #MchOrderID    是    
    #UserName    是    
    #PayType    是    
    #ProCode    是    
    #PayNum    是    
    #Amount    是    
    #Signature    是   
    #Ip    否    
    #ServerID    否    
    app_key = pay_channel.get_config_value('app_key', '9@zi(v6bw0$k6fku')
    user_type = pay_channel.get_config_value('user_type', 51)
    
    MchID = request.GET.get('MchID', '')# 商户号
    MchOrderID = request.GET.get('MchOrderID', '')#迅雷支付订单号，唯一
    UserName = request.GET.get('UserName', '')#充值的迅雷账号数字ID 
    PayType = request.GET.get('PayType', '')#支付类别（默认0）
    ProCode = request.GET.get('ProCode', '')#产品代码，可扩展为充值优惠（需双方协商开发）
    PayNum = request.GET.get('PayNum', '')#数量（默认1），可扩展为充值赠送商品数量（需双方协商开发）
    Amount = request.GET.get('Amount', '')#订单金额（分）
    Signature = request.GET.get('Signature', '')# 数字签名
    Ip = request.GET.get('Ip', '')#充值的ip，此值不参与签名计算
    ServerID = request.GET.get('ServerID', '')#返回充值发生的服务器ID，它的值为3.3.1和3.3.2中所传入的serverid参数，此值不参与签名计算
    
    #Signature=md5(MchID=x&MchOrderID=y&UserName=z&PayType=t&ProCode=p&PayNum=n&Amount=a&Key=a).ToLower()
    sign = 'MchID=%s&MchOrderID=%s&UserName=%s&PayType=%s&ProCode=%s&PayNum=%s&Amount=%s&Key=%s' % (MchID, MchOrderID, UserName, PayType, ProCode, PayNum, Amount, app_key)
    sign = md5(sign)
    
    pay_amount = 0
    order_id = ''
    open_id = ''
    server_id = 0
    remark = ''
    result_msg = ''
    
    if Signature == sign:
        try:
            Amount = float(Amount)
            if Amount > 0:
                pay_amount = Amount / 100
                try:
                    UserName = UserName[4:]
                except Exception, ex:
                    print 'xunleikankan username is error'
                    print ex
                order_id = MchOrderID
                open_id = UserName
                server_id = int(ServerID)
                result_msg = return_xml(MchOrderID, UserName, Amount, app_key)
                remark = 'success'
        except Exception, ex:
            print 'xunleikankan error'
            print ex
    else:
        result_msg = 'sign error'
        
    return {"amount":pay_amount, "order_id":order_id ,"open_id":open_id, "user_type":user_type,"server_id":server_id,  "remark":remark, "result_msg":result_msg}

def return_xml(MchOrderID, UserName, Amount, app_key):
    #ReturnCode    是    返回值，详见后
    #MchID    是    商户号
    #MchOrderID    是    迅雷支付订单号，唯一
    #UserName    是    充值的迅雷账号数字ID
    #Amount    是    订单金额（分）
    #OrderDate    是    订单提交时间（yyyyMMddhhmmss）
    #OrderID    是    游戏方使用的订单号
    #PayDate    是    充值时间（yyyyMMddhhmmss）
    #ReturnMsg    是    返回信息
    #Signature    是    数字签名
    now = datetime.datetime.now()
    now_str = now.strftime('%Y%m%d%H%M%S')
    OrderDate = now_str
    PayDate = now_str
    OrderID = '%s%s' % (int(time.mktime(now.timetuple())), MchOrderID)
    sign = md5('ReturnCode=1&MchID=xl&MchOrderID=%s&UserName=%s&Amount=%s&OrderID=%s&PayDate=%s&Key=%s' % (MchOrderID, UserName, Amount, OrderID, PayDate, app_key))
    
    data = '''<?xml version="1.0" encoding="utf-8" ?> 
    <root>
      <ReturnCode>1</ReturnCode> 
      <MchID>xl</MchID>
      <MchOrderID>%s</MchOrderID> 
      <UserName>%s</UserName> 
      <Amount>%s</Amount>
      <OrderDate>%s</OrderDate> 
      <OrderID>%s</OrderID>
      <PayDate>%s</PayDate>
      <ReturnMsg>success</ReturnMsg> 
      <Signature>%s</Signature>
    </root>''' % (MchOrderID, UserName, Amount, OrderDate, OrderID, PayDate, sign)
    
    return data
    
def query_xunleikankan(request):
    UserName = request.GET.get('UserName', '')
    #md5(ReturnCode=r&MchID=x&UserName=y&Ticket=t&Key=a).ToLower()
    sign = md5('ReturnCode=1&MchID=xl&UserName=%s&Ticket=0&Key=%s' % (UserName, '9@zi(v6bw0$k6fku'))
    result_data = '''<?xml version="1.0" encoding="utf-8" ?><root><ReturnCode>1</ReturnCode><MchID>xl</MchID><UserName>%s</UserName><Ticket>0</Ticket><ReturnMsg></ReturnMsg><Signature>%s</Signature></root>''' % (UserName, sign)
    return HttpResponse(result_data)
    