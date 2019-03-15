# -*- coding: utf-8 -*-
#已测  
from xml.dom import minidom


def confirm_cmcc_get_link_id(request):
    return None

def confirm_cmcc(request, pay_channel={}):
    
    request_xml = request.raw_post_data
    
    #request_xml = '''<?xml version="1.0" encoding="UTF-8"?><request><userId>1151367961</userId><cpServiceId>601810061888</cpServiceId><consumeCode>000061887004</consumeCode><cpParam>4X4210563X000000</cpParam><hRet>0</hRet><status>1101</status><transIDO>2162139PONE2814785</transIDO><versionId>100</versionId></request>'''
    
    link_id = ''
    amount = 0
    server_id = 0
    player_id = 0
    order_id = ''
    remark = ''
    result_msg = ''
#    if True:
    try:
        
        data = parse_notify_data(request_xml)
        
        list_cp_param = data.cpParam.split('X')
        server_id = int(list_cp_param[0])
        player_id = int(list_cp_param[1])
        order_id = data.transIDO
        link_id = data.consumeCode
        
        
        hRet = int(data.hRet)
        
        result_code = {
            1101 :  u"成功",
            -1   :  u"未知错误",
            100  :  u"手机号码不存在",
            101  :  u"手机号码错误",
            102  :  u"用户停机",
            103  :  u"用户欠费",
            104  :  u"用户没有使用该业务的权限",
            105  :  u"业务代码错误",
            106  :  u"服务代码错误",
            107  :  u"业务不存在",
            108  :  u"该业务暂停服务",
            109  :  u"该服务种类不存在",
            110  :  u"该服务种类尚未开通",
            111  :  u"该业务尚未开通",
            112  :  u"合作方的合作代码错误",
            113  :  u"合作方不存在",
            114  :  u"暂停服务",
            115  :  u"用户没有定购该套餐业务",
            116  :  u"用户暂停定购该套餐业务",
            117  :  u"该业务不能对该用户开放",
            118  :  u"用户已经订购了该套餐业务",
            119  :  u"用户不能取消该业务",
            120  :  u"话单格式错误",
            121  :  u"没有该类业务",
            122  :  u"接收异常",
            123  :  u"业务价格为负",
            124  :  u"业务价格格式错误",
            125  :  u"业务价格超出范围",
            126  :  u"该用户不是神州行用户",
            127  :  u"该用户没有足够的余额",
            128  :  u"无效的业务ID，无法找到相应的话费和金额",
            129  :  u"用户已经是注册用户",
            130  :  u"用户在BOSS中没有相关用户数据",
            131  :  u"BOSS系统数据同步出错",
            132  :  u"相关信息不存在",
            133  :  u"用户数据同步出错",
            134  :  u"合作方数据同步出错",
            135  :  u"业务数据同步出错",
            136  :  u"用户密码错误",
            139  :  u"用户是黑名单用户",
            140  :  u"用户没有点播该业务",
            141  :  u"用户是白名单用户",
            142  :  u"用户销户",
            143  :  u"用户预销户",
            144  :  u"非智能网受信用户",
            201  :  u"点卡帐户已经存在",
            202  :  u"用户帐户鉴权余额不足",
            203  :  u"无此点卡帐户",
            204  :  u"充值金额超过当天最大限额",
            205  :  u"充值金额超过当月最大限额",
            206  :  u"扣费点数超过单次最大限额",
            207  :  u"扣费点数超过当日最大限额",
            208  :  u"扣费点数超过当月最大限额",
            280  :  u"冲正时间超期",
            281  :  u"无法找到冲正对应的原流水号",
            282  :  u"补款,冲正失败",
            283  :  u"部分退费",
            284  :  u"待冲正的POS交易流水号已被冲正",
            398  :  u"自动充值找不到响应的代码",
            399  :  u"自动充值其他错误",
            1001 :  u" OCS/OCE余额不足",
            1002 :  u" OCS/OCE用户状态不正确",
            1003 :  u" OCS/OCE流水重复",
            1004 :  u" OCS/OCE处理任务超时",
            1005 :  u" OCS/OCE参数验证错误",
            1006 :  u" OCS/OCE冲正时效已过期",
            1007 :  u" OCS/OCE交易密码错误",
            1009 :  u" OCS/OCE未知异常",
            2560 :  u" OCS/OCE用户转品牌",
            9000 :  u" 系统磁盘读写错误",
            9001 :  u" 网络异常",
            9002 :  u" 网络错误",
            9003 :  u" 业务网关忙，业务网关缓存",
            9005 :  u" 系统繁忙",
            9007 :  u" 业务网关超过限制的流量",
            9008 :  u" 系统异常，并不可用",
            9009 :  u" 业务网关异常，并不可用",
            9010 :  u" 该业务网关没有权限调用该接口消息",
            9011 :  u" 没有权限发送该接口消息给业务网关",
            9012 :  u" 版本不支持",
            9013 :  u" 消息类型不对，系统不支持",
            9014 :  u" 验证错误，无法解析XML结构、缺少必须存在的字段，或者消息格式不正确",
            9015 :  u" 拒绝消息，服务器无法完成请求的服务",
            9017 :  u" 非法接入IP      /*IP地址鉴权*/"
        }
        try:
            tmp_status = int(data.status)
            if 0 == hRet :
                amount = 1
            remark = u'%s|%s' % (result_code.get(tmp_status, ''),data.userId)
        except Exception, ex:
            print 'cmcc map status code error:', ex
            remark = str(tmp_status)
        result_msg = generate_ResponseData(ResponseData(data.transIDO, hRet))
    except Exception:
        result = ResponseData(0, 1)
        result_msg = generate_ResponseData(result)
    result_msg = result_msg.encode('utf-8')
    #print 'result code: %s ' % result.hRet
    return {'server_id':server_id,'player_id':player_id,'link_id':link_id,'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg}

#
#def confirm_cmcc(request):
#    
#    #request_xml = '''<?xml version="1.0" encoding="UTF-8"?><request><userId>1151367961</userId><cpServiceId>601810061888</cpServiceId><consumeCode>000061887004</consumeCode><cpParam>4X4210563X000000</cpParam><hRet>1</hRet><status>1101</status><transIDO>2162139PONE2814785</transIDO><versionId>100</versionId></request>'''
#    
#    request_xml = request.raw_post_data
#    print request_xml
#    template = 'pay/pay_post.html'
#    
#    try:
#        result = save_payAction(request_xml, request)
#    except Exception:
#        result = ResponseData(0, 1)
#    print 'result code: %s ' % result.hRet
#    pay_status = generate_ResponseData(result)
#    return render_to_response(template, {"pay_status": pay_status})
# 
#
#def save_payAction(request_xml,request):
#    try:
#        data = parse_notify_data(request_xml)
#    except:
#        return ResponseData(0, 1001)
#    
#    hRet = int(data.hRet)
#    
#    order_id = data.transIDO
#    if '' == order_id:
#        return ResponseData(0, 1003) 
#
#    try:
#        list_pay_channel = PayChannel.objects.using('read').filter(func_name='cmcc', link_id=data.consumeCode)
#    except:
#        return ResponseData(order_id, 1005) 
#    
#    if 0 == list_pay_channel.__len__():
#        return ResponseData(order_id, 1006) 
#    
#    try:
#        list_cp_param = data.cpParam.split('X')
#        server_id = list_cp_param[0]
#        player_id = list_cp_param[1]
#    except:
#        return ResponseData(order_id, 1007) 
#    
#    pay_channel = list_pay_channel[0] 
#
#    if 0 < PayAction.objects.filter(order_id = order_id).count():
#        return ResponseData(order_id, 0) 
#    
#    the_action = PayAction()
#    the_action.query_id = the_action.get_query_id()
#    the_action.order_id = order_id
#    the_action.channel_key = pay_channel.channel_key
#    the_action.server_id = server_id
#    the_action.pay_type = pay_channel.id
#    the_action.pay_user = player_id
#    the_action.pay_ip = request.META.get('REMOTE_ADDR','')
#    the_action.post_amount = 1
#    
#    if 0 == hRet:
#        the_action.pay_amount = the_action.post_amount
#        the_action.pay_gold = the_action.pay_amount * pay_channel.exchange_rate
#        the_action.pay_status = 2
#    else:
#        the_action.pay_status = -2
#    
#    result_code = {
#        1100:u'用户充值成功',
#        1101:u'用户充值失败',
#        1107:u'控制鉴权失败',
#        1111:u'计费代码错误（无效、下线等）',
#        1112:u'充值代码无效',
#        1113:u'充值代码过有效期',
#        1114:u'黑名单用户不允许充值',
#        1115:u'用户伪码为空',
#        1116:u'用户伪码错误',
#        1118:u'充值代码错误（无效、下线等）',
#        1183:u'充值金额超过当天最大限额',
#        1184:u'充值金额超过当月最大限额',
#        1281:u'用户鉴权失败'
#    }
#    
#    remark = ''
#    try:
#        tmp_status = int(data.status)
#        remark = result_code.get(tmp_status, '')
#    except:
#        remark = ''
#    
#    the_action.remark = remark
#    try:
#        the_action.save(using='write')
#    except:
#        return ResponseData(order_id, 1005)
#    
#    return ResponseData(order_id, 0)

class ResponseData(object):
    def __init__(self, transIDO, hRet):
        self.error_code_map = {
                  1001:u'解析xml错误',
                  1002: u'平台计费结果状态码为1', 
                  1003:u'获取不到事务流水号',
                  1004:u'事务流水号长度不为17',
                  1005:u'数据库连接出错',
                  1006:u'计费业务代码无效',
                  1007:u'合作方透传参数无效',
                  1008:u'订单号已存在',
                  1:u'未知错误',
                  0:u'Successful'
                  }
        self.transIDO = transIDO
        self.hRet = hRet
        
        self.message = self.error_code_map.get(self.hRet, u'未知错误')
        
    def set_message(self, message):
        self.message = message

def generate_ResponseData(response_data):
    response_str = u'''<?xml version="1.0" encoding="UTF-8"?><response><transIDO>%s</transIDO><hRet>%s</hRet><message>%s</message></response>'''
    response_str = response_str % (response_data.transIDO, response_data.hRet, response_data.message)
    return response_str
    

class CMCCNotifyData(object):
    def __init__(self, hRet, status, transIDO, versionId, userId, cpServiceId, consumeCode, cpParam):
        self.hRet = hRet
        self.status = status
        self.transIDO = transIDO
        self.versionId = versionId
        self.userId = userId
        self.cpServiceId = cpServiceId
        self.consumeCode = consumeCode
        self.cpParam = cpParam
        
 
def parse_notify_data(data):
    '''
    通过minixml解析data
    '''
   
    dom = minidom.parseString(data)
    notify = dom.getElementsByTagName("request")[0]
    hRet = getNodeTextByTagName(notify, "hRet")
    status = getNodeTextByTagName(notify, "status")
    transIDO = getNodeTextByTagName(notify, "transIDO")
    versionId = getNodeTextByTagName(notify, "versionId")
    userId = float(getNodeTextByTagName(notify, "userId"))
    cpServiceId = getNodeTextByTagName(notify, "cpServiceId")
    consumeCode = getNodeTextByTagName(notify, "consumeCode")
    cpParam = getNodeTextByTagName(notify, "cpParam")
    
    result =  CMCCNotifyData(hRet, status, transIDO, versionId, userId, cpServiceId, consumeCode, cpParam)
    return result
    

def getNodesText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

def getNodeTextByTagName(node, tagName):
    selected = node.getElementsByTagName(tagName)
    if selected:
        return getNodesText(selected[0].childNodes)
    else:
        return ""
