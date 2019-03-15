# -*- coding: utf-8 -*-
from services.views import md5
from services.http import http_post
from django.http import HttpResponse
import json, time

def confirm_a360_get_link_id(request):
    return ''


def confirm_a360(request, pay_channel={}):

    app_key = pay_channel.get_config_value('app_key','d922f3b4d08aa5fb3f29aeb592213d15')
    #app_key  Y  应用app key 
    #product_id  Y  所购商品 id 
    #amount  Y  总价,以分为单位 
    #app_uid  Y  应用内用户id   
    #app_ext1  N  应用扩展信息 1 原样返回 
    #app_ext2  N  应用扩展信息 2 原样返回 
    #user_id  N  360 账号 id 
    #order_id  Y  360 返回的支付订单号 
    #gateway_flag  N  如果支付返回成功，返回 success 应用需要确认是 success才给用户加钱
    #sign_type  Y  定值 md5 
    #app_order_id  N  应用订单号 
    #sign_return  Y 应用回传给订单核实接口的参数 不加入签名校验计算 
    #sign  Y  签名 
    
    amount = request.GET.get('amount', '')#以分为单位 
    app_uid = request.GET.get('app_uid', '')
    app_ext1 = request.GET.get('app_ext1', '')
    gateway_flag = request.GET.get('gateway_flag', '')
    order_id = request.GET.get('order_id', '')
    
    
    result_msg = 'error'
    pay_amount = 0
    server_id = 0
    player_id = 0
    remark= ''
    orderno = order_id
    
    try:
        if check_sign(request, app_key):
            result_msg = 'ok'
            amount = float(amount)
            if amount > 0 and gateway_flag == 'success':
                pay_amount = amount / 100
                player_id = int(app_uid)
                server_id = int(app_ext1)
                orderno=order_id
        else:
            remark = 'error sign'
    except Exception, ex:
        print ex
        remark = 'interal error'
    
    return {'server_id':server_id,'player_id':player_id,'order_id':orderno,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

    
def check_sign(request,app_key):
    keys = request.GET
    keys = [tuple(item) for item in keys.items()]
    keys.sort()
    sign_str = []
    sign = ''
    for item in keys:
        if item[0]=='sign':
            sign = item[1]
        elif item[0] == 'sign_return':
            continue
        else:
            sign_str.append(item[1])
            
    sign_str = '#'.join(sign_str)
    sign_str = '%s#%s' % (sign_str, app_key)
    sign_str = md5(sign_str)
    print "=====", (sign, sign_str)
    if sign == sign_str:
        return True

    return False
    
    
def query_a360(request):
    g = lambda x,y:request.POST.get(x,y)
    code = g('code','')
    t = g('t', '')
    client_id = 'cb26fca917fa06404ad43fbd5f68b2b1'
    client_secret = 'd922f3b4d08aa5fb3f29aeb592213d15'
    if 'c1wan' == t:
        client_id = '296b209cdc14817feb19adf4dfca7e61'
        client_secret = '24ff2c281606b475a7f3cede20f09565'
    elif 'youai360bssg' == t:
        client_id = g('client_id', '24903cebad0aa882443fc8cfd24650ae')
        client_secret = 'f450b94ce27a05f0700cc01cb546857f'
    
    
    request_url = 'https://openapi.360.cn/oauth2/access_token'
    userinfo_url = 'https://openapi.360.cn/user/me.json'
    

    grant_type = 'authorization_code'#定值
    redirect_uri = 'oob'#定值
    
    
    request_url = '%s?grant_type=%s&code=%s&client_id=%s&client_secret=%s&redirect_uri=%s' %(request_url, grant_type, code, client_id, client_secret, redirect_uri)
    
    result_code = 1
    result_msg = ''
    link_key = ''
    sign = ''
    access_token = ''
    try:
        data_result = http_post(request_url)
        data_result = json.loads(data_result)
        access_token = data_result.get('access_token', '')#Access Token 值 
        expires_in = data_result.get('expires_in', '')#Access Token 的有效期 以秒计 
        refresh_token = data_result.get('refresh_token', '')#用于刷新 Access Token的 Token, 有效期 14天 
        scope = data_result.get('scope', '')#Access Token 最终的访问范围，即用户实际授予的权限列表当前只 支持值 basic
        
        
        #查询用户信息
        #access_token  Y  授权的 access token 
        #fields   N  允许应用自定义返回字段，多个属性之间用英文半角逗号作为分   隔符。不传递此参数则缺省返回 id,name,avatar 
        #?access_token=12345678983b38aabcdef387453ac8133ac3263987654321&fields=id,name,avatar,sex,area 
        if access_token != '':
            userinfo_url = '%s?access_token=%s&fields=id' % (userinfo_url, access_token)
            user_info = http_post(userinfo_url)
            user_info = json.loads(user_info)
            link_key = user_info.get('id', '')
            if link_key != '':
                result_code = 0
        else:
            result_msg = u'会话已过期，请重新登陆'
        
        timestamp = int(time.time())
        mykey = 'boluoboluomi'
        sign = md5(('%s%s%s') % (link_key, timestamp, mykey))
    except Exception, ex:
        result_msg = 'internal error'
        print ex
    
    result_data = '%s&%s&%s&%s&%s&%s' % (result_code, link_key, access_token,timestamp, result_msg, sign)
    
    return HttpResponse(result_data)
    
    