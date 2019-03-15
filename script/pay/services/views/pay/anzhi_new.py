#coding=utf-8

import base64, json
from Crypto.Cipher import DES3

def confirm_anzhi_new_get_link_id(reqeust):
    return ''


def confirm_anzhi_new(request, pay_channel):
    secret = pay_channel.get_config_value("app_secret", "DIdJW7edGVW44KNaWWvebyo1")
    
    print request.POST
    data = request.POST.get("data")

    server_id = player_id = order_id = pay_amount = 0
    result_msg = ''
    remark = ''

    try:
        des_db = des3_decrypt(data, secret)
        print '=====', des_db
        if not des_db is None:
            server_id, player_id = des_db.get("cpInfo", "").split("_")
            order_id = int(des_db.get("orderId", 0))
            pay_amount = int(des_db.get("payAmount", 0)) / 100
            result_msg = "success"
        else:
            result_msg = "fail"
            remark = "decrypt fail"
    except Exception,e:
        print e

    return {"server_id":int(server_id), "player_id":int(player_id), "order_id":order_id, "amount":pay_amount, "remark":remark, "result_msg":result_msg}


def des3_decrypt(data, key):
    if len(data) % 8 != 0:
        return None
	
    try:
        obj = DES3.new(key, DES3.MODE_ECB, '00000000')
        des = obj.decrypt(base64.decodestring(data))
	print "-----",des
        if des:
            return json.loads(des[:des.index('}')+1])
    except Exception,e:
	print e
        return None
