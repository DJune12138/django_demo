# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from services.models.pay import PayAction,PayChannel
import json,datetime

'''
所有状态,正值为成功,负值为失败
0 客户已提交
1 已转发到支付接口 
2 接收到支付接口的确认
3 转发中...
4 接收到游戏服务器确认
'''

def get_gold(request):
    pay_status=0
    server_id = int(request.POST.get('serverid','1'))
    account = int(request.POST.get('userid','0'))
    if account==0:
        return render_to_response('pay/pay_post.html',{'pay_status':pay_status})
    
    
    pay_channel_list = PayChannel.objects.using('read').filter(func_name='getgold',status=0)
    if len(pay_channel_list)>0:
        pay_channel = pay_channel_list[0]
    else:
        pay_status = -2
        return render_to_response('pay/pay_post.html',locals())
    
    time_interval = pay_channel.get_config_value('time_interval',30)

    #领取金币服务,先判断今天有没有领取
#    date = datetime.datetime.now().date()
#    if datetime.datetime.now().hour<5:
#        date -= datetime.timedelta(days=1)
#    sdate = date + datetime.timedelta(hours=5)
    edate = datetime.datetime.now()
    sdate = edate - datetime.timedelta(minutes=time_interval)
    list_pay = PayAction.objects.using('write').filter(server_id=server_id,pay_type=pay_channel.id,pay_user=account,post_time__gte=sdate,post_time__lt=edate)
    if len(list_pay)>0:
        pay_status = -1
        return render_to_response('pay/pay_post.html',{'pay_status':pay_status})
    
    the_action = PayAction()
    the_action.card_no = ''
    the_action.card_pwd = ''
    the_action.pay_user = account
    the_action.server_id = server_id
    the_action.post_amount = 1.00
    the_action.pay_amount = 1.00
    the_action.pay_gold = pay_channel.get_gold(the_action.post_amount)
    the_action.extra = pay_channel.get_extra(the_action.pay_gold)
    the_action.channel_key = request.POST.get('from','')
    the_action.pay_type = pay_channel.id
    the_action.pay_ip = request.META.get('REMOTE_ADDR','') 
    
    the_action.order_id = 0
    try:
        the_action.pay_status = 2
        the_action.query_id = the_action.get_query_id()
        the_action.safe_save()
        #the_action.id = 10
        pay_status = the_action.query_id

    except Exception,e:
        print('save error',e)
        pay_status=0
    
#    send_to_server(str(pay_status))
    
    return render_to_response('pay/pay_post.html',{'pay_status':pay_status})

def check_get_gold(request):
    pay_status=0
    server_id = int(request.POST.get('serverid','1'))
    account = int(request.POST.get('userid','0'))
    time_interval = 30
    
    try:
        pay_channel_list = PayChannel.objects.using('read').filter(func_name='getgold')
        if len(pay_channel_list)>0:
            pay_channel = pay_channel_list[0]
        else:
            pay_status = -2
            return render_to_response('pay_post.html',locals())
    
        if pay_channel.pay_config!=None and pay_channel.pay_config!='':
            pay_config = json.loads(pay_channel.pay_config)
            print(pay_config)
            time_interval = pay_config.get('time_interval',30)

            edate = datetime.datetime.now()
            sdate = edate - datetime.timedelta(minutes=time_interval)
            list_pay = PayAction.objects.using('write').filter(server_id=server_id,pay_type=pay_channel.id,pay_user=account,post_time__gte=sdate,post_time__lt=edate)
            if len(list_pay)==0:
                pay_status = 1
    except Exception,e:
        print('get gold has error',e)  
        pay_status = -1
    return render_to_response('pay/pay_post.html',{'pay_status':pay_status})