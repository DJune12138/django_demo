# -*- coding: utf-8 -*-
from Crypto.Cipher import DES
from services.views import md5
 

def confirm_uuc_get_link_id(request):
    return ''

def confirm_uuc(request, pay_channel={}):
    app_id = pay_channel.get_config_value('app_id', '5yMoB6rwJo0Vw9NEVHx7Jc56vCbEabWa')
    app_key = pay_channel.get_config_value('app_key', '6FkWWx')
    
    callback_rsp = request.POST.get('callback_rsp', '')
    #callback_rsp = '''a6720456d80ab9d0831563be67fe429fb5259930cc77e1d79328cbad29e36d34ad05842bf93699b0d427c2f514778548a9665580044bb8eefa8b7973f0960cc5aab6a2945fad6591e2f494d55a21016c87644823235ce01ddb91a1f5fac7839b1c8f7cd6ded14fd82f76500a47c42481196b13cefb8eb3769faafde03463b432617210c273db8f4cd205e8fb86e517a3aa4cc58828b6114f80763f21adebcc41ace52706f9d1fb232f219b5f610e0907d904d307124347cc61594b7a265a212639c7a64fc10bab98bb136d10ecb932875f80a9d67caac325'''
    
    error = 0
    remark = ''
    result_msg = ''
    pay_amount = 0 
    o_id = ''
    server_id = 0
    player_id = 0
    try:
            
        
        data_str = callback_rsp.lower()
        data_str = hex2bin(data_str)
        #data_str = data_str.decode('utf-8')
        key = '2SoXIhFB'
        des = DES.new(key, DES.MODE_CBC,key)
        data = des.decrypt(data_str)
        pad = ord(data[-1])
        data = data[ : -pad]
        
    except Exception, ex:
        print callback_rsp
        error = 1
        remark = 'callback_rsp error'
        print 'callback_rsp error ', ex
    
    if not error:
        param = param_to_dic(data.split("&"))
        
        
        signMsg = param.get('signMsg', '')
        
        
        txn_seq = param.get('txn_seq', '')#支付流水号
        order_id = param.get('order_id', '')#CP 订单号
        rsp_code = param.get('rsp_code', '')#交易结果标识，成 功 000000
        txn_time = param.get('txn_time', '')#
        actual_txn_amt = param.get('actual_txn_amt', '') #交易金额 ( 分 )
        time_stamp = param.get('time_stamp', '')
        
        server_sign = "app_key=" + app_id
        server_sign += "&txn_seq=" + txn_seq
        server_sign += "&order_id=" + order_id
        server_sign += "&rsp_code=" + rsp_code
        server_sign += "&txn_time=" + txn_time
        server_sign += "&actual_txn_amt=" + actual_txn_amt
        server_sign += "&time_stamp=" + time_stamp
        server_sign += "&key=" + app_key
        server_sign = md5(server_sign)
        server_sign = server_sign.upper()
        
        print app_id
        print txn_seq
        print order_id
        print rsp_code
        print txn_time
        print actual_txn_amt
        print time_stamp
        print app_key
        
        print (signMsg, server_sign)
        
        try:
            if signMsg == server_sign:
                result_msg = '1'
                if str(rsp_code) == '000000':
                    pay_amount = float(actual_txn_amt) / 100
                    server_id = int(order_id.split('_')[0])
                    player_id = int(order_id.split('_')[1])
                    o_id = txn_seq
                else:
                    remark = code_map.get(str(rsp_code), '未知错误')
            else:
                remark = '签名错误'
        except Exception, ex:
            print 'comfirm uuc error ', ex
    
    return {"amount":pay_amount, "order_id":o_id, "server_id":server_id, "player_id":player_id, "remark":remark, "result_msg":result_msg}

code_map = {
            '200001': 'appkey 为空',
            '200002': 'appkey 不计费',
            '200003': '金额为 0 不计费',
            '200004': '计费类型为空或者支付类型为空',
            '200005': '密文为空',
            '200006': '应用找不到该密钥 ( 确定 secretKey 正确 )',
            '200007': '验证失败',
            '500011': '银行卡信息错误 （请检查银行卡号和密码',
            '500012': '卡信息有误 （请检查卡号和密码正确）',
            '500013': '卡密码有误 （请确保卡密码正确）',
            '500014': '卡信息或者密码有误',
            '500003': '交易时间为空 .',
            '500019': '交易时间有误',
            '500020': '商户为空或者大于 500 位',
            '500021': '商户 URL 有误 .',
            '500022': '订单号为空 .',
            '500023': '订单号长度有误',
            '500024': '订单号不为数字',
            '500025': 'ip 有误',
            '500026': '商品名称为空或者长度超过 30',
            '500027': '商品数量有误',
            '500028': '商品编号有误',
            '555556': '发送失败',
            '777777': '后台交易失败',
            '88081': '网络错误',
            '88086': 'Service 错误 ( 支付服务启动或者运行失败 )',
            '999999': '内部错误  '
}
    
def param_to_dic(list_param):
    result = {}
    for item in list_param:
        tmp = item.split('=')
        if tmp.__len__() != 2:
            continue
        name = tmp[0].strip()
        value = tmp[1].strip()
        result[name] = value
    
    return result



def hex2bin(data):
    result = [];
    index = 0
    data_length = data.__len__()
    while True:
        if index >= data_length:
            break
        
        result.append(chr(int(data[index:index+2], 16)))
        index += 2
    result = ''.join(result)
    return result

