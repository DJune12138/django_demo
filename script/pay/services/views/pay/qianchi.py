# -*- coding: utf-8 -*-
from services.views import md5
import json, urllib

def confirm_qianchi_get_link_id(request):
    return request.GET.get('waresid', '10007700000004100077')
    
    
def confirm_qianchi(request, pay_channel={}):
    app_id = pay_channel.get_config_value('app_id', 'wc4ui4t7kqop12hgcw32dir8')
    
    post_data = json.loads(request.raw_post_data)
    
    exorderno = post_data.get('exorderno', '')    #外部订单号 
    transid = post_data.get('transid', '')     #交易流水号 
    waresid = post_data.get('waresid', '')     #商品编号 
    cpid = post_data.get('cpid', '')   #CP编号
    chargepoint = post_data.get('chargepoint', '')     #计费点编号 
    feetype = post_data.get('feetype', '')     #计费类型 
    money = post_data.get('money', '')   #交易金额                          本次交易的金额，单位：分
    count = post_data.get('count', '')    #购买数量 
    result = post_data.get('result', '')    #交易结果 
    transtype = post_data.get('transtype', '')    #交易类型 
    transtime = post_data.get('transtime', '')    #交易时间
    paytype = post_data.get('paytype', '')  #支付渠道
    gameType = post_data.get('gameType', '')  #游戏类型
    gameServer = post_data.get('gameServer', '')   #游戏服务器
    gameRegion = post_data.get('gameRegion', '')  #游戏大区
    gameUID = post_data.get('gameUID', '')  #当前支付的用户ID
    gameName = post_data.get('gameName', '')   #购买游戏产品的名称
    gameDesc = post_data.get('gameDesc', '')   #购买游戏产品的描述
    sign = post_data.get('sign', '') #消息签名 
    
    
    try:
        gameName = urllib.unquote(gameName.encode('utf-8'))
        gameName = gameName.decode('utf-8')
    except Exception,e:
        print('has error',e)
    
    server_sign = '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % (exorderno, transid, waresid, cpid, chargepoint, feetype, money,
                                                       count, result, transtype, transtime, paytype, gameType, gameServer, gameRegion,
                                                       gameUID, gameName, gameDesc, app_id)
    
#    print (exorderno, transid, waresid, cpid, chargepoint, feetype, money,
#       count, result, transtype, transtime, paytype, gameType, gameServer, gameRegion,
#       gameUID, gameDesc, app_id)
#    
    #print server_sign
    server_sign = md5(server_sign)
    print (sign, server_sign)
    
    orderid = ''
    result = ''
    remark = ''
    link_id = ''
    player_id = 0
    server_id = 0
    amount = 0
    result_code = '0'
    if sign == server_sign:
        orderid = transid
        link_id = gameUID
        server_id = int(gameServer)
        player_id = int(gameRegion)
        amount = float(money) / 100
        result_code = 'SUCCESS'
    else:
        result_code = '0'
        remark = 'sign error'
    
    return {'link_id':link_id, 'player_id':player_id, 'server_id':server_id, 'order_id':orderid, 'amount':amount, 'remark':remark, 'result_msg':result_code}
