# -*- coding: utf-8 -*-
#已测  POST http://127.0.0.1:8002/service/confirm/yunyoyo?server_seq_num=123231&trade_no=120507224627804959449D&amount=10&user_id=14680065&ext_info=14&timestamp=123123321&remark=hello&verstring=31e149ee6cf70d69b9a33e012ce299e0
from services.views import md5
import base64

def confirm_yunyoyo_get_link_id(request):
    return ''


def confirm_yunyoyo(request,pay_channel={}):
    cpid = pay_channel.get_config_value('cpid',230)
    game_seq_num = pay_channel.get_config_value('game_seq_num',1)
    notice_key = pay_channel.get_config_value('notice_key','TFJkSTYyTks=')
    #secret_key = pay_channel.get_config_value('secret_key','NnVxdnlDdzA=')
    
    server_seq_num = request.POST.get('server_seq_num','')
    trade_no = request.POST.get('trade_no','')
    amount = request.POST.get('amount','')
    user_id = request.POST.get('user_id','')
    ext_info = request.POST.get('ext_info','')
    timestamp = request.POST.get('timestamp','')
    remark = request.POST.get('remark','')
    verstring = request.POST.get('verstring','')
    
    sign_str = u'trade_no=%s&cpid=%s&game_seq_num=%s&server_seq_num=%s&amount=%s&user_id=%s&ext_info=%s&timestamp=%s&SecretKey=%s'%(trade_no,cpid,game_seq_num,server_seq_num,amount,user_id,ext_info,timestamp,base64.decodestring(notice_key))
    #print(sign_str)
    sign_str = md5(sign_str)
    print(sign_str,verstring)
    pay_status = 'error order'
    user_type = 4
    server_id = 0
    pay_amount = 0
    if sign_str == verstring:
        server_id = int(ext_info)
        pay_amount = float(amount)
        pay_status = 'success'
    else:
        pay_status = 'error sign'
        
    return {'server_id':server_id,'user_type':user_type,'open_id':user_id,'order_id':trade_no,'amount':pay_amount,'remark':remark,'result_msg':pay_status}
