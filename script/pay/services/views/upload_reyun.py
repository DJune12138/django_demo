# !/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import urllib
import json

DEFAULT_POST_HEADERS = {
    'Content-Type': 'application/json'
}

BASE_URL = "http://log.reyun.com"

ANDORID = "a3f866e298a999b1d60ebacc93b1677f"
IOS = "9335c3afe1b849b2f9cefb8f22e81186"

def upload_reyun_post(params,add_to_headers=None):
# 100720EE-6181-4AD5-89FA-2262436531ED {"what":"payment","appid":"9335c3afe1b849b2f9cefb8f22e81186","context":{"tz":"+8","iapamount":"6480.0","ip":"14.23.124.148","ry_ts":"1501037399027","virtualcoinamount":"6480.0","deviceid":"unknown","serverid":"2","transactionid":"20170721204500122143AC62","iapname":"3元每日礼包","currencytype":"CNY","currencyamount":"648.0","channelid":"4","paymenttype":"free"},"where":"payment","when":"2017-07-26 10:49:59","ds":"2017-07-26","who":"2097437"}
    headers = DEFAULT_POST_HEADERS
    if add_to_headers:
        headers.update(add_to_headers)
    #包装发送信息
    try:
        data = {}
        print params
        # data["appid"] = IOS if params["device_type"] == "appstore"  else ANDORID
        data["appid"] = params["appid"]
        data["who"] = params["player_id"]
        context = {}
        context["idfa"] = context["deviceid"] = params["mobile_key"] or "unknown"
        context["transactionid"] = params["query_id"]
        context["paymenttype"] = params["payType"] or "unknown"
        context["currencytype"] = params["currency"]
        context["currencyamount"] = params["pay_amount"]
        context["virtualcoinamount"] = params["pay_gold"]
        context["iapname"] = params["charge_type"]
        context["iapamount"] = params["pay_gold"]
        context["serverid"] = params["server_id"]
        context["channelid"] = params.get("channel_key","unknown")
        # context["idfa"] =  params.get("idfa","100720EE-6181-4AD5-89FA-2262436531ED") #广告标识
        context["idfv"] =  params.get("idfv","unknown") #Vindor标示符
        context["level"] = -1
        data["context"] = context
        postData = json.dumps(data)
        print data
        path = "/receive/rest/payment"
        # if not path:
        #     return {"status":-1,"msg":"path error"}

        url = BASE_URL + path
        response = requests.post(url,postData,headers=headers,timeout=10)
        if response.status_code == 200:
            result = response.json()
            print "upload reyun result:",result
            if result.has_key("status") and result["status"] == 0:
                return {"status":0,"msg":"success"}
            return {"status":-1,"msg":result}
        else:
            return {"status":-1,"msg":response.json()}
    except Exception as e:
        print "upload_reyun Error:",e
        return {"status":-1,"msg":e}
