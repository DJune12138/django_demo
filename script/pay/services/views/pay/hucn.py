# -*- coding: utf-8 -*-
#已测   POST  http://127.0.0.1:8002/service/confirm/hucn?custom=14&orderid=120507224627804959449D&account=196&regold=10&result=0&msg=hello&channel=alipay&sign=18d762a91a6f
from services.views import md5


def confirm_hucn_get_link_id(request):
    return request.POST.get('channel','')

def confirm_hucn(request,pay_channel={}):
    app_key = pay_channel.get_config_value('app_key','I0oskdibsBfb6klo')
    user_type = pay_channel.get_config_value('user_type',8)
    custom = request.POST.get('custom','')
    order_id = request.POST.get('orderid','')
    account = request.POST.get('account','')
    regold = request.POST.get('regold','')
    result = request.POST.get('result','')

    remark = request.POST.get('msg','')
    channel = request.POST.get('channel','')
    sign = request.POST.get('sign','')
    
    sign_str = 'custom=%s&account=%s&regold=%s&orderid=%s&result=%s&msg=%s&channel=%s&%s'%(custom,account,regold,order_id,result,remark,channel,app_key)
    #print(sign_str)
    sign_str = md5(sign_str)[10:22]
    result_msg = '0'
    pay_amount = 0
    server_id = 0
    
    #print sign_str
    if sign==sign_str:
        try:
            server_id = int(custom)
    
            if int(result)==0:
                pay_amount = float(regold)
    
            result_msg =  '{query_id}'   
        except Exception,e:
            print('confirm hucn has error',e)
    else:
        result_msg = 'Sign error'
    
    return {'server_id':server_id,'user_type':user_type,'open_id':account,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}



