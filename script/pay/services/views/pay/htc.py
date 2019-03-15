# -*- coding: utf-8 -*-
from services.alipay import getNodeTextByTagName
from services.http import http_post
from services.views import md5
from xml.dom import minidom

def pay_htc(the_action,pay_channel = {},service_url='service.fytxonline.com'):
    
    pay_way = pay_channel.get_config_value('pay_way', '')
    exchange_url = pay_channel.get_config_value('exchange_url', 'http://game.htc.joloplay.com/order')
    settle_url = pay_channel.get_config_value('settle_url', 'http://game.htc.joloplay.com/confirmOrder')
    gamecode = pay_channel.get_config_value('app_id', '1368004766017')
    appkey = pay_channel.get_config_value('app_key', 'uHYbU2nSpZbg6xcWFiRzIT0tyZGmTCqa')
    
    pamt = 0
    try:
        pamt = int(the_action.post_amount)
    except Exception,ex:
        print 'htc.py => <pay_gash> error'
        print ex
    
    sign = '%s%s%s%s%s%s' % (the_action.card_no, gamecode, the_action.query_id, '', pamt, appkey)
    print sign
    sing = md5(sign)
    
    post_data = '''<?xml version="1.0" encoding="GBK"?>
                    <order>
                    <usercode>%s</usercode>
                    <gamecode>%s</gamecode>
                    <tradnum>%s</tradnum>
                    <expand>%s</expand>
                    <pamt>%s</pamt>
                    <checking>%s</checking>
                    </order>
                    ''' % (the_action.card_no, gamecode, the_action.query_id, '', pamt, sing)
    
    result_data = '1'
    
    order_status = ''
    try:
        print 'exchange_url:::', exchange_url
        print 'post_data:::', post_data
        result_data = http_post(exchange_url, post_data)
        print 'result_data:::', result_data
        result_data = result_data.replace('GBK', 'utf-8')
        result_data = parse_exchange_data(result_data)
        msg_map =  {"0":"余额不足，兑换失败",
                    "1":"订单成功（游戏平台暂时扣除游戏币）",
                    "2":"验证错误",
                    "3":"游戏不存在",
                    "4":"用户不存在"
        }
        
        if the_action.query_id == result_data['tradnum'] and gamecode == result_data['gamecode']:
            order_status = str(result_data['status'])
            if '1' == order_status:
#                result_data['code'] = 0
#                result_data['msg'] = the_action.query_id
                result_data = '0'
            else:
#                result_data['code'] = 1
#                result_data['msg'] = msg_map.get(str(result_data['status']), '未知错误')

                result_data = '1'
                
    except Exception, ex:
        print 'htc.py => <pay_htc>  error'
        print ex
        
    #请款
    try:
        if '0' == result_data:
            if settle(the_action.query_id, order_status, gamecode, appkey, settle_url):
                the_action.status = 2
                the_action.pay_amount = the_action.post_amount
                result_data = 'success'
            else:
                the_action.remark = '请款失败,不能使用普通补单工具补单'
                print 'settle error'
                result_data = '1'
                the_action.status = -4
            
            the_action.save()
                
    except Exception, ex:
        print ex
    return 1, result_data
    



#usercode    用户游戏平台唯一身份标识
#gamecode    游戏编号 ，由游戏平台分配
#tradnum    订单编号：由游戏方生成（订单号前缀为gamgcode）
#expand    游戏方自定义参数
#pamt    玩家兑换游戏币需消耗P宝(or G宝)金额（必须是整数，不能是小数） 1:1
#checking    验证信息，为MD5加密的参数拼接字符串:
#usercode+gamecode+tradnum+expand+pamt+key
#key 为游戏密钥 。



def parse_exchange_data(data):
    '''
    通过minixml解析data
    <order>
        <tradnum>xxxxxx</tradnum>
        <status>1</status>
        <checking>xxxxxxx</checking>
        <gamecode>xxxxxxxx</gamecode>
        <expand>xxxxxxxxxxx</expand>
    </order>
    tradnum    订单号：3.1.1中游戏方提供的订单号
    status    交易结果
    0 余额不足，兑换失败
    1.订单成功（游戏平台暂时扣除游戏币）
    2.验证错误
    3.游戏不存在
    4.用户不存在
    5.参数错误(pamt必须为整数)
    gamecode    游戏在游戏平台分配的编号
    expand    游戏方的扩展参数
    checking    验证信息，为MD5加密的参数拼接字符串： 
    tradnum+status+gamecode+expand+key     key 为游戏密钥

    '''
    dom = minidom.parseString(data)
    order = dom.getElementsByTagName("order")[0]
    tradnum = getNodeTextByTagName(order, "tradnum")
    status = getNodeTextByTagName(order, "status")
    checking = getNodeTextByTagName(order, "checking")
    gamecode = getNodeTextByTagName(order, "gamecode")
    expand = getNodeTextByTagName(order, "expand")
    
    return {"tradnum":tradnum, "status":status, "checking":checking, "gamecode":gamecode, "expand":expand}
    
#<?xml version="1.0" encoding="GBK"?>
#<order><tradnum>1305131128241253828A4A</tradnum><status>1</status><checking>3854EF888D8CEB8ADDB37CC7DBF647DC</checking><gamecode>1368004766017</gamecode><expand></expand></order>
#
def settle(query_id, status, gamecode, key, settle_url):
    sign = md5('%s%s%s' % (query_id, status, key))
    post_data = '''<?xml version="1.0" encoding="GBK"?>
                    <order>
                    <tradnum>%s</tradnum>
                    <status>%s</status>
                    <checking>%s</checking>
                    <gamecode>%s</gamecode>
                    </order>''' % (query_id, status, sign, gamecode)
    
    try:
        print 'settle post_data:::', post_data
        result_data = http_post(settle_url, post_data)
        print 'settle result_data:::', result_data
        result_data = result_data.replace('GBK', 'utf-8')
        result_data = parse_settle_data(result_data)
        if query_id == result_data['tradnum'] and 'success' == result_data['result']:
            return True
        return False
        
    except Exception, ex:
        print ex
        print 'settle error'
    
    return False



def parse_settle_data(data):
#    <order>
#    <tradnum>xxxxxx</tradnum>
#    <expand>xxxxxxx</expand>
#    <result>success</result>
#    <checking>xxxxxxx</checking>
#    </order>
#        参数说明
#    参数    参数说明
#    tradnum    订单号
#    expand    3.1.1中游戏方自定义参数
#    result    同步结果：表示订单同步成功
#    checking    验证信息，为MD5加密的参数拼接字符串： tradnum+expand+result +key
#     key 为游戏密钥
    
    
    
    
    dom = minidom.parseString(data)
    order = dom.getElementsByTagName("order")[0]
    tradnum = getNodeTextByTagName(order, "tradnum")
    result = getNodeTextByTagName(order, "result")
    checking = getNodeTextByTagName(order, "checking")
    expand = getNodeTextByTagName(order, "expand")
    
    return {"tradnum":tradnum, "result":result, "checking":checking, "expand":expand}
    
    
    