# -*- coding: utf-8 -*-
#

from services.views import md5
import json
import urllib,urllib2,hashlib
import base64
import traceback

def confirm_mengcheng_get_link_id(request):
    return ''


def check_sign(request,app_key):
    _g = request.POST
    s_sign = ''
    sig = ''
    sign_str = ''
    for k in sorted(_g.keys()):
            _v = _g.get(k,'')
            if k!='sign' and _v:
                sign_str += '%s=%s' % (k,_v)
            else:
                sig = _v
    sign = hashlib.new('sha1',sign_str+app_key).hexdigest()#计算消息SHA-1摘要信息值
    print _g
    print (sign_str,sign,sig)
    return sign == sig.encode('utf-8')

def confirm_mengcheng(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','MjJiNTNmYjIwNzFhOWI1YjYwNDAyNjBmMDBkY2NkZGEwMDEzNDY4OA==')
    app_key = base64.decodestring(app_key)
    keys = ['transdata','sign']
    transdata,sign = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]
    
    account = msg = ''
    result_msg = 'fail'
    server_id = player_id = orderid = pay_amount = 0

    if check_sign(request,app_key):
        try:
            transdata = json.loads(transdata)
            if int(transdata.get('status',0))==1:
                pay_amount = float(transdata['money']) / 100 #单位分
                server_id,player_id = transdata['cpprivate'].split('_')[:2]
                server_id,player_id = int(server_id),int(player_id)
                orderid = transdata['ordersn']
                msg = transdata['transtime']
                result_msg = 'success'
        except Exception,e:
            traceback.print_exc()
            print('confirm mengcheng has error',e)
            
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r

'''
transdata={"ordersn":"139451045648655","goodsid":"1000000010","money":1,"count":1,"status":1,"app_id":"100010000010000000064","transtime":"2002-03-11
12:18:03","cpprivate":null}&sign=f370303b73aeeac9c2d296ee6acecae1e8f1c2c1
'''