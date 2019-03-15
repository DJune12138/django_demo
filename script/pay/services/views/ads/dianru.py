#! /usr/bin/python
# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.shortcuts import render_to_response
from services.models.adapply import AdConfig
from services.models.log import Log
from services.http import http_post
import datetime,json

def download(request):
    #appId=472885640&mac=1C:AB:A7:D6:E7:81&ifa=111F7987-6E2F-473A-BFED-E4C52CB5A6DC&source=domob

    appid = request.GET.get('appId', '')
    md5_str = ''
    mac = request.GET.get('mac', '')
    ifa = request.GET.get('ifa', '')
    source = request.GET.get('source', '')
    adconfig = None
    try:
        adconfig = AdConfig.objects.using('adapply').filter(app_id = appid)
        if 0 >= adconfig.__len__():
            raise Exception("not find AdConfig :%s" % appid)
        adconfig = adconfig[0]
        conn = connections['write']
        cursor = conn.cursor()
        ip = request.META['REMOTE_ADDR']
        sql = "INSERT INTO log_dianru (log_type, log_server, log_channel, log_user, log_data, log_result, f1, f2, f3, f4, f5, f6, log_time) VALUES( 0,0,0,0,0,0,%s,%s,%s,%s, %s, '',NOW() )"
        cursor.execute(sql, (appid, mac, ifa, source, ip))
        #conn.commit()
    except Exception, ex:
        print 'log_dianru error:', ex
        return HttpResponse("internal error", status = 502)

    #response = HttpResponse(adconfig.url, status = 302)

    #return response

    return HttpResponseRedirect("https://itunes.apple.com/cn/app/feng-yun-tian-xia-2013shi/id579853996?mt=8")

def active(request, channel_key):
    #mac=%s&idfa=%s&playerId=%s&serverId=%s
    g           = lambda x,y:request.GET.get(x, request.POST.get(x, y))
    mac         = g('mac', '')
    idfa        = g('idfa', '')
    playerId    = g('playerId', '')
    serverId    = g('serverId', '')
    #/client/ads/dianru/active/0100200000&mac=406C8F16CDE3&idfa=0D1A404B-E1EF-4AEB-9DAA-41E027AE2ED9&playerId=46178032&serverId=34
    if -1 == mac.find(':') and '' != mac:
        new_mac = ''
        for i in range(0, 6):
            cursor = 2*i
            new_mac = '%s:%s' % (new_mac , mac[cursor:cursor+2])
        mac = new_mac[1:]

    config = AdConfig.objects.using('adapply').filter(channel_key=channel_key)
    if 0 >= config.__len__():
        return HttpResponse("not find config")

    config = config[0]
    appid = config.app_id
    conn = connections['write']
    cursor = conn.cursor()
    if '00000000-0000-0000-0000-000000000000' != idfa:
        sql = 'SELECT `id`, `f3` FROM log_dianru WHERE f1 = %s AND f2 = %s AND f3 = %s'
        cursor.execute(sql, (appid, mac, idfa))
    else:
        sql = 'SELECT `id`, `f3` FROM log_dianru WHERE f1 = %s AND f2 = %s AND log_result = 0'
        cursor.execute(sql, (appid, mac))

    data_list = cursor.fetchall()
    if 0 >= data_list.__len__():
        return HttpResponse("not exists")
    model_id = int(data_list[0]["id"])
    _idfa = data_list[0]["f3"]
    sql = 'UPDATE log_dianru SET log_result =  1, log_user = %s, log_server = %s WHERE id = %s'
    cursor.execute(sql, (playerId, serverId, model_id))
    #conn.commit()
    if '00000000-0000-0000-0000-000000000000'==idfa:
        idfa = _idfa
    return HttpResponse(return_data(appid, mac, idfa))

def getDomobSign(appid, udid, ma, ifa, oid, key):
    import hashlib
    return hashlib.md5('%s,%s,%s,%s,%s,%s' %(appid, udid, ma, ifa, oid, key)).hexdigest()
    
def return_data(appid, mac, idfa):
    result_msg = "fail"
    #http://e.domob.cn/track/ow/api?appId=531266294&udid=7C:AB:A3:D6:E7:81&ifa=511F7987-6E2F-423A-BFED-E4C52CB5A6DC&acttime=1391502359&returnFormat=1
    try:
        request_url = 'http://e.domob.cn/track/ow/api/postback?appId=%s&udid=%s&ifa=%s&acttime=%s&returnFormat=1&sign=%s' % (appid, mac, idfa, int(time.time()), getDomobSign(appid, mac, '', idfa, '', 'cebbdcbd989326661878649d6565f719'))
        request_data = http_post(request_url, timeout_param = 5) 
        json_data = json.loads(request_data)
        status = json_data.get('success', False)
        message = json_data.get('message', '')
        if status:
            result_msg = "success"
        else:
            result_msg = message
        
    except Exception, ex:
        print 'dianru error ', ex
        result_msg = "internal error"
    
    return result_msg
