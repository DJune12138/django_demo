# -*- coding: utf-8 -*-
from services.views import md5

def confirm_qitian91dianjin_get_link_id(request):
    return ''

def confirm_qitian91dianjin(request,pay_channel={}):
    
    g = lambda x,y:request.POST.get(x,request.GET.get(x,y))
    app_key = pay_channel.get_config_value('app_key','aa863dded89fd5f26dc5e7fc4e08cfb8')
    
    App_Id = g('App_Id', '')
    Uin = g('Uin', '')
    Urecharge_Id = g('Urecharge_Id', '')
    Extra = g('Extra', '')
    Recharge_Money = g('Recharge_Money', '')
    Recharge_Gold_Count = g('Recharge_Gold_Count', '')
    Pay_Status = g('Pay_Status', '')
    Create_Time = g('Create_Time', '')
    Sign = g('Sign', '')
    
    sign_str = 'App_Id=%s&Create_Time=%s&Extra=%s&Pay_Status=%s&Recharge_Gold_Count=%s&Recharge_Money=%s&Uin=%s&Urecharge_Id=%s%s'\
    % (App_Id, Create_Time, Extra, Pay_Status, Recharge_Gold_Count, Recharge_Money, Uin, Urecharge_Id, app_key)
    print 'sign_str%s'% sign_str
    
    remark = ''
    result_msg = ''
    order_id = ''
    server_id = 0
    player_id = 0
    amount = 0
    
    if Sign == md5(sign_str):
        if Pay_Status == '1':
            try:                
                server_id = int(Urecharge_Id.split('_')[0])
                player_id = int(Urecharge_Id.split('_')[1])
                amount = int(Recharge_Money.split('.')[0])
                order_id = Urecharge_Id
            except Exception, ex:
                print 'Urecharge_Id error'
         
        result_msg = 'Success'
    else:
        result_msg = 'sign error'
    
    return {'server_id':server_id,'player_id':player_id, 'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg}

