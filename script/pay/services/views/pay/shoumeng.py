# -*- coding: utf-8 -*-
from services.views import md5

def confirm_shoumeng_get_link_id(request):
    return request.GET.get('payType','')

def confirm_shoumeng(request,pay_channel):
    
    #orderId    渠道商订单ID    String    必填    是
    #uid    渠道商用户唯一标识    String    必填    是
    #amount    充值金额(单位：元)    int    必填    是
    #coOrderId    游戏商订单号    String    必填    是
    #success    订单状态：0成功，1失败    int    必填    是
    #msg    订单失败时的错误信息    String    否    否
    #sign    MD5签名结果    String    必填    否
    #
    #
    #MD5签名规则
    #先将指定参数串按照参数名范例指定的次序，并将参数secret(由畅娱                                提供)及其值附加在排序后的参数串末尾，进行md5得到待签名字符串。
    #MD5签名采用标准MD5算法，得到32位小写的签名。
    #Secret参数由双方协商，不以参数的形式传递，供MD5签名时使用，不可以泄漏到第三方。
    #
    #签名示例
    #sign=md5(orderId=de123131&uid=1234&amount=50&coOrderId=abcdefg &success=0&secret=abcd)
    #返回SUCCESS
    
    result_msg = 'FAILURE'
    orderId = request.POST.get('orderId','')
    uid = request.POST.get('uid','')
    amount = request.POST.get('amount','')
    coOrderId = request.POST.get('coOrderId','')
    success = request.POST.get('success','')
    msg = request.POST.get('msg','')
    
    sign = request.POST.get('sign','')
    
    try:
        app_key = pay_channel.get_config_value('app_key','dcb60382d326868980c2c4d080811666')
    except Exception,e:
        print('confirm shoumeng has error0',e)
    
    sign_str = 'orderId=%s&uid=%s&amount=%s&coOrderId=%s&success=%s&secret=%s' % (orderId, uid, amount, coOrderId, success, app_key)
    print sign_str
    sign_str = md5(sign_str)
    print(sign_str,sign)
    
    pay_amount = 0
    the_server_id = 0
    player_id = 0 
    remark = ''
    if sign==sign_str:
        try:
            amount = float(amount)
            if success =='0' and amount > 0:
                pay_amount = amount
                tmp = coOrderId.split('_')
                the_server_id = int(tmp[0])
                player_id = int(tmp[1])
            else:
                remark = msg
            result_msg =  'SUCCESS'
        except Exception,e:
            print('confirm youai has error',e)
    else:
        result_msg = 'ErrorSign'
    
    return {'server_id':the_server_id, 'player_id':player_id,'order_id':orderId,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        

        
        
        
        
        
        
        
        
        