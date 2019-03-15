# -*- coding: utf-8 -*-
from views import md5

def confirm_a7725_get_link_id(request):
    type_str = request.REQUEST.get('item','')
    paytype = request.REQUEST.get('paytype', '')
    if paytype == 'google-google':                 #只有google的 才是 商品项目
        if type_str == '':
            gold = request.REQUEST.get('gold', '') #如果不是月卡,充值渠道link_key是用gold区分
            if gold:
                return 'a7725_%s' % gold
    print '-' * 40
    print paytype
    return type_str if  type_str else paytype


def confirm_a7725(request, pay_channel={}):
    g = request.REQUEST
    print g
    orderid = g.get('orderid', '')#7725订单号
    userid = g.get('userid', '')
    roleid = g.get('roleid', '')
    rolename = g.get('rolename', '')
    game = g.get('game', '')
    server = g.get('server', '')
    amount = g.get('amount', '')#订单金额，TWD
    gold = g.get('gold', '')
    paytype = g.get('paytype', '')
    info = g.get('info', '')
    timestamp = g.get('timestamp', '')
    pvc = g.get('pvc', '')
    sign = g.get('sign', '')
    currency = g.get('currency','')
    allow_ips = ['61.219.16.11','61.219.16.12']
    result_msg = '{"code":3001, "error":"OTHER_ERROR"}'
    
    app_key = pay_channel.get_config_value('app_key', '_h0en5ftwx;ohmw#_dcl')
    server_id = 0
    order_id = ''
    player_id = 0
    pay_amount = 0
    remark = ''
    is_pass = False
    try:
        is_pass = chk_sign(request, app_key)
    except Exception, ex:
        print 'chk sign error:', ex
    
    if is_pass:
        result_msg = '{"code":3, "error":"SUCCESS"}'
        try:
            amount = float(amount)
            server_id = int(server)
            player_id = int(roleid)
            order_id = orderid
            if amount > 0 :
                pay_amount = float(gold)
                remark = paytype
                if paytype == 'google-google':  #如果是google的商品,充值通道由link_key特别处理
                    paytype = ''
        except Exception, ex:
            print 'confirm 7725 error:', ex
            
    
    _r = {'post_amount':amount,'open_id':userid,'server_id':server_id, 'player_id':player_id,  'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg,'pay_channel_str':paytype}
    print _r
    return _r


def chk_sign(request, app_key):
    g = request.REQUEST
    keys = request.REQUEST.keys()
    keys.sort()
    sign = ''
    s_sign = ''
    for k in keys:
        if k == 'sign':
            sign = g.get('sign')
            continue
        value = g.get(k, '').replace('\r', '').replace('\n', '').replace('&', '')
        s_sign = '%s%s=%s' % (s_sign, k, value)
        
    s_sign = md5('%s%s' %(s_sign, app_key))
    print sign, s_sign
    
    if sign == s_sign:
        return True
    
    return False
        
