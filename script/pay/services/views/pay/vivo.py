# -*- coding: utf-8 -*-
#

from services.views import md5
import json
import urllib,urllib2,hashlib
import base64
import traceback

def confirm_vivo_get_link_id(request):
    return request.REQUEST.get('channel','')#用户使用的支付渠道，代码对应关系见



def check_sign(request,app_key):
    '''
    1. 被签名字符串中的关键信息需要按照key值做升序排列；
    2. 空值（空字符串或null值）不参与签名运算； 
    3. 将被签名字符串转成字节数组时必须指定编码为utf-8。

    signature=to_lower_case(md5_hex(key1=value1&key2=value2&...&keyn=valuen&to_lower_case(md5_hex(secret_key))))
    '''
    _g = request.POST
    signature = ''
    sign_str = ''
    for k in sorted(_g.keys()):
            _v = _g.get(k,'').encode('utf-8')
            if k!='signature' and _v and _v!='null':
                sign_str += '%s=%s&' % (k,_v)
            else:
                signature = _v
    _app_key =  hashlib.new('md5',app_key).hexdigest().lower()
    sign = hashlib.new('md5',sign_str+_app_key).hexdigest()
    print _g
    print (sign_str+_app_key,sign,signature)
    return signature == sign.encode('utf-8').lower()

def confirm_vivo(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','')
    
    rq = request.REQUEST
    respCode = rq.get('respCode','')
    respMsg = rq.get('respMsg','')
    signMethod = rq.get('signMethod','')
    signature = rq.get('signature','')
    storeId = rq.get('storeId','')        #定长20位数字，由vivo分发的唯一识别码
    storeOrder = rq.get('storeOrder','')  #和客户端约定传 serverId_playerId 商户自定义， 最长 64 位字母、数字和下划线组成
    vivoOrder = rq.get('vivoOrder','')
    orderAmount = rq.get('orderAmount','0')
    respCode = rq.get('respCode','')
    channel = rq.get('channel','')
    channelFee = rq.get('channelFee','')  #渠道费    渠道扣除的费用，格式同：orderAmount
    

    account = msg = result_msg =''
    server_id = player_id = orderid = pay_amount = 0
    try:
        if check_sign(request,app_key):
            if respCode == '0000':                #0000，代表支付成功
                pay_amount = float(orderAmount)  #单位：元，
                server_id,player_id = storeOrder.split('_')[:2]
                server_id,player_id = int(server_id),int(player_id)
                orderid = vivoOrder
                msg = channelFee
                result_msg = 'success'
    except Exception,e:
            traceback.print_exc()
            print('confirm vivo has error',e)
            
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r

