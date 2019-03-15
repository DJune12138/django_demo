# -*- coding: utf-8 -*-
# dongganhema

from services.views import md5
import json
import urllib,urllib2,hashlib
import base64
import traceback

def confirm_dghm_get_link_id(request):
    return ''


def check_sign(request,app_key):
    url_params = request.get_full_path()
    _,params = url_params.split('?')[:2]
    signSource = params[:params.find('&signMsg')]
    signMsg = request.GET.get('signMsg','')
    
    signSource += '&appKey=%s' % app_key
    sign = hashlib.new('md5',signSource).digest()
    sb = bytearray()
    HEX_CHARS = "0123456789abcdef";
    for ab in bytearray(sign):
        sb.append(HEX_CHARS[ (ab>>4) & 0x0F])
        sb.append(HEX_CHARS[ab & 0x0F])
    mySign = str(sb).upper()
    print (signSource,signMsg,sign,mySign)
    return signMsg == mySign

def confirm_dghm(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','')
    keys = ['orderId','amount','payNum','resultCode','failure','reserved1']
    orderId,amount,payNum,resultCode,failure,reserved1 = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]
    
    
    account = msg = ''
    result_msg = 'result=1'
    server_id = player_id = orderid = pay_amount = 0

    if check_sign(request,app_key):
        try:
            if int(resultCode) == 0  and int(failure) == 0:
                pay_amount = float(amount) / 100 #单位分
                server_id,player_id = reserved1.split('_')[:2]
                server_id,player_id = int(server_id),int(player_id)
                orderid = orderId
                msg = payNum
                result_msg = 'result=0'
        except Exception,e:
            traceback.print_exc()
            print('confirm dghm has error',e)
            
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r

