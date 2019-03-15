# -*- coding: utf-8 -*-
#已测   POST  http://127.0.0.1:8002/service/confirm/downjoy?result=1&orderid=120507224627804959449D&amount=10&uif=122&utp=11&eif=14_122_167_2&pcid=11&cardno=111&timestamp=123123&errorcode=122&remark=hello&verstring=a2ead439d7dcb397baf5d90f9b53efe4
from services.models.pay import PayChannel
from services.views import md5
import urllib, time


def pay_efun(payAction,pay_channel={},host_ip='service.fytxonline.com'):

    if pay_channel==None:
        pay_channel = PayChannel.objects.using('read').get(id=payAction.pay_type)
        
    gameCode = pay_channel.get_config_value('app_id', 'lsj')
    key = pay_channel.get_config_value('app_key', 'B708A6BC2006911EDF5AC3871E7FB7CF')
    #timestamp = payAction.post_time.strftime('%Y%m%d%H%M%S')
    timestamp = time.mktime(payAction.post_time.timetuple())
    
    serverCode = '%ss%s' % (gameCode,payAction.server_id)
    creditId = payAction.query_id
    userId = payAction.pay_user
    payFrom = pay_channel.get_config_value('payFrom', 'efun_efun_efun_lsj')
    #md5Str:   new MD5(gameCode+serverCode+credited+userId+payFrom+time+key)
    
    md5Str = '%s%s%s%s%s%s%s' % (gameCode, serverCode, creditId, userId, payFrom, timestamp, key)
    print md5Str
    md5Str = md5(md5Str)
    print md5Str
    language = 'tw'
    remark = ''
    
    data = {}
    data['gameCode'] = gameCode
    data['serverCode'] = serverCode
    data['creditId'] = creditId
    data['userId'] = userId
    data['payFrom'] = payFrom
    data['time'] = timestamp
    data['md5Str'] = md5Str
    data['language'] = language
    data['remark'] = remark
    
    #http://pay.efun.com/payForward_toPay.shtml?
    #gameCode=lsj
    #&serverCode=lsjs1
    #&creditId=12121212
    #&userId=1
    #&payFrom=efun_efun_efun_lsj
    #&time=134434343434
    #&md5Str=xxxxxxxxxxxxxxxx
    #&language=tw
    #&remark=xxxxxxxxxxxxxxx
     
     
    result_code = 1
    msg = urllib.urlencode(data)
    
    return (result_code,msg)
