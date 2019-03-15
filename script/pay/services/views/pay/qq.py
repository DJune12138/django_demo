# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from services.models.pay import PayAction,PayChannel
from services.http import http_post
import json,datetime,urllib

#alter table pay_action change order_id order_id varchar(50) null; 

def pay_qqv3(request,server_id=0,player_id=0):
    app_secret = 'mPUlaMUOO7a9mRwa'
    app_id = 900000633
    platform_id = 1002
    terminaltype = 0
    result_code = 0
    server_id = int(server_id)
    player_id = int(player_id)
#    query_url = 'http://openapi.3g.qq.com/v3/mobile/login/verify'
    #query_url = 'http://openapi.3g.qq.com/v3/mobile/people/@me/@self'
    
    query_url = '/v3/mobile/check_balance'
#    if True:
    try:
        if request.GET.get('key','').find('|')!=-1:
            openid,openkey = request.GET.get('key','|').split('|')
        else:
            openid = request.GET.get('id','')
            openkey = request.GET.get('key','')
            
        params = 'appid=%d&format=json&openid=%s&openkey=%s&pf=qzone&platformid=%d&tt=%d'%(app_id, openid, openkey,platform_id,terminaltype)
        result = get_qqv3(app_secret,query_url,params)
#        print(query_url,result)
        result = json.loads(result)
        if result.get('entry',None)!= None:
            balance = int(result['entry']['balance'])
            status = int(result['entry']['status'])
            
            if status == 0 and balance >= 10:
                post_data = {'callbackUrl':'http://cp.206m.tj.twsapp.com/service/confirm/qq',
                  'finishPageUrl':'http://cp.206m.tj.twsapp.com/service/confirm/qq',
                  'message':'金币',
                  'paymentItems':[{'itemId':'fy01','itemName':'金币','unitPrice':'1','quantity':'%d'%balance,'imageUrl':'http://cp.206m.tj.twsapp.com/static/gold.png','description':'《风云天下OL》游戏金币，可用于购买消除CD、训练位、定向洗炼等游戏增值服务。','type':'1','subType':'2'}]}
                post_data = json.dumps(post_data).replace(': ',':').replace(', ',',')
                #parameters['payInfo'] = post_data
                #post_data = urllib.quote(post_data)
                post_data = 'appid=%d&format=json&openid=%s&openkey=%s&payInfo=%s&pf=qzone&platformid=%d&tt=%d'%(app_id,openid, openkey,post_data,platform_id,terminaltype)
                query_url = '/v3/mobile/charge'
                result = get_qqv3(app_secret,query_url,post_data,True)
#                print(query_url,result)
                result = json.loads(result)
                if result.get('entry',None)!= None:
                    result_code = result['entry'][0]['status']
                    order_id = result['entry'][0]['paymentId']
                    if result_code == '2':
                        #发放金币
                        balance = balance / 10

                        result_code = save_action(server_id,player_id,order_id,balance)
    except Exception,e:
        print('pay_qq has error',e)
        result_code = -1

    return render_to_response('pay/pay_post.html',{'pay_status':result_code})


def get_qqv3(app_secret,get_url,params,is_post=False):
    query_host = 'http://openapi.3g.qq.com'
#    query_host = 'http://119.147.19.43'
    import hmac,hashlib,base64
    method_str = 'GET'
    if is_post:
        method_str = 'POST'
    sign = '%s&%s&%s'%(method_str,urllib.quote(get_url,''),urllib.quote(params,''))
#    print(params,sign)
    hashed = hmac.new('%s&'%app_secret, sign, hashlib.sha1)
    sign = base64.encodestring(hashed.digest())
    sign = urllib.quote(sign[:-1],'')
    if is_post:
        params = '%s&sig=%s'%(params,sign)
        get_url = '%s%s'%(query_host,get_url)
#        print(get_url)
        result = http_post(get_url,params,timeout_param=5)
    else:
        get_url = '%s%s?%s&sig=%s'%(query_host,get_url,params,sign)
#        print(get_url)
        result = http_post(get_url,timeout_param=5)
#    print(result,get_url,params)
    return result
    
def pay_qq(request,server_id=0,player_id=0):
    token_str = request.GET.get('key','')
    if token_str.find('-')==-1:
        return pay_qqv3(request,server_id,player_id)
    
    import oauth.oauth as oauth

    CONSUMER_KEY = '9SzZujdaJcozFbY7cE1q'#.encode('ascii')
    CONSUMER_SECRET = 'mPUlaMUOO7a9mRwa'#.encode('ascii')
    
    parameters = {'appid':'206'}

    result_code = 0

    server_id = int(server_id)
    player_id = int(player_id)
    
    result = ''
#    if True:
    try:
        query_url = 'http://openapi.3g.qq.com/payment/balance?appid=%s'%parameters['appid']

        consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
        token_key,token_secret = token_str.split('-')
        
        access_token = oauth.OAuthToken(token_key,token_secret)

        result =  get_qq(consumer,access_token,query_url,parameters)

        result = json.loads(result)
        if result.get('entry',None)!= None:
            balance = int(result['entry']['balance'])
            status = int(result['entry']['status'])
            
            print(balance,status)
            
            if status == 0 and balance >= 10:
