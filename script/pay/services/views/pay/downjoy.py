# -*- coding: utf-8 -*-
#已测   POST  http://127.0.0.1:8002/service/confirm/downjoy?result=1&orderid=120507224627804959449D&amount=10&uif=122&utp=11&eif=14_122_167_2&pcid=11&cardno=111&timestamp=123123&errorcode=122&remark=hello&verstring=a2ead439d7dcb397baf5d90f9b53efe4
from services.models.pay import PayChannel
from services.views import md5
import urllib


def pay_downjoy(payAction,pay_channel={},host_ip='service.fytxonline.com'):
#    from services.DES import DES
    merchantid = pay_channel.get_config_value('merchantid',314)
    gameId = pay_channel.get_config_value('gameId',2)
    serverId = pay_channel.get_config_value('serverId',1)
    merchantKey = pay_channel.get_config_value('merchantKey','DBu0V%pv')
#    desKey = 'REJ1MFYlcHY=' 
#    postLinks = ('http://189hi.cn/189pay2/shenzhoufujava_feed.do',
#                'http://189hi.cn/189pay2/yeepayjunnetjava_feed.do',
#                'http://189hi.cn/189pay2/yeepayszxjava_feed.do',
#                'http://189hi.cn/189pay2/yeepayunicomjava_feed.do',
#                'http://189hi.cn/189pay2/yeepaysndajava_feed.do',
#                'http://189hi.cn/189pay2/yeepayzhengtujava_feed.do',
#                'http://189hi.cn/189pay2/yeepaytelecomjava_feed.do',
#                )
    #postTypes = ('001','010','006','007','005','012','016')
    if pay_channel==None:
        pay_channel = PayChannel.objects.using('read').get(id=payAction.pay_type)

    callback_url = 'mangosanguo' #http://%s/service/confirm/downjoy'%host_ip
    uif = payAction.card_no
    utp = 0
    eif = payAction.query_id
#    cardno= payAction.card_no
#    cardpwd = payAction.card_pwd
#    amount = int(payAction.post_amount)
    timestamp = payAction.post_time.strftime('%Y%m%d%H%M%S')
#    uip = payAction.pay_ip
    
#    the_des = DES(desKey)
#    cardno = the_des.Encrypt(cardno)
#    cardpwd = the_des.Encrypt(cardpwd)
    
    postData = 'mid=%s&gid=%s&sid=%s&uif=%s&utp=%d&eif=%s&bakurl=%s&timestamp=%s'%(merchantid,gameId,serverId,uif,utp,eif,callback_url,timestamp)
    
    verString = '%s&merchantkey=%s'%(postData,merchantKey)
    verString = md5(verString).lower()
    #postData = '%s&verstring=%s'%(postData,verString)
    
    # 拼订单提交数据
    data = {}
    data["mid"] = merchantid
    data["gid"] = gameId
    data["sid"] = serverId
    data["uif"] = uif
    data["utp"] = utp
    data["eif"] = eif
    data["bakurl"] = callback_url 
    data["timestamp"] = timestamp
    data["verstring"] = verString

    result_code = 1
    msg = urllib.urlencode(data)
    #msg = '%s?%s'%(pay_channel.post_url,urllib.urlencode(data))
    
#    #print(pay_channel.post_url,data,verString)
#    result = http_post(pay_channel.post_url,urllib.urlencode(data))
#
#    result_code = int(result.split('&')[0].split('=')[1])
#    msg = ''
#    if result.split('&').__len__()>1:
#        msg = result.split('&')[1].split('=')[1]
        
    return (result_code,msg)



def confirm_downjoy_get_link_id(request):
    return ''

def confirm_downjoy(request,pay_channel={}):
    merchantid = pay_channel.get_config_value('merchantid',314)
    gameId = pay_channel.get_config_value('gameId',2)
    serverId = pay_channel.get_config_value('serverId',1)
    merchantKey = pay_channel.get_config_value('merchantKey','DBu0V%pv')
    
    result = request.POST.get('result','')
    order_id = request.POST.get('orderid','')
    pay_amount = request.POST.get('amount','')
#    mid = request.POST.get('mid','')
#    gid = request.POST.get('gid','')
#    sid = request.POST.get('sid','')
    uif = request.POST.get('uif','')
    utp = request.POST.get('utp','')
    eif = request.POST.get('eif','')
    pcid = request.POST.get('pcid','')
    
    cardno = request.POST.get('cardno','')
    timestamp = request.POST.get('timestamp','')
    errorcode = request.POST.get('errorcode','')
    remark = request.POST.get('remark','')
    verstring = request.POST.get('verstring','')
    
    verString = u'result=%s&orderid=%s&amount=%s&mid=%s&gid=%s&sid=%s&uif=%s&utp=%s&eif=%s&pcid=%s&cardno=%s&timestamp=%s&errorcode=%s&merchantkey=%s'%(result,order_id,pay_amount,merchantid,gameId,serverId,uif,utp,eif,pcid,cardno,timestamp,errorcode,merchantKey)
#    print(verString)
    verString = md5(verString)
    print(verstring,verString)

    pay_status = 'unknow error'
    pay_action_id = eif
    amount = 0
    server_id = 0
    player_id = 0
    pay_type = 0
    try:
        print verString
        if verString == verstring:
            server_id,player_id,pay_type,gameId = pay_action_id.split('_')
            server_id = int(server_id)
            player_id = int(player_id)
            
            if int(result) == 1:
                amount = float(pay_amount)              
            
            pay_status = 'success'
        else:
            pay_status = 'error sign'
    except:
        pay_status = 'error unknow'
    return {'server_id':server_id,'player_id':player_id,'query_id':pay_action_id,'pay_type':pay_type,'order_id':order_id,'amount':amount,'remark':remark,'result_msg':pay_status}

