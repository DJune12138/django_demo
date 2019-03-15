#coding=utf-8

import rsa
import base64
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

RESULT_STR = "result=%s&resultMsg=%s"

def confirm_oppo_get_link_id(request):
    return ''

def confirm_oppo(request, pay_channel):
    public_key = pay_channel.get_config_value('public_key', '''-----BEGIN PUBLIC KEY-----
                                                            MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmreYIkPwVovKR8rLHWlFVw7YD
                                                            fm9uQOJKL89Smt6ypXGVdrAKKl0wNYc3/jecAoPi2ylChfa2iRu5gunJyNmpWZzl
                                                            CNRIau55fxGW0XEu553IiprOZcaw5OuYGlf60ga8QT6qToP0/dpiL/ZbmNUO9kUh
                                                            osIjEu22uFgR+5cYyQIDAQAB
                                                            -----END PUBLIC KEY-----''')
    
    rp = request.POST
    notifyId = rp.get("notifyId", "")
    partnerOrder = rp.get("partnerOrder", "")
    productName = rp.get("productName", "")
    productDesc = rp.get("productDesc", "")
    price = rp.get("price", 0)  #以分为单位
    count = rp.get("count", 0)
    attach = rp.get("attach", "")
    sign = rp.get("sign", "")

    server_id = 0
    order_id = ''
    player_id = 0
    pay_amount = 0
    result_msg = ''
    remark = ''


    try:
        basestr = "notifyId=%s&partnerOrder=%s&productName=%s&productDesc=%s&price=%s&count=%s&attach=%s" \
                  % (notifyId, partnerOrder, productName, productDesc, price, count, attach)
	print "========",basestr
	print "========",sign
        publicKey = rsa.PublicKey.load_pkcs1_openssl_pem(public_key)
        verify = rsa.verify(basestr, base64.decodestring(sign), publicKey)
        print "--------",verify
        if verify:
            attach_split  = attach.split("_")
	    server_id = int(attach_split[0])
	    player_id = int(attach_split[1])
            order_id = notifyId
            pay_amount = int(price) / 100
            result_msg = RESULT_STR % ("OK", "回调成功")
        else:
            remark = "sign error"
            result_msg = RESULT_STR % ("FALT", "验签失败")
    except Exception,e:
        print e

    return {"server_id":server_id, "player_id":player_id, "order_id":order_id, "amount":pay_amount, "remark":remark, "result_msg":result_msg}
