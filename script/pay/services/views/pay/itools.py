# -*- coding: utf-8 -*-
import json
from Crypto import *

import base64
from M2Crypto import *

public_key = '''
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC2kcrRvxURhFijDoPpqZ/IgPlA
gppkKrek6wSrua1zBiGTwHI2f+YCa5vC1JEiIi9uw4srS0OSCB6kY3bP2DGJagBo
Egj/rYAGjtYJxJrEiTxVs5/GfPuQBYmU0XAtPXFzciZy446VPJLHMPnmTALmIOR5
Dddd1Zklod9IQBMjjwIDAQAB
-----END PUBLIC KEY-----
'''

def confirm_itools_get_link_id(request):
    try:
        m2c_pub = get_m2c_pub(public_key)
        notify_data = request.REQUEST.get('notify_data','')
        notify_data = decrypt(notify_data, m2c_pub)
        notify_data = json.loads(notify_data)
        return ''
    except:
        return ''

def get_m2c_pub(pub_string):#将公钥字符串转为m2c的对象
    return RSA.load_pub_key_bio(BIO.MemoryBuffer(pub_string))

def decrypt(data,m2c_pub):#公钥解密数据
    data = base64.decodestring(data)
    _maxlength = 128
    l_dstr = [ m2c_pub.public_decrypt(data[i*_maxlength:_maxlength*(i+1)],RSA.pkcs1_padding) for i in  xrange(len(data)/_maxlength) ]
    return ''.join(l_dstr)

def verify(data,sign,m2c_pub):#签名认证
    m = EVP.MessageDigest('sha1')
    m.update(data)
    digest = m.final()
    sign = base64.decodestring(sign)
    return m2c_pub.verify(digest,sign,algo='sha1') or False
    
def confirm_itools(request,pay_channel):
    
    public_key = pay_channel.get_config_value('public_key', '''
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC2kcrRvxURhFijDoPpqZ/IgPlA
gppkKrek6wSrua1zBiGTwHI2f+YCa5vC1JEiIi9uw4srS0OSCB6kY3bP2DGJagBo
Egj/rYAGjtYJxJrEiTxVs5/GfPuQBYmU0XAtPXFzciZy446VPJLHMPnmTALmIOR5
Dddd1Zklod9IQBMjjwIDAQAB
-----END PUBLIC KEY-----
    ''')
    

    notify_data = request.POST.get('notify_data','')
    sign  = request.POST.get('sign','').encode('utf-8')
#    print '-' * 20
#    print notify_data,sign
    
    m2c_pub = get_m2c_pub(public_key)
    notify_data = decrypt(notify_data, m2c_pub)
    
    query_id = ''
    order_id = ''
    pay_amount = 0
    remark = ''
    result_msg = 'fail'
    server_id = player_id = ''
    if verify(notify_data,sign,m2c_pub):
        try:
            notify_data = json.loads(notify_data)
            #print notify_data
            #{"order_id_com":"2013050900000712",”user_id”:”10101”,”amount”:”0.10”,”account”:”test001”,”order_id”:”2013050900000713”,”result”:”success”}
#            order_id_com    string    发起支付时的订单号
#            user_id    string    支付的用户id
#            amount    string    成功支付的金额
#            account    string    支付帐号
#            order_id    string    支付平台的订单号
#            result    string    支付结果
            open_id = notify_data.get('user_id')
            #s_u_o_id = [ int(x) for x in notify_data.get('order_id_com', '').split('_') if x.isdigit()]#包含sid_uid_order_id 客服端提交的订单
            s_u_o_id = notify_data.get('order_id_com', '').split('_')
            server_id = int(s_u_o_id[0])
            player_id = int(s_u_o_id[1])
            query_id = s_u_o_id[2:]
            #server_id,player_id,query_id = s_u_o_id if len(s_u_o_id) == 3 else ['','','']
            order_id = notify_data.get('order_id', '')
            amount = float(notify_data.get('amount', ''))
            if 'success' == notify_data.get('result', '') and amount > 0:
                pay_amount = amount
                result_msg = 'success'
                
        except Exception,e:
            print('confirm itools has an error:',e)
    
    #print   {"server_id":server_id, "player_id": player_id,'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}
    return  {"server_id":server_id, "player_id": player_id,'query_id':query_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}
