# -*- coding: utf-8 -*-
from services.views import md5
from xml.dom import minidom

def confirm_uni_get_link_id(request):
    return None

def confirm_uni(request, pay_channel={}):
    result_xml = request.raw_post_data
    app_key = pay_channel.get_config_value('app_key', '5d3145e1226fd39ee3b3')
    orderid, ordertime, cpid, appid, fid, consumeCode, payfee, payType, hRet, status, signMsg = '', '', '', '', '', '', '', '', '', '', ''
    try:
        orderid, ordertime, cpid, appid, fid, consumeCode, payfee, payType, hRet, status, signMsg = parse_notify_data(result_xml)
    except:
        pass
    #加密格式为对如下字符串进行MD5加密
    #orderid=XXX&ordertime=XXX&cpid=XXX&appid=XXX&fid=XXX&consumeCode=XXX&payfee=XXX&payType=XXX&hRet=XXX&status=XXX&Key=XXX
    #hRet    支付结果    Interger    Max(4)    支付结果，0代表成功，其他代表失败
    #payfee 支付金额，分
    
    #0-沃支付，1-支付宝，2-VAC支付，3-神州付
    sign_str = 'orderid=%s&ordertime=%s&cpid=%s&appid=%s&fid=%s&consumeCode=%s&payfee=%s&payType=%s&hRet=%s&status=%s&Key=%s' % (orderid, ordertime, cpid, appid, fid, consumeCode, payfee, payType, hRet, status, app_key)
    
    sign_str = md5(sign_str)
    print signMsg, sign_str
    
    result_msg = ''
    pay_amount = 0
    o_id = ''
    server_id = 0
    player_id = 0
    remark = ''
     
    
    if signMsg == sign_str:
        result_msg = '''<?xml version="1.0" encoding="UTF-8"?><callbackRsp>1</callbackRsp>'''
        source_type = payType
        try:
            payType = int(payType)
        except Exception, ex:
            print 'pay uni error => convert int error '
            print payType
            payType = source_type
        print 'uni pay type:', payType
        
        if hRet == '0':
            payfee = float(payfee)
            if payfee > 0:
                pay_amount = payfee / 100
                orderid = str(orderid)
                o_id = orderid
                if -1 != orderid.find('_'):
                    orderid_arry = orderid.split('_')
                else:
                    orderid_arry = orderid.split('X')
                    import time
                    o_id = '%s_%s' % (o_id, int(time.time()))
                try:
                    server_id = int(orderid_arry[0])
                    player_id = int(orderid_arry[1])
                except:
                    remark = '内部错误:%s' % orderid
                    print orderid
                if payType == 2:
                    pay_amount = 0
                    remark = '话费充值已关闭，如有问题，请联系在线客服。'
        else:
            remark = err_code.get(str(status), '未知错误')
        
    else:
        remark = 'sign error'
                
    
    return {"amount":pay_amount, "order_id":o_id, "server_id":server_id, "player_id":player_id, "remark":remark, "result_msg":result_msg, "link_id":payType}

def parse_notify_data(data):
    '''
    通过minixml解析data
    '''
   
    dom = minidom.parseString(data)
    notify = dom.getElementsByTagName("callbackReq")[0]
    orderid = getNodeTextByTagName(notify, "orderid")
    ordertime = getNodeTextByTagName(notify, "ordertime")
    cpid = getNodeTextByTagName(notify, "cpid")
    appid = getNodeTextByTagName(notify, "appid")
    fid = getNodeTextByTagName(notify, "fid")
    consumeCode = getNodeTextByTagName(notify, "consumeCode")
    payfee = getNodeTextByTagName(notify, "payfee")
    payType = getNodeTextByTagName(notify, "payType")
    hRet = getNodeTextByTagName(notify, "hRet")
    status = getNodeTextByTagName(notify, "status")
    signMsg = getNodeTextByTagName(notify, "signMsg")
    
    return orderid, ordertime, cpid, appid, fid, consumeCode, payfee, payType, hRet, status, signMsg

def getNodeTextByTagName(node, tagName):
    selected = node.getElementsByTagName(tagName)
    if selected:
        return getNodesText(selected[0].childNodes)
    else:
        return ""

def getNodesText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

err_code = {
            "00000":"支付成功",
            "01001":"订购用户不存在",
            "01002":"订购用户状态被停止",
            "01003":"订购用户欠费，预付费用户计费失败",
            "01004":"订购用户在黑名单",
            "01006":"此业务能力已被屏蔽",
            "01007":"用户无法屏蔽/恢复业务能力",
            "01099":"其他错误",
            "01005":"无效用户，用户不再当前平台终",
            "01104":"用户不存在",
            "01105":"用户状态不正常",
            "03100":"用户不是一个预付费用户",
            "03101":"用户余额不足",
            "03102":"压缩余额失败",
            "03103":"没有需要的计费信息",
            "03104":"写CDR失败",
            "03108":"等候SCP响应失败",
            "10001":"用户不存在",
            "10002":"开发者不支持vac",
            "10003":"业务不存在",
            "10004":"业务状态不正常",
            "10005":"渠道代码错误",
            "10007":"超过当月限额",
            "10008":"超过当日限额",
            "10009":"任务不存在（内部异常）",
            "10010":"数据库操作失败（内部异常）",
            "10011":"业务不属于该CP",
            "10012":"重复激活，对关卡类计费点"
}
from django.http import HttpResponse
def query_uni(request):
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><checkOrderIdRsp>0</checkOrderIdRsp>')
