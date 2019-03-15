# -*- coding: utf-8 -*-
from services.models import PayAction
from services.http import http_post
from xml.dom import minidom
from xml.etree import ElementTree
from services.alipay import getNodeTextByTagName
from django.http import HttpResponse


def pay_cmmm(payAction,pay_channel={},host_ip='service.fytxonline.com'):
    return (1,payAction.id)
    

def confirm_cmmm_get_link_id(request):
    return ''
#应用编码：    300002788609
#app key：    4528EBE65421DF04
def confirm_cmmm(request, pay_channel={}):
    
    request_xml = request.raw_post_data
    print 'cmmm xml:'
    print request_xml
    
    t_TradeID = ''
    t_OrderID = ''
    t_TotalPrice = 0
    t_ExData = ''
    remark = ''
    try:
        t_TradeID, t_OrderID, t_TotalPrice, t_ExData = parse_notify_data(request_xml)
        print 'TradeID:', t_TradeID
        print 't_OrderID:', t_OrderID
        print 't_TotalPrice:', t_TotalPrice
        print 't_ExData:', t_ExData
    except Exception, ex:
        print 'parser notify xml error'
        print ex
    
    app_id = pay_channel.get_config_value('app_id', '300002904622')
    request_url = pay_channel.get_config_value('request_url', 'http://ospd.mmarket.com:8089/trust')
   
    #result_code, TotalPrice, ExData, remark = query_order(t_TradeID, t_OrderID, app_id, request_url)
    #if -1 == result_code:
    #    result_code_1, TotalPrice, ExData, remark = query_order(t_TradeID, t_OrderID, app_id, request_url)
        
    #查单返回的TotaPrice永远为0 ExData 为空.....??
    
    
    #回调先让订单失败， 查单交给客户端， 因为没有签名，  充值回调不会重复通知所以先获取订单好pay接口， 
    
    server_id = 0
    player_id = 0
    order_id = ''
    pay_amount = 0
    query_id = ''
    result_msg = get_rep_data(4000)
    if t_TotalPrice > 0 and t_ExData != '':
        try:
            tmp = t_ExData.split('_')
            server_id = tmp[0]
            player_id = tmp[1]
            server_id = int(server_id)
            player_id = int(player_id)
            query_id = tmp[2]
            order_id = t_OrderID
            pay_amount = t_TotalPrice / 100 #收到回调直接成功了...
            #remark = '%s`%s`%s' (t_TotalPrice / 100, app_id, request_url)
            result_msg = get_rep_data(0)
        except Exception, ex:
            print 'confirm cmmm error'
            result_msg = get_rep_data(1)
            print ex

    
    return {'server_id':server_id, 'player_id':player_id,'query_id':query_id ,'order_id':order_id, 'amount':pay_amount, 'remark':remark, 'result_msg':result_msg}


def query_cmmm(request):
    return HttpResponse(0)
    OrderID = request.GET.get('orderID', request.POST.get('orderID', ''))
    Paycode = request.GET.get('paycode', request.POST.get('paycode', ''))
    tradeID = request.GET.get('tradeID', request.POST.get('tradeID', ''))
    ORDERTYPE = request.GET.get('ordertype', request.POST.get('ordertype', ''))
    QueryID = request.GET.get('QueryID', request.POST.get('QueryID', ''))
    
    bRet = 1
    for i in range(1):
        if QueryID == '' or OrderID == '' or tradeID == '':
            break
        
        pay_action = None
        try:
            pay_action_list = PayAction.objects.filter(query_id=QueryID)
            print pay_action_list
            if 0 == pay_action_list.__len__():
                break
            pay_action = pay_action_list[0]
            if None == pay_action:
                break
            print 'pay_action.pay_status'
            print pay_action.pay_status
            if pay_action.pay_status >= 2:
                bRet = 0
                break
            
            remark = pay_action.remark
            tmp = remark.split('`')
            pay_amount = float(tmp[0])
            print 'query cmmm:'
            print 'pay_amount:'
            print pay_amount
            AppID = '300002904622'
            request_url = 'http://ospd.mmarket.com:8089/trust'
            if 2 >= tmp.__len__():
                AppID = tmp[1]
                if 3 >= tmp.__len__():
                    request_url = tmp[2]
                    
            #查单返回的TotaPrice永远为0 ExData 为空.....??
            result_code, TotalPrice, ExData, remark = query_order(tradeID, OrderID, AppID, request_url)
            
            if -1 == result_code:
                result_code, TotalPrice, ExData, remark = query_order(tradeID, OrderID, AppID, request_url)
            
            if 0 != result_code:
                break
            
            pay_action.amount = pay_amount
            pay_action.status = 2
            pay_action.save()
            bRet = 0
        except Exception, ex:
            print 'cmmm query error'
            print ex
        
    return HttpResponse(bRet)
    
    

def query_order(TradeID, OrderID, AppID='300002904622', request_url= 'http://ospd.mmarket.com:8089/trust'):
    
    result_code = 1
    TotalPrice = 0
    ExData = ''
    remark = ''  
    
    #0：测试订单
    #1：正式订单
    
#    <?xml version=\"1.0\" 
#    standalone=\"yes\"?><Trusted2ServQueryReq><MsgType>Trusted2ServQueryReq
#    </MsgType><Version>1.0.0</Version><OrderID>********</OrderID><AppID>300
#    00*******</AppID><OrderType>1</OrderType></Trusted2ServQueryReq> 
    code_map = {
        0:"用户已订购，存在对应订单 ",
        2:"用户未订购，不存在对应订单",
        11:"没有授权调用该能力 ",
        12:"能力服务忙 ",
        13:"其他，平台未知错误 ",
        17:"数字签名不正确 ",
        18:"请求能力不存在 ",
        19:"应用不存在"
    }
    
    request_xml = '<?xml version="1.0" encoding="UTF-8"?><Trusted2ServQueryReq><MsgType>%s</MsgType><Version>%s</Version><AppID>%s</AppID><OrderID>%s</OrderID><TradeID>%s</TradeID><OrderType>%s</OrderType></Trusted2ServQueryReq>'
    
    request_xml = request_xml % ('Trusted2ServQueryReq', '1.0.0', AppID, OrderID, TradeID, 0)
    
    order_status_xml = ''
    try:
        order_status_xml = http_post(request_url, request_xml)
    except Exception, ex:
        print '1cmmm query_order error::'
        print ex
        try:
            order_status_xml = http_post(request_url, request_xml)
        except Exception, ex:
            print '2cmmm query_order error::'
            print ex
        
    
    try:
        
        print 'order_status_xml::'
        print order_status_xml
        order_status_xml = minidom.parseString(order_status_xml)
        r_trans = order_status_xml.getElementsByTagName("Trusted2ServQueryResp")[0]
        rcode = getNodeTextByTagName(r_trans, "ReturnCode")
        
        rcode = int(rcode)
        remark = code_map.get(rcode, '查单未知错误')
        TotalPrice = 0
        ExData = ''
        if rcode == 0:
            result_code = 0
            TotalPrice = float(getNodeTextByTagName(r_trans, "TotalPrice"))
            ExData = getNodeTextByTagName(r_trans, "ExData")
            
    except Exception, ex:
        result_code = -1
        print 'cmmm query order parser xml error'
        print ex
    
    return result_code, TotalPrice, ExData, remark
    
def get_rep_data(hRet):
    data = '<?xml version="1.0" encoding="UTF-8"?>'
    data += '<SyncAppOrderResp><MsgType>SyncAppOrderResp</MsgType><Version>1.0.0</Version><hRet>%d</hRet></SyncAppOrderResp>'
    data = data%hRet
    return data
    

def parse_notify_data(data):
    '''
    通过minixml解析data
    '''
    dom = minidom.parseString(data)
    notify = dom.getElementsByTagName("SyncAppOrderReq")[0]
    TradeID = getNodeTextByTagName(notify, "TradeID")
    OrderID = getNodeTextByTagName(notify, "OrderID")
    TotalPrice = float(getNodeTextByTagName(notify, "TotalPrice"))
    ExData = getNodeTextByTagName(notify, "ExData")
    return TradeID, OrderID, TotalPrice, ExData
