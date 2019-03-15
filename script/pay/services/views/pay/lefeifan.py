#coding:utf-8

from services.views import md5


def confirm_lefeifan_get_link_id(request):
    return ''


def confirm_lefeifan(request,pay_channel={}):
    #app_key = pay_channel.get_config_value('app_key','I0oskdibsBfb6klo')
    app_key = pay_channel.get_config_value('app_key','c87dfb0f15088051f05a10c074e06381')

    keys = ['account','amount','orderid','result','channel','msg','extrainfo','sign']
    account,amount,orderid,result,channel,msg,extrainfo,sign = [ request.POST.get(x,request.GET.get(x,'')) for x in keys ]
    sign_str = u'account=%s&amount=%s&orderid=%s&result=%s&channel=%s&msg=%s&extrainfo=%s&appkey=%s' % (account,amount,orderid,result,channel,msg,extrainfo,app_key)
    sign_str = md5(sign_str)
    print '-' * 40
    print dict(request.POST)
    print (extrainfo,amount)
    print (sign,sign_str)
    pay_amount = 0
    server_id = player_id = 0
    if sign.encode('utf-8') == sign_str:
        try:
            if int(result) == 0:
                pay_amount = float(amount)
                server_id,player_id = [ int(i) for i in extrainfo.split('_')]
                result_msg =  str(orderid)
                msg = u'%s: %s' % (channel,msg)
        except Exception,e:
            result_msg = '-3'
            print('confirm lefeifan has error',e)
    else:
        result_msg = '-1 sign_error'
        
    _r = {'server_id':server_id,'player_id':player_id,'order_id':orderid,'amount':pay_amount,'remark':msg,'result_msg':result_msg}
    print _r
    return _r

'''
数据提交方式：post
提交参数示例：
account=77&amount=50&orderid=20130806123547852&result=0&channel=联通充值卡&msg=成功&extrainfo=25
参数说明
参数    说明    类型    长度    示例值
account    关联账号    String    30    77
amount    到账金额（元）    int    4    50
orderid    订单ID    String    30    201308151852125872
result    充值结果    int    4    0成功，1失败
channel    充值通道名称    String    20    联通充值卡
msg    成功或失败原因    String    50    卡号或密码错误
extrainfo    自定义信息字段    String    200    打开SDK充值界面时传入的自定义信息原样返回
sign    验证加密串    String    32    见下面说明
sign=MD5(account=77&amount=50&orderid=20130806123547852&result=0&channel=联通充值卡&msg=成功&extrainfo=25&appkey={appkey})

HTTP响应结果：
成功：CP方订单ID
失败：-1验证信息错误； 
     -2不存在的账号，或该账号在该区未建立角色；
     -3 其它错误
'''
