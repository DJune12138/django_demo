# -*- coding: utf-8 -*-
from services.views import md5
import urllib

def confirm_guguo_get_link_id(request):
    return ''

def confirm_guguo(request,pay_channel):
    app_key = pay_channel.get_config_value('app_key','1de853df437052757c11863f048f5531')
    
    g = lambda x,y:request.POST.get(x,y)
    
    
    openId = g('openId', '')#    String    11    唯一标识，对应COOGUO用户ID    1
    serverId = g('serverId', '')#    String    30    充值服务器ID，接入时应与COOGUO协商    2
    serverName = g('serverName', '')#    String    30    充值服务器名字    3
    roleId = g('roleId', '')#    String    30    游戏角色ID    4
    roleName = g('roleName', '')#    String    30    游戏角色名称    5
    orderId = g('orderId', '') #   String    20    COOGUO订单号    6
    orderStatus = g('orderStatus', '')#    String    4    订单状态，1-成功；其他为失败    7
    payType = g('payType', '')#    String    30    支付类型，如：2_13_支付宝、4_15_银联等    8
    amount = g('amount', '')#    String    10    成功充值金额，单位(分)，实际float类型    9
    remark = g('remark', '')#    String    255    结果说明，描述订单状态    10
    callBackInfo = g('callBackInfo', '')#    String    255    合作商自定义参数，SDK调用时传入的数据    11
    payTime = g('payTime', '')#    String    20    玩家充值时间，yyyyMMddHHmmss    12
    paySUTime = g('paySUTime', '')#    String    20    玩家充值成功时间，yyyyMMddHHmmss    13
    sign = g('sign', '')#    String    32    参数签名（用于验签对比）

    serverName = urllib.unquote(serverName.encode('utf-8')).decode('utf-8')
    roleName = urllib.unquote(roleName.encode('utf-8')).decode('utf-8')
    payType = urllib.unquote(payType.encode('utf-8')).decode('utf-8')
    remark = urllib.unquote(remark.encode('utf-8')).decode('utf-8')
    
    #sign = MD5(“openId=100000& serverId=123& serverName=测试服务器& roleId=147& roleName=测试角色& orderId=20121129115114758& orderStatus=1& payType=支付宝& amount=100.0& remark=&callBackInfo=自定义数据&payTime=20130101125612&paySUTime=20130101126001&app_key=1478523698”)
    server_sign = u'openId=%s&serverId=%s&serverName=%s&roleId=%s&roleName=%s&orderId=%s&orderStatus=%s&payType=%s&amount=%s&remark=%s&callBackInfo=%s&payTime=%s&paySUTime=%s&app_key=%s' 
    server_sign = server_sign % (openId, serverId, serverName, roleId, roleName, orderId, orderStatus, payType, amount, remark, callBackInfo, payTime, paySUTime, app_key)
    server_sign = md5(server_sign)
    
    pay_amount = 0
    player_id = 0
    server_id = 0 
    order_id = ''
    remark = ''
    result_msg = '0'
    
    if sign == server_sign:
        result_msg = '1'
        try: 
            amount = float(amount)/100
            if amount > 0 and int(orderStatus) == 1:
                result_msg = 'success'
                pay_amount = amount                
                order_id = orderId
                tmp = callBackInfo.split('_')
                server_id = int(tmp[0])
                player_id = int(tmp[1])
        except Exception ,ex:
            result_msg = 'error'
            remark = 'comfrim guguo error:', ex
    else:
        result_msg = 'errorSign'
        remark = 'sign error'
    
    return {'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}
     
    
    
    