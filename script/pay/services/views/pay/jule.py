# -*- coding: utf-8 -*-
#聚乐

import json
import base64
import rsa
import urllib

    
def confirm_jule_get_link_id(request):
    return ''


def convert_post_data(post_data):
    _d = {}
    for kv in post_data.split('&'):
        k,v = kv.split('=')
        _d[k] = urllib.unquote_plus(v.replace('"',''))
    return _d
    
    
def confirm_jule(request,pay_channel):
    
    public_key = pay_channel.get_config_value('public_key', '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDFS26n017LsjF6IJtY9rkxOLpEPCoDQYI0RfH+fnDktNVuWxfBbyf4aBu4pmblhpLHIqz3m9uiuwI/Yu8j1GWzYpji7KthvRTEnOpUa1LKHDO5dE6NUO05+dXxZLqqGMUp6abyLJTqIA+pudOupIALDTfq5kQ8qbYFYXMhbIQq0wIDAQAB
-----END PUBLIC KEY-----''')
    post_data =  request.raw_post_data
    print '-' * 40
    print post_data
    _data = convert_post_data(post_data)
    pub = rsa.PublicKey.load_pkcs1_openssl_pem(public_key)
    order = _data.get('order','')
    sign  = _data.get('sign','')

    query_id = ''
    order_id = ''
    pay_amount = 0
    remark = ''
    result_msg = 'fail'
    server_id = player_id = ''
    
    try:
        if rsa.verify(order,base64.decodestring(sign),pub):
            order_json = json.loads(order)
            remark = order_json.get('result_msg',result_msg).encode('utf-8','ignore')
            if int(order_json.get('result_code',0)) == 1:
                server_id,player_id = [ int(x) for x  in order_json.get('game_order_id','0_0').split('_')[:2]]
                order_id = order_json.get('jolo_order_id', '')
                pay_amount = float(order_json.get('real_amount', 0))/100 #付款成功金额，单位人民币分
                result_msg = 'success'
    except rsa.pkcs1.VerificationError:
            result_msg = 'sign error'
            
    except Exception,e:
        print('confirm jule has an error:',e)
    
    _r = {"server_id":server_id, "player_id": player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}
    print _r
    return  _r



'''
        String signType = paramters.get("sign_type");//签名类型，一般是RSA
        String sign = java.net.URLDecoder.decode(paramters.get("sign"),"utf-8");// 签名
        String order = paramters.get("order");
        
        JSONObject jsonObject = new JSONObject(orderDecoderToJson);    
        int resultCode=jsonObject.getInt("result_code");//1成功 0失败
        String resultMsg=(String)jsonObject.get("result_msg");//支付信息
        String gameCode=(String)jsonObject.get("game_code");//游戏编号
        int realAmount=(int)jsonObject.getInt("real_amount");//付款成功金额，单位人民币分
        String cpOrderId=(String)jsonObject.get("game_order_id");//cp自身的订单号  
        String joloOrderId=(String)jsonObject.get("jolo_order_id");//jolo订单
        String createTime=(String)jsonObject.get("gmt_create");//创建时间 订单创建时间 yyyy-MM-dd  HH:mm:ss
        String payTime=(String)jsonObject.get("gmt_payment");//支付时间 订单支付时间  yyyy-MM-dd  HH:mm:ss
        
        System.out.println("resultCode>>>"+resultCode);
        System.out.println("resultMsg>>>"+resultMsg);
        System.out.println("cpOrderId>>>"+cpOrderId);
        System.out.println("joloOrderId>>>"+gameCode);
        System.out.println("gameCode>>>"+joloOrderId);
        System.out.println("realAmount>>>"+realAmount);
        System.out.println("createTime>>>"+createTime);
        System.out.println("payTime>>>"+payTime);
                
        
'''