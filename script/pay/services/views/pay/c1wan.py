# -*- coding: utf-8 -*-
from services.views import md5

def confirm_c1wan_get_link_id(request):
    return ''

def confirm_c1wan(request,pay_channel):
    app_key = pay_channel.get_config_value('app_key','1de853df437052757c11863f048f5531')
    user_type = pay_channel.get_config_value('user_type',43)
    
    sid = request.POST.get('sid', '')#服务器ID（由游戏方提供）
    orderid = request.POST.get('orderid', '')#订单编号，c1wan订单系统的唯一号,最少16字节
    cash = request.POST.get('cash', '')#玩家充值金额, 保留2位小数
    money = request.POST.get('money', '')#实际金额,保留2位小数
    amount = request.POST.get('amount', '')#充值游戏币数量
    way_name = request.POST.get('way_name', '')
    exchange = request.POST.get('exchange', '')
    pay_time = request.POST.get('pay_time', '')
    uid = request.POST.get('uid', '')#玩家用户ID，玩家唯一标识账号
    # 只有用户支付成功才会产生通知。
    
    pay_amount = 0
    open_id = ''
    server_id = 0 
    order_id = ''
    remark = ''
    result_msg = '0'
    if check_sign(request, app_key):
        result_msg = '1'
        try:
            pay_amount = float(money)
            if pay_amount > 0:
                open_id = uid
                server_id = int(sid)
                order_id = orderid
        except Exception ,ex:
            remark = 'interal error'
            print ex
    else:
        remark = 'sign error'
    
    return {'server_id':server_id,'user_type':user_type,'open_id':open_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}
    
def check_sign(request, key):
    keys = request.POST
    keys = [tuple(item) for item in keys.items()]
    keys.sort()
    sign_str = []
    sign = ''
    for item in keys:
        if item[0]=='sign':
            sign = item[1]
        else:
            sign_str.append('%s=%s'%(item[0],item[1]))
    sign_str = ''.join(sign_str)
    sign_str = '%s%s' % (sign_str, key)
    sign_str = md5(sign_str)
    
    print (sign, sign_str)
    
    if sign == sign_str:
        return True
    
    return False