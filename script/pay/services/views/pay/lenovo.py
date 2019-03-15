# -*- coding: utf-8 -*-
from services.views import md5
import json, base64

def confirm_lenovo_get_link_id(request):
    return ''

def int2byte(num):
    byte = []
    while num > 0:
        asc = num % 256
        byte.append(asc)
        num = num / 256
    byte.reverse()
    return byte

def confirm_lenovo(request,pay_channel={}):
    
    g = lambda x,y='':request.POST.get(x,y)
    app_key = pay_channel.get_config_value('app_key','OEM2NzlDNjQ0MkE3ODAyQ0FCNDQ0QjVDMUE3Q0Y5MjJENTk1RUFFQ01UWTJNVFUxT0RjeE1qZzNOek13TnpZeU16TXJNVE00TmpjNE1qZ3dOakk1TURVNE1EQXlNVFEyTkRBeU9ERXlNelUxTURJek5qRTVNRE16')
    
    transdata = g('transdata')#JSON
    sign = g('sign')
    decodeBaseStr = base64.decodestring(app_key)
    decodeBaseStr = base64.decodestring(decodeBaseStr[40:])
    decodeBaseVec = decodeBaseStr.split('+')
    
    privateKey = decodeBaseVec[0]
    modkey = decodeBaseVec[1]
    

    server_sign = ''
    for i in sign.split(' '):
        if '' == i.strip():
            continue
        v = int(i, 16)
        v = pow(v, int(privateKey), int(modkey))
        for item in int2byte(v):
            if item != 32:
                server_sign = '%s%s' % (server_sign, chr(item))
     
    remark = ''
    result_msg = ''
    order_id = ''
    server_id = 0
    player_id = 0
    amount = 0
    try:
        if server_sign == md5(transdata):
            
            transdata = transdata.encode('utf-8')
            
            transdata = json.loads(transdata)
            j = lambda x,y='':transdata.get(x,y)
            
            exorderno = j('exorderno')#商户订单号
            transid = j('transid')#计费支付平台的交易流水号
            appid = j('appid')#平台为商户应用分配的唯一编号
            waresid = j('waresid')#平台为应用内需计费商品分配的编号
            feetype = j('feetype')#计费类型：0 – 开放价格1 – 免费    2 – 按次   3 – 包自然时长    4 – 包账期5 – 买断6 – 包次数7 – 按时长8 – 包活跃时长9 – 批量购买100 – 按次免费试用101 – 按时长免费试用
            
            money = j('money')#本次交易的金额，单位：分
            count = j('count')#本次购买的商品数量
            result = j('result')#交易结果：0 – 交易成功 1 – 交易失败
            transtype = j('transtype')#交易类型：0 – 交易 1 – 冲正
            transtime = j('transtime')#交易时间格式
            cpprivate = j('cpprivate')#商户私有信息
            
            tmp = exorderno.split('_')
            server_id = int(tmp[0])
            player_id = int(tmp[1])
            order_id = transid
            if result == 0:
                amount = int(round(money / 100.0))
            
            result_msg = 'SUCCESS'
        else:
            result_msg = remark = 'sign error'
    except Exception, ex:
        print 'confirm lenovo error:', ex
        
    
    return {'server_id':server_id,'player_id':player_id, 'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg}

