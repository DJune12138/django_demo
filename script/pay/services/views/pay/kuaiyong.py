#encoding:utf8

import base64
import urllib
from M2Crypto import *
from django.http import HttpResponse
from services.http import http_post

default_public_key = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCqROZ5DqfDRjKcq
BaCytnofefc3qC6VyTgkVcsp+DkFU/vWydyVMuKJNHDtLp58gbIct
GIZCqlR0DcT8OTnDs3tk0NSLimHbr3teSguT4Z9ldg80MuwJ1ul/p
Dg11Gy0jfYKwYLkmNkEMBuXkPTIwBhrIYtr7YKymaHvIngJ77IQID
AQAB
-----END PUBLIC KEY-----'''

def confirm_kuaiyong_get_link_id(request):
    return request.POST.get("subject", "").strip()

def confirm_kuaiyong(request, pay_channel):
    public_key = pay_channel.get_config_value("key", default_public_key)
    verify_url = "http://service.yhzbonline.com/service/query/kuaiyong"

    #print request.POST
    p = lambda x,y='': request.POST.get(x, y)
    notify_data = p("notify_data")
    orderid = p("orderid")
    dealseq = p("dealseq")
    uid = p("uid")
    subject = p("subject")
    ver = p("v")
    sign = p("sign")

    server_id = player_id = pay_amount = 0
    order_id = remark = result_msg = ""

    try:
        pub_key = get_m2c_pub(public_key)
        nd = decrypt(notify_data, pub_key)
        nd = url_decode(nd) if nd else {}

        sign_con = "dealseq=" + dealseq + "&notify_data=" + notify_data + "&orderid=" + orderid + "&subject=" \
                   + subject + "&uid=" + uid + "&v=" + ver

        verify_result = http_post(verify_url, "data=%s&sign=%s" % (base64.b64encode(sign_con), urllib.quote(sign)))
        if int(verify_result) == 1:
            extra_info = dealseq.split("_")
            server_id = int(extra_info[0])
            player_id = int(extra_info[1])
            order_id = orderid
            pay_amount = float(nd["fee"])
            result_msg = "success"
        else:
            result_msg = "fail"
    except Exception,e:
        import traceback
        traceback.print_exc()

    return {"server_id":server_id, "player_id":player_id, "order_id":order_id, "amount":pay_amount, "remark":remark, "result_msg":result_msg}

def query_kuaiyong(request):
    pub_key = default_public_key

    print "==== verify ====",request.POST
    content = request.POST.get("data", "")
    sign = request.POST.get("sign", "")
    if content:
        content = base64.decodestring(content)

    m2c_key = get_m2c_pub(pub_key)
    result = 0
    try:
        result = verify(content, sign, m2c_key)
        print "verify result: ", result
    except Exception,e:
        return HttpResponse(e)

    return HttpResponse(str(result))


def url_decode(decode_str):
    ret_data = dict([tuple(i.split("=")) for i in decode_str.split("&")])
    return ret_data

def get_m2c_pub(pub_string):#将公钥字符串转为m2c的对象
    return RSA.load_pub_key_bio(BIO.MemoryBuffer(pub_string))

def decrypt(data,m2c_pub):#公钥解密数据
    data = base64.decodestring(data)
    _maxlength = 128
    l_dstr = [ m2c_pub.public_decrypt(data[i*_maxlength:_maxlength*(i+1)],RSA.pkcs1_padding) for i in  xrange(len(data)/_maxlength) ]
    return ''.join(l_dstr)

def verify(data,signature,m2c_pub):#签名认证
    m = EVP.MessageDigest('sha1')
    m.update(data)
    digest = m.final()
    signature = base64.decodestring(signature)
    return m2c_pub.verify(digest,signature,algo='sha1') or False
