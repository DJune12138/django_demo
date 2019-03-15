# -*- coding: utf-8 -*-
#天翼空间

from services.views import md5
import json
import urllib,urllib2,hashlib

def confirm_tykj_get_link_id(request):
    return ''


def check_sign(request,app_key):
    _g = request.POST
    s_sign = ''
    sig = ''
    sign_str = ''
    for k in sorted(_g.keys()):
            _v = _g.get(k,'')
            if k!='sig' and _v:
                sign_str += '%s%s' % (k,_v)
            else:
                sig = _v
    sign = hashlib.new('sha1',urllib.quote_plus(sign_str+app_key)).hexdigest()#计算消息SHA-1摘要信息值
    print _g
    print (sign_str,sign,sig)
    return sign == sig.encode('utf-8')

def confirm_tykj(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','cab1c89c19ebb56f')
    
    keys = ['chargeResult','txId','chargeId','payTime','orderSn','IMSI','reservedInfo','price','chargeType','sig']
    chargeResult,txId,chargeId,payTime,orderSn,IMSI,reservedInfo,price,chargeType,sig = \
    [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]
    
    account = msg = ''
    result_msg = {"resultCode":"1111","resultDesc":"失败"}
    pay_amount = 0
    server_id = player_id = 0
    orderid = 0
    if check_sign(request,app_key):
        try:
            if int(chargeResult) == 0 and int(chargeType)==1:
                pay_amount = float(price)
                server_id_len = int(txId[0])#第一个字符表示服务器id的长度
                server_id,player_id = (int(txId[1:1+server_id_len]),int(txId[6:]))#第6位以上为player_id
                orderid = orderSn
                result_msg['resultCode'] = "0000"
                result_msg['resultDesc'] = '成功'
        except Exception,e:
            print('confirm tykj has error',e)
        msg = error_code_map.get(str(chargeResult),'未知错误!')
    result_msg = json.dumps(result_msg)      
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r

error_code_map = {"100000003":"无计费点信息","100000004":"不允许的计费类型","100000006":"传入的信息过长","100000101":"离线短信内容解析异常，短信内容为空","100000102":"离线短信内容解析异常，apsecret未匹配","100000103":"离线短信内容解析异常，DES解密失败","100000104":"离线短信内容解析异常，格式不正确","100000201":"在线短信内容解析异常，短信内容为空","100000202":"在线短信内容解析异常，格式不正确","100000203":"在线短信内容解析异常，不存在计费信息","100000204":"在线短信内容解析异常，缓存失效","100000205":"在线短信内容解析异常，缓存内容不正确","100000206":"在线短信内容解析异常，订单号不存在","100000301":"未配置第三方请求地址","100000302":"获取第三方计费点信息网络异常","100000303":"获取第三方计费点信息resultCode不存在","100000304":"获取第三方计费点信息resultCode不匹配‘0000’","100001002":"计费失败","100001006":"重复的包月订单"}
