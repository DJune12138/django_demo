# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.db.models import Q
from services.models.pay import PayAction
#from services.views import md5,getConn
from services.http import http_post
from services.views import hash256
import datetime,json,urllib

def pay_mycard(the_action,pay_channel = {},host_ip='service.fytxonline.com'):
    #from suds.client import Client
    result_code = 0
    result_msg = ''
    
    key1 = pay_channel.get_config_value('key1','mycardFGPG')
    key2 = pay_channel.get_config_value('key2','qwer2571')
#    if True:
    try:
        sign = '%s%s%s%s'%(key1,pay_channel.link_id,the_action.query_id,key2)
        sign = hash256(sign)
        query_data = 'facId=%s&facTradeSeq=%s&hash=%s'%(pay_channel.link_id,the_action.query_id,sign)
        query_url = 'http://test.b2b.mycard520.com.tw/MyCardInservices/Auth?%s'%query_data
        result = http_post(query_url)
        result = json.loads(result)
        print(query_url,result)
        auth_code = result.get('AuthCode',None)
        if result.get('ReturnMsgNo',0)==1 and auth_code != None:
            
            sign = '%s%s%s%s%s%s%s'%(key1,pay_channel.link_id,auth_code,the_action.pay_user,the_action.card_no,the_action.card_pwd,key2)
            sign = hash256(sign)

            query_data = 'facId=%s&authCode=%s&facMemId=%s&cardId=%s&cardPwd=%s&hash=%s'%(pay_channel.link_id,auth_code,the_action.pay_user,urllib.quote(the_action.card_no),urllib.quote(the_action.card_pwd),sign)
            query_url = 'http://test.b2b.mycard520.com.tw/MyCardInservices/Confirm?%s'%query_data
            
            result = http_post(query_url)
            print(query_url,result)
            result = json.loads(result)
            
            if result.get('ReturnMsgNo',0)==1:
                the_action.order_id = the_action.card_no
                the_action.pay_status=2
                the_action.pay_amount = float(result.get('CardPoint',0))
                the_action.pay_gold = pay_channel.get_gold(the_action.pay_amount)
                the_action.extra = pay_channel.get_extra(the_action.pay_gold)
                
                result_code = 1
            else:
                the_action.pay_status=-2
        else:
            the_action.pay_status=-2
            
        the_action.remark = result.get('ReturnMsg','')#.encode('utf-8')
        the_action.save(using='write')
        result_msg = the_action.remark
    except Exception,e:
        result_code = -1
        print('pay mycard has error',e)
        
    return (result_code,result_msg)

def confirm_mycard_get_link_id(request):
    return None

def confirm_mycard(request,pay_channel={}):
    return {}
    
def result_mycard(request,server_id=0,pay_type=''):
    card_no=request.GET.get('MyCardID','')
    if pay_type=='2,3':
        the_date = datetime.datetime.strptime('2012/10/25','%Y/%m/%d')
    else:
        the_date = datetime.datetime.now()
    sdate = request.GET.get('StartDate',the_date.strftime('%Y/%m/1'))
    edate = request.GET.get('EndDate',the_date.strftime('%Y/%m/%d'))

    server_id = int(server_id)
    list_record = []
    total_record = 0
    query = Q(pay_status__gte=2)
    if server_id > 0 :
        query = Q(server_id=server_id)
    
    if card_no!='':
        query = query & Q(card_no=card_no) 
        if pay_type=='2,3':
            query = query & Q(post_time__lte=datetime.datetime.strptime('2012/10/26','%Y/%m/%d'))
    else:
        if sdate!='' or edate!='':
            try:
                sdate = datetime.datetime.strptime(sdate,'%Y/%m/%d')
                edate = datetime.datetime.strptime(edate,'%Y/%m/%d') + datetime.timedelta(days=1)
                if pay_type=='2,3':
                    the_date = datetime.datetime.strptime('2012/10/25','%Y/%m/%d')
                    if sdate > the_date:
                        sdate = the_date
                    if edate > the_date:
                        edate = the_date + datetime.timedelta(days=1)
                query = query & Q(post_time__gte=sdate,post_time__lte=edate)
            except:
                pass
        
    if pay_type!='':
        query = query & Q(pay_type__in=pay_type.split(','))

    try:
        total_record = PayAction.objects.using('read').filter(query).count()
        if total_record > 0:
            list_record = PayAction.objects.using('read').filter(query)
    except Exception,e:
        print('result mycard has error',e)
        
    return render_to_response('pay/pay_result_mycard.html',{'list_record':list_record})