#                balance = 1
                post_data = {'callbackUrl':'http://cp.206m.tj.twsapp.com/service/confirm/qq',
                  'finishPageUrl':'http://cp.206m.tj.twsapp.com/service/confirm/qq',
                  'message':'金币',
                  'paymentItems':[{'itemId':'fy01','itemName':'金币','unitPrice':'1','quantity':'%d'%balance,'imageUrl':'http://cp.206m.tj.twsapp.com/static/gold.png','description':'《风云天下OL》游戏金币，可用于购买消除CD、训练位、定向洗炼等游戏增值服务。','type':'1','subType':'2'}]}
                post_data = json.dumps(post_data).replace(': ',':').replace(', ',',')
                #parameters['payInfo'] = post_data
                post_data = urllib.quote(post_data)
                post_data = 'payInfo=%s'%post_data
                
                print(post_data)
                query_url = 'http://openapi.3g.qq.com/payment/charge?appid=%s'%parameters['appid']
                
                result =  get_qq(consumer,access_token,query_url,parameters,post_data)
                result = json.loads(result)
                if result.get('entry',None)!= None:
                    result_code = result['entry'][0]['status']
                    order_id = result['entry'][0]['paymentId']
                    if result_code == '2':
                        #发放金币
                        balance = balance / 10

                        result_code = save_action(server_id,player_id,order_id,balance)
    except Exception,e:
        result_code = -1
        print('pay qq has error',e)

    return render_to_response('pay/pay_post.html',{'pay_status':result_code})


def get_qq(consumer,token,get_url,parameters,post_data=None):
    import oauth.oauth as oauth
    import httplib
    if post_data == None:
        method = 'GET'
    else:
        method = 'POST'
    the_url = get_url.split('?')[0]
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token = token, http_method=method, http_url=the_url,parameters=parameters)
    oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), consumer, token)

    #urlInfo = httplib.urlsplit(get_url)
    #print(RESOURCE_URL)
    if get_url.find('https://')>-1:
        connection = httplib.HTTPSConnection('10.172.48.92',3300,timeout=5)
    else:
        connection = httplib.HTTPConnection('10.172.48.92',3300,timeout=5)
    
    connection.connect()
    data_type = 'x-www-form-urlencoded'
    print(oauth_request.to_header()['Authorization'])
    
    if post_data:
        connection.putrequest("POST", get_url)
        connection.putheader("Content-Length", len(post_data))
        connection.putheader("Content-Type", "application/x-www-form-urlencoded")
        connection.putheader("Content-Type", "application/%s"%data_type)
    else:
        connection.putrequest("GET", get_url)
        connection.putheader("Content-Length", 0)
    
    connection.putheader('Authorization',oauth_request.to_header()['Authorization'])
    
    connection.putheader("Connection", "close")
    connection.endheaders()

    if post_data:
        connection.send(post_data)
#    connection.request(method,get_url,post_data, headers=oauth_request.to_header())

    response = connection.getresponse()
    result = str(response.read())
    print(result)
    return result


def save_action(server_id,player_id,order_id,amount):
    from services.views.pay import getPlayerChannelId
    pay_channel = PayChannel.objects.get(func_name='qq')
    the_action = PayAction()
    the_action.pay_type = pay_channel.id
    the_action.channel_id = getPlayerChannelId(server_id,player_id)
    the_action.channel_key = pay_channel.channel_key
    the_action.server_id = server_id
    the_action.order_id = order_id
    the_action.pay_user = player_id
    the_action.post_amount = amount
    the_action.pay_amount = amount
    the_action.pay_status = 2
    the_action.pay_gold = pay_channel.get_gold(the_action.pay_amount)
    the_action.extra = pay_channel.get_extra(the_action.pay_gold) 
    the_action.post_time = datetime.datetime.now()
    the_action.last_time = datetime.datetime.now()
    the_action.set_query_id()
#    the_action.last_ip = request.META.get('REMOTE_ADDR','')
    the_action.remark = 'qq充值'
#                        the_action.save(using='write')
    the_action.safe_save()
    return the_action.query_id
    

def confirm_qq(request):
    import Crypto.Cipher.DES3 as DES
    desKey = '9SzZujdaJcozFbY7cE1q'
    result_code = 1
    post_data_str = request.raw_post_data
    the_des = DES.new(desKey)
    post_data = {}
    try:
        
        post_data_str = the_des.decrypt(post_data_str)
        post_data_str = '{"%s"}'%(post_data_str.replace('=','":"').replace('&','","'))
        post_data = json.loads(post_data_str)
        
        pay_actions = PayAction.objects.filter(query_id=post_data['linked'])
        if len(pay_actions)>0:
            the_action = pay_actions[0]
            if the_action.pay_status < 2:
                
                pay_channel = PayChannel.objects.get(func_name='qq',link_id=post_data['goodsId'])
                the_action.last_time = datetime.datetime.now()
                the_action.order_id = post_data['buyId']
                the_action.post_amount = int(post_data['goodsCount'])
                the_action.pay_amount = the_action.post_amount
                the_action.pay_gold = the_action.pay_amount * pay_channel.exchange_rate
                the_action.pay_status = 2
                the_action.remark = post_data['type']
                the_action.save(using='write')
                result_code = 0
    except:
        result_code = -1
        pass
    
    pay_status = 'uid=%s&linkId=%s&buyId=%s&goodsId=%s&goodsCount=%s&status=%s'%(post_data.get('uid',''),post_data.get('linkId',''),post_data.get('buyId',''),post_data('goodsId',''),post_data('goodsCount',''),result_code)
    pay_status = the_des.encrypt(pay_status)
    return render_to_response('pay/pay_post.html',{'pay_status':pay_status})