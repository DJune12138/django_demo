# !/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time



DEFAULT_POST_HEADERS = {
    'Content-Type': 'application/json',
    'authentication':'dVMHmvaKbdcaiuZS5jZddi'
}

BASE_URL = "https://api2.appsflyer.com/inappevent/"


def upload_douzhen_post(params, add_to_headers=None):
    headers = DEFAULT_POST_HEADERS
    if add_to_headers:
        headers.update(add_to_headers)
    # 包装发送信息
    try:
        data = {}
        data["appsflyer_id"] = params["appsflyer_id"]

        if params["identify"]=="ios":
            data["idfa"] = params["advertising_idfa"]
            data["bundle_id"]= "tw.9453play.mwts"
        elif params["identify"]=="android":
            data["advertising_id"]=params["advertising_idfa"]

        data["eventName"] = "af_purchase"
        data["eventCurrency"] = "TWD"
        data["af_events_api"]="true"
        val = {}
        val["af_revenue"]=params["pay_amount"]
        val["af_content_type"]="wallets"
        val["af_quantity"]= 1
        data["eventValue"]= json.dumps(val)
        postData = json.dumps(data)

        #发送请求
        path = params["douzhen_appid"]
        url = BASE_URL + path
        response = requests.post(url, postData, headers=headers, timeout=10)

        if response.status_code == 200:
            return { "status": response.status_code,"msg":"ok","params":postData}
        else:
            return { "status": response.status_code,"msg":"faill"}
    except Exception as e:
        print "upload_douzhen Error:", e
        return {"msg": e}
