# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from xml.dom import minidom
import json, base64, hashlib, re
from Crypto.Cipher import DES3
from services.alipay import getNodeTextByTagName
from services.models.pay import PayAction

def confirm_gash_get_link_id(request):
    return ''


def confirm_gash(request, pay_channel={}):
    # 取得回傳結果
    
    transData = request.POST.get('data')
    
    #print 'confirm code:::', transData
    
    #file_object = open('/data/gash_response_file.txt', 'w')
    #file_object.write(transData)
    #file_object.close()
    
    
    # 解析回傳結果
    trans =  base64.decodestring(transData)
    
    #print 'trans:::', trans
    
    trans = minidom.parseString(trans)
    trans =  trans.getElementsByTagName("TRANS")
    trans = trans[0]
    
    rcode = getNodeTextByTagName(trans, "RCODE")
    coid = getNodeTextByTagName(trans, "COID")
    cid = getNodeTextByTagName(trans, "CID")
    erpc = getNodeTextByTagName(trans, "ERPC")
    rrn = getNodeTextByTagName(trans, "RRN")
    cuid = getNodeTextByTagName(trans, "CUID")
    amount = getNodeTextByTagName(trans, "AMOUNT")
    #product_id = getNodeTextByTagName(trans, "PRODUCT_ID")
    paid = getNodeTextByTagName(trans, "PAID")
    #memo = getNodeTextByTagName(trans, "MEMO")
    
    platform = get_platform(cid)
    #cid = gash_cfg.get(platform).get('CID')
    #print (cid, coid, rrn, cuid, amount, rcode, platform)
    server_sign = get_erpc(cid, coid, rrn, cuid, amount, rcode, platform)
    
    #print 'sign begin:::'
    #print (erpc,server_sign)
    
    #自己用的参数
    pay_amount = 0
    order_id = ''
    result_msg = 'error'
    remark = ''
    query_id = coid
    link_id = ''
    if erpc == server_sign and erpc != "" and server_sign != "":
        
        if rcode == "0000":
            try:
                remark = json.dumps({'coid':coid, 'paid':paid, 'amount': amount, 'cid':cid})
                settle_rcode = settle(coid, paid, amount, cid)
                settle_rcode = settle_rcode.strip()
                order_id = rrn
                if "0000" == settle_rcode:
                    print 'settle success:::'
                    gash_point = float(amount)
                    
                    cuid = cuid.strip().upper()
                    link_id = cuid
                    if get_erp_id(paid) == 'PINHALL':
                        if cuid == 'MYR':
                            gash_point = gash_point * 9.6
                        elif cuid == 'HKD':
                            gash_point = gash_point * 0.38
                    pay_amount = gash_point
                    print ' final pay_amount:::', pay_amount
                    result_msg = '儲值成功'
                else:
                    pay_amount = 0
                    #remark = gash_cfg.get('error_msg').get(settle_rcode, '')
                    result_msg = '請款失敗: <!-- %s -->' % remark
            except Exception, ex:
                print 'gash comfirm error   ', coid , ex
                pay_amount = 0
                remark = ex
                result_msg = '系統內部錯誤 <!-- %s -->' % remark
        else:
            remark = gash_cfg.get('error_msg').get(rcode, '')
            result_msg = remark
    else:
        remark = '簽名錯誤'
        result_msg = remark
        
    result_msg = '%s<script type="text/javascript">document.location="app:close";</script>'%result_msg
    result = {'link_id':link_id, 'query_id':query_id, 'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}
    
    return result

def client_settle(request):
    from django.http import HttpResponse
    
    operate_type = int(request.GET.get('type', request.POST.get('type', 0)))
    
    item_id = 0
    tmp = request.GET.get('id', request.POST.get('id', 0))
    if '' != tmp:
        item_id = int(tmp)
    
    query_id = request.POST.get('query_id', '')
    pay_type = request.POST.get('pay_type', '')
    cid = request.POST.get('cid', '')
    amount = request.POST.get('amount', 0)
    url = '/client/pay/gash/settle'
    if 0 == item_id and '' == query_id and '' == pay_type and 0 == amount:
        return render_to_response('pay/gash/settle.html', {"url":url, "type": operate_type, "id":item_id})
    
    if 0 != item_id:
        the_action = PayAction.objects.get(id = item_id)
        query_id = the_action.query_id
        try:
            json_data = json.loads(the_action.remark)#{'coid':coid, 'paid':paid, 'amount': amount, 'cid':cid}
            pay_type = json_data.get('paid', '')
            amount = float(json_data.get('amount', 0))
            cid = json_data.get('cid', '')
        except:
            return render_to_response('pay/gash/settle.html', {"url":url, "type": operate_type, "id":0})
    
    
    result = '请款成功'
    if 0 == operate_type:
        settle_rcode = settle(query_id, pay_type, amount, cid)
        if "0000" != settle_rcode:
            result = gash_cfg.get('error_msg').get(settle_rcode, settle_rcode)
        
    else:
        result = check_order(query_id, pay_type, amount)
        
    return HttpResponse(result)
    

def settle(query_id, pay_type, amount, cid):
    #print 'settle begin :::'
    platform = get_platform(cid)
    from suds.client import Client
    request_url = gash_cfg.get('settle_url')
    #print 'request_url:::', request_url
    client = Client(request_url, timeout = 10)
    try:
        trans = get_settle_xml(query_id, pay_type, amount, '', platform)
        result = client.service.getResponse(data=trans)
    except Exception, ex:
        client = Client(request_url, timeout = 20)
        try:
            trans = get_settle_xml(query_id, pay_type, amount, '', platform)
            result = client.service.getResponse(data=trans)
        except:
            print 'soap request settle error ',  query_id, ex
            return ''  
    
    
    print 'settle send code ::', query_id, trans
    print 'settle code ::', query_id, result
    
    result = base64.decodestring(result)
    
    try:
    
        result = minidom.parseString(result)
         
        r_trans =  result.getElementsByTagName("TRANS")[0]
         
        rcode = getNodeTextByTagName(r_trans, "RCODE")
    
    except Exception, ex:
        print 'settle xml parser error ', query_id, ex
        return ''
    
    return rcode 
      
def check_order(query_id, pay_type, amount, cid): 
    rcode = ''
     
    request_url = gash_cfg.get('checkorder_url')
    
    client = None
    if '' == rcode:
        rcode = '查单错误'
        
        from suds.client import Client
        client = Client(request_url, timeout=10)
        try:  
            platform = get_platform(cid)
            print 'amount:::', amount
            trans = get_check_order_xml(query_id, pay_type, amount, platform)
            result = client.service.getResponse(data=trans)
            print 'check send code :::', trans
            print 'check order code:::%s' % result
            result = base64.decodestring(result)
        except Exception, ex:
            print 'check_order error ', ex
        
        
        try:
            result = minidom.parseString(result)
                 
            r_trans =  result.getElementsByTagName("TRANS")[0]
                 
            rcode = getNodeTextByTagName(r_trans, "PAY_STATUS")
        except Exception, ex:
            rcode = 'parser xml error'
            
    check_order_map = {"S": "交易成功","F": "PA交易失敗", "0":"PA交易未完成 ","T": "PA交易逾時" ,"W" :"待確認(for ATM)" ,"C" :"已調退"} 
    print 'rcode:::', rcode
    rcode = check_order_map.get(str(rcode), rcode)
    
    return rcode
    
    

def get_check_order_xml(query_id, pay_type, amount, platform):
    cid = gash_cfg.get(platform).get('CID', '')
    coid = query_id
    cuid = gash_cfg.get('type').get(pay_type).get('type')
    
    erqc = get_erqc(cid, coid, cuid, amount, platform)
    erqc = erqc.strip()
    data = '''<?xml version="1.0" encoding="utf-8"?>
    <TRANS>
      <MSG_TYPE>0100</MSG_TYPE>
      <PCODE>200000</PCODE>
      <CID>%s</CID>
      <COID>%s</COID>
      <CUID>%s</CUID> 
      <AMOUNT>%s</AMOUNT>
      <ERQC>%s</ERQC>
    </TRANS>
    ''' % (cid, coid, cuid, amount, erqc)
    data = base64.encodestring(data)
    return data
    

def pay_gash(the_action,pay_channel = {},service_url='service.fytxonline.com'):
    
    pay_way = pay_channel.get_config_value('pay_way', '')
    platform = pay_channel.get_config_value('platform', 'taiwan')
    product_name = pay_channel.get_config_value('product_name', 'mgtx')
    end_date = the_action.post_time.strftime('2112-%m-%d %H:%M:%S')
    pay_url = 'http://%s/client/pay/gash/transaction?orderid=%s&platform=%s&product_name=%s'% (service_url,the_action.query_id, platform, product_name)
    if pay_way != 'card':
        pay_url = 'http://%s/client/pay/gash/telecom?orderid=%s&platform=%s&product_name=%s'% (service_url,the_action.query_id, platform, product_name)
    
    pay_url = u'{"beginDate":"%s","endDate":"%s","title":"Gash储值","size":[0.9,0.9],"position":[-1,-1],"url":"%s"}'%('2012-01-01 00:00:00',end_date,pay_url)
    
    return 1,pay_url
    


def pay_gash_telecom(request):
    orderid = request.GET.get('orderid', '')
    platform = request.GET.get('platform', 'taiwan')
    product_name = request.GET.get('product_name', 'mgtx')
    pargs = {}
    pargs["orderid"] = orderid
    pargs['platform'] = platform
    pargs['product_name'] = product_name
    return render_to_response('pay/gash/pay.html', pargs)
    
def pay_gash_transaction(request):
    g = lambda x,y:request.POST.get(x, request.GET.get(x, y))
    query_id = g('orderid', '0')
    platform = g('platform', 'taiwan')
    product_name = g('product_name', 'mgtx')
    amount = float(request.POST.get('amount', 0))
    pay_type = request.GET.get('type', '')#默认点卡储值
    
    if pay_type == '':
        pay_type = request.POST.get('type', 'COPGAM02')
    
    #platform = get_platform(pay_type)
    data = get_order_xml(query_id, pay_type, amount, '', '', platform, request.get_host(), product_name)
    #print 'pay code :::', data
    pargs = {}
    pargs['url'] = gash_cfg.get('order_url')
    pargs['data'] = data
    
    return render_to_response('pay/gash/transaction.html', pargs)
    
    

def get_order_xml(query_id, pay_type, amount, link_id, remark, platform, host_url, product_name = 'gold'):
    
    cid = gash_cfg.get(platform).get('CID', '')
    coid = query_id
    
    cuid = gash_cfg.get('type').get(pay_type).get('type')
    #mid = gash_cfg.get(platform).get('MID')
    #bid = gash_cfg.get(platform).get('BID')
    paid = pay_type
    
    return_url = 'http://%s/service/confirm/gash' % host_url
    erqc = get_erqc(cid, coid, cuid, amount, platform)
    
    erp_id = get_erp_id(paid)
    data = '<?xml version="1.0"?><TRANS><MSG_TYPE>0100</MSG_TYPE><PCODE>300000</PCODE><CID>%s</CID><COID>%s</COID><CUID>%s</CUID><PAID>%s</PAID><AMOUNT>%s</AMOUNT><RETURN_URL>%s</RETURN_URL><ORDER_TYPE>M</ORDER_TYPE><MEMO>fytx</MEMO><ERP_ID>%s</ERP_ID><PRODUCT_NAME>%s</PRODUCT_NAME><PRODUCT_ID></PRODUCT_ID><USER_ACCTID>%s</USER_ACCTID><ERQC>%s</ERQC></TRANS>'
    data = data % (cid, coid, cuid, paid, amount, return_url, erp_id, product_name, '', erqc)
    
    print 'data:::', data
    data = base64.encodestring(data)
    
    return data


def get_settle_xml(query_id, pay_type, amount, remark, platform):
    cid = gash_cfg.get(platform).get('CID', '')
    coid = query_id
    cuid = gash_cfg.get('type').get(pay_type).get('type')
    mid = gash_cfg.get(platform).get('MID')
    bid = gash_cfg.get(platform).get('BID')
    paid = pay_type
    amount = amount
    erqc = get_erqc(cid, coid, cuid, amount, platform)
    erqc = erqc.strip()
    data = '''<?xml version="1.0" encoding="utf-8"?>
    <TRANS>
      <MSG_TYPE>0500</MSG_TYPE>
      <PCODE>300000</PCODE>
      <CID>%s</CID>
      <COID>%s</COID>
      <CUID>%s</CUID>
      <PAID>%s</PAID>
      <AMOUNT>%s</AMOUNT>
      <ERQC>%s</ERQC>
      <MID>%s</MID>
      <BID>%s</BID>
      <MEMO>%s</MEMO>
    </TRANS>
    ''' % (cid, coid, cuid, paid, amount, erqc, mid, bid, remark)
    data = base64.encodestring(data)
    return data
     
 
def get_erqc(cid, coid, cuid, amount, platform):
    password = gash_cfg.get(platform).get('PASSWORD')
    key1 = gash_cfg.get(platform).get("PWD1")
    key2 = gash_cfg.get(platform).get("PWD2")
    
    amount = pad_amount(amount)
    _str = '%s%s%s%s%s' % (cid, coid, cuid, amount, password)
    
    _str = encrypt(_str, key1, key2)
    
    _str = _str.strip()
    
    #sha1  20位
    _str = hashlib.sha1(_str).digest()
    
    # base 64
    _str = base64.encodestring(_str)
    
    #去空格
    _str = _str.strip()
    
    return _str

def encrypt(_str, key, iv):
    key = base64.decodestring(key)
    iv = base64.decodestring(iv)
    
    des3 = DES3.new(key,DES3.MODE_CBC,iv) 
    
    #补位
    padding = DES3.block_size - (len(_str) % DES3.block_size)
    _str = _str + padding * chr(padding)
    
    #  3DES加密
    result = des3.encrypt(_str)
    
    # base 64
    result = base64.encodestring(result)
    
    result = re.sub('\s+','',result)
    
    return result

def decrypt(_str,key, iv):
    
    result = base64.decodestring(_str)
    
    #去空格
    result = re.sub('\s+','',result)
    
    #3DES
    des3 = DES3.new(key,DES3.MODE_CBC,iv) 
    result = des3.encrypt(_str)
    
    #去空格
    result = result.strip()
    
    #去除补位
    pad = ord(result[-1])
    result = result[:-pad]
    
    return result
    
    
    
def get_erpc(cid, coid, rrn, cuid, amt, rcode, platform):
    
    # 金额补14 位
    amt = pad_amount(amt)
    
    key1 = gash_cfg.get(platform).get("PWD1")
    key2 = gash_cfg.get(platform).get("PWD2")
    
    encrypt_data = '%s%s%s%s%s%s'% ( cid, coid, rrn, cuid, amt, rcode)
    
    result = encrypt(encrypt_data, key1, key2)
    
    #result = result.strip()
    
    #sha1  20位
    result = hashlib.sha1(result).digest()
    
    #result = result.strip()
    
    # base 64
    result = base64.encodestring(result)
    
    #去空格
    result = result.strip()
    
    
    return result

#处理amount 
# 驗證用的 AMOUNT 需整理成 14 碼
def pad_amount(amount):
    str_amount = str(amount)
    point_index = str_amount.find(".")
    str_amount_len = str_amount.__len__()
    if -1 != point_index:
        tmp = ''
        xiaoshu_len = str_amount_len - (point_index + 1)
        if xiaoshu_len > 2:
            tmp = str_amount[point_index + 1:point_index + 3]
        else:
            #小数点补够2位
            tmp = str_amount[point_index + 1:str_amount_len] 
            tmp = tmp + (2 - xiaoshu_len) * '0'
        
        str_amount = "%s%s" %  (str_amount[:point_index], tmp)
        
        #补够14位
        str_amount = (14 - str_amount.__len__()) * '0' + str_amount 
        
    else:
        #整数补够12位， 小数补够2位
        
        str_amount = (12 - str_amount_len) * '0' + str_amount 
        str_amount = '%s00' % str_amount
        
    print ('amount:::', str_amount)
    return str_amount

def get_platform(cid):
#    tmp = ["COPGAM02"]
#    if tmp.__contains__(paid):
#        return 'gashcard'
#    return 'telecom'
    if cid == 'C002070000343':
        return 'haiwai'
    return 'taiwan'

def get_erp_id(paid):
    tmp = ["COPGAM02"]
    if tmp.__contains__(paid):
        return 'PINHALL'
    return 'J990002'

gash_cfg = {
    'taiwan' :  
        {
            'MID': 'M1000206',
            "BID":"",
            "CID": "C002060000342",
            "PWD1": "st6LJ64e0myks5waDNf4iWnqvWkylLo8",
            "PWD2": "NFYFwiD2K6A=",
            "PASSWORD": "rt65356ihn4wq",
        },
     
    "haiwai":
        {
             #商家代號
            "MID":"M1000207",
            #商家平台代码
            "BID":"",
            #商家服务代码
            "CID":"C002070000343",
            #商家密鑰I
            "PWD1":"nuRm42YsBYDxIVm03fyDPfzSpO0A/iEi",
            #交易秘钥II
            "PWD2":"sMcD4NBTuXs=",
            #商家密碼
            "PASSWORD": "683w4kqfjhaw3r",
        
         },
    
    #秘密基地
    'mimijidi_taiwan':
        {
            'MID': 'M1000206',
            "BID":"",
            "CID": "C001690000281",
            "PWD1": "XMiS+GdFoaS1u7U+dWPnpmyy8J1iA5Sd",
            "PWD2": "5JrKf1VBdLI=",
            "PASSWORD": "49929udfkop2",
        },
    'mimijidi_haiwai':
        {
            'MID': 'M1000170',
            "BID":"",
            "CID": "C001700000282",
            "PWD1": "y2KoYoen/Xi+L2rQ/8WZJPHwpxz7VZqq",
            "PWD2": "24IwG+1K0lY=",
            "PASSWORD": "err23rpktg42",
         },
    
    "type" : 
        {
            "BNK80801":{"name": "玉山WebATM  ", "type" : "TWD"},
            "BNK82201":{"name" : "中國信託", "type" : "TWD"},
            "TELCHT01":{ "name" : "中華電信市話", "type" : "TWD"},
            "TELCHT02":{"name" : "中華電信寬頻", "type" : "TWD"},
            "TELCHT03":{ "name" : "中華電信手机", "type" : "TWD"},
            "TELFET01":{ "name" : "遠傳電信", "type" : "TWD"},
            "TELTCC01":{ "name" : "台灣大哥大", "type" : "TWD"},
            "TELSON04":{ "name" : "亞太電信", "type" : "TWD"},
            "TELCHT05":{ "name" : "中華電信839一般型", "type" : "TWD"},
            "TELCHT06":{ "name" : "中華電信數據一般型(Hinet)", "type" : "TWD"},
            "TELCHT07":{ "name" : "中華電信市話一般型", "type" : "TWD"},
            "TELVIBO":{ "name" : "威寶電信", "type" : "TWD"},
            "COPGAM03":{ "name" : "帳號轉點", "type" : "AAA"},
            "COPGAM02":{ "name" : "卡密儲值", "type" : "PIN"}
        },

    "error_msg" : 
        {
            "0000" : "訊息處理成功",
            "1001" : "驗證碼錯誤",
            "1101" : "錯誤的訊息格式",
            "1102" : "錯誤的訊息格式",
            "1103" : "錯誤的訊息格式",
            "1104" : "不合法的交易",
            "1105" : "不合法的金額",
            "1106" : "不合法的 ERP",
            "1107" : "不合法的交易訊息代碼",
            "1108" : "不合法的月租交易參數",
            "1109" : "錯誤的訊息格式",
            "1110" : "不支援小數金額",
            "1201" : "服務不合法的商家代碼",
            "1202" : "不合法的商家代碼",
            "1203" : "不合法的平台代碼",
            "1204" : "不合法的服務代碼",
            "1205" : "不合法的網路位址",
            "1301" : "不合法或存在的付款機構",
            "1401" : "無法找到原始交易",
            "1402" : "交易內容與原始不一致",
            "1501" : "額度不足",
            "1502" : "超過金額上限",
            "1503" : "無效的交易時間",
            "1504" : "不允許使用的付款機構",
            "1601" : "未啟用的商家代碼",
            "1602" : "未啟用的平台代碼",
            "1603" : "未啟用的服務代碼",
            "1604" : "停用的商家代碼",
            "1605" : "停用的平台代碼",
            "1606" : "停用的服務代碼",
            "1607" : "停用的付款機構",
            "2001" : "交易重複",
            "2002" : "重複請款",
            "2003" : "月租僅第一期需要請款",
            "2004" : "無法解開交易參數",
            "3001" : "無法完成付款",
            "3002" : "付款機構不提供月租服務",
            "3003" : "付款機構只提供月租服務",
            "3004" : "付款待確認",
            "3010" : "超過使用者額度",
            "3011" : "號碼資格不符",
            "3012" : "使用者已申請此服務",
            "3098" : "GS系統繁忙，請稍後再試",
            "3099" : "GS系統錯誤",
            "3801" : "帳號剩餘點數不足",
            "3802" : "帳號未開啟異業轉點服務",
            "3803" : "帳號交易金額累計已達上限",
            "3901" : "儲值點數不一致",
            "3902" : "儲值密碼已鎖定",
            "3903" : "儲值密碼已使用",
            "3904" : "儲值密碼錯誤",
            "3905" : "儲值密碼無法使用",
            "9001" : "交易參數無法轉換",
            "9998" : "系統繁忙",
            "9999" : "系統發生異常"
        },

    "order_url"     : "https://api.eg.gashplus.com/CP_Module/order.aspx",
    "settle_url"    : "https://api.eg.gashplus.com/CP_Module/settle.asmx?wsdl",
    "checkorder_url": "https://api.eg.gashplus.com/CP_Module/checkorder.asmx?wsdl",


    "test_order_url": "https://stage-api.eg.gashplus.com/CP_Module/order.aspx",
    "test_settle_url": "https://stage-api.eg.gashplus.com/CP_Module/settle.asmx?wsdl",
    "test_checkorder_url": "https://stage-api.eg.gashplus.com/CP_Module/checkorder.asmx?wsdl"

}



       
