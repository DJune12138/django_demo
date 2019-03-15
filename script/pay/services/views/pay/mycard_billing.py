# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from services.models.pay import PayAction,PayChannel
#from services.views import md5,getConn
from services.http import http_post
from xml.dom import minidom
import urllib,re

def pay_mycard_billing(the_action,pay_channel={},service_url='service.fytxonline.com'):
    pay_url = 'http://%s/client/pay/mycard/%d'%(service_url,the_action.id)
    #{\"beginDate\":\"%s\",\"endDate\":\"%s\",\"title\":\"%s\",\"size\":[-1,-1],\"positioin\":[-1,-1],\"url\":\"%s\"}
    end_date = the_action.post_time.strftime('2112-%m-%d %H:%M:%S')
    pay_url = '{"beginDate":"%s","endDate":"%s","title":"MyCard儲值","size":[0.9,0.9],"position":[-1,-1],"url":"%s"}'%('2012-01-01 00:00:00',end_date,pay_url)
    return 1,pay_url

#选择金额及充值方式
def pay_mycard_billing_select(request,action_id=0):
    action_id = int(action_id)
    #显示充值列表
    return render_to_response('pay/pay_mycard_billing.html',locals())


#跳转到mycard页
def pay_mycard_billing_go(request,action_id=0):
    action_id = int(action_id)
    pay_amount = int(request.GET.get('pay_amount','10'))
    server_code = request.GET.get('server_code','')

    the_action = PayAction.objects.get(id=action_id)
    pay_channel = PayChannel.objects.using('read').get(id=the_action.pay_type)
    the_action.post_amount = pay_amount
    the_action.remark = server_code
    the_action.save(using='write')

    #http://test.b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/Auth/SPS0124691/0001/150
    #http://test.b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/ProductsQuery/FGPG
    #http://test.b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/PaymentsQuery/FGPG/FGPG50
    #http://test.b2b.mycard520.com.tw/MyCardBilling/?AuthCode=395EEA9448BCA7EFF32F6FA16337B8F2A995600E6E964F02
    auth_url = 'https://b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/Auth/%s/%s/%s'%(server_code,the_action.query_id,pay_amount)
    auth_result = http_post(auth_url)
    print(auth_result)
    reb = re.compile('<[^<]+>')
    auth_result = reb.sub('',auth_result)
    result_code,result_msg,order_id,auth_code = auth_result.split('|')

    if result_code=='1':
        the_action.order_id = order_id
        the_action.remark = auth_code
        the_action.save(using='write')
        pay_url = 'http://www.mycard520.com.tw/MyCardBilling/?AuthCode=%s'%auth_code
        return HttpResponseRedirect(pay_url)
    else:
        return render_to_response('pay/confirm_mycard_billing.html',locals())


def confirm_mycard_billing_get_link_id(request):
    return None

#接收充值结果
def confirm_mycard_billing(request,pay_channel={}):

    trade_no = request.POST.get('TradeSeq','')
    result_code = request.POST.get('ReturnMsgNo','')
    result_msg = request.POST.get('ReturnMsg','')
    auth_code = request.POST.get('AuthCode','')
    pay_actions = []
    try:
        if trade_no!='' and result_code == '1':
            pay_actions = PayAction.objects.filter(query_id=trade_no)

            if len(pay_actions) > 0:
                the_action = pay_actions[0]
                pay_channel = PayChannel.objects.using('read').get(id=the_action.pay_type)

                check_url = 'https://b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/TradeQuery?AuthCode=%s'%auth_code
                check_result = http_post(check_url) #查询充值结果
                reb = re.compile('<[^<]+>')
                check_result = reb.sub('',check_result)
                print(check_result)
                #查詢結果代碼|查詢結果|交易結果
                result_code,result_msg,check_code = check_result.split('|')

                if result_code == '1' and check_code=='3' :
                    CPMemberId = the_action.pay_user;
                    confirm_url = 'https://b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/PaymentConfirm?CPCustId=%s&AuthCode=%s'%(CPMemberId,auth_code)
                    confirm_result = http_post(confirm_url) #申请扣款
                    confirm_result = reb.sub('',confirm_result)
                    print(confirm_result)
                    #請款結果|請款訊息|智冠交易序號|連續扣款序號
                    result_data = confirm_result.split('|')
                    result_code = result_data[0]
                    result_msg = result_data[1] #order_id,loop_order_id 
                    if result_code == '1' and the_action.pay_status < 2:
                        the_action.pay_status = 2
                        the_action.pay_amount = the_action.post_amount
                        the_action.pay_gold = pay_channel.get_gold(the_action.pay_amount)
                        the_action.extra = pay_channel.get_extra(the_action.pay_gold) 
                        result_msg = '儲值成功!'
                else:
                    the_action.pay_status = -2

                the_action.remark = result_msg

                the_action.save(using='write')
        else:
            if len(pay_actions) > 0:
                the_action = pay_actions[0]
                the_action.pay_status = -2
                the_action.remark = result_msg
                the_action.save(using='write')

            try:
                result_msg = urllib.unquote(result_msg)
                result_msg = result_msg.decode('utf-8')
            except Exception,e:
                result_msg = '儲值失敗.'
                print('recv msg mycard billing has error',e)
    except Exception,e:
        result_msg = '發生未知錯誤!'
        print('confirm mycard billing has error',e)

    return render_to_response('pay/confirm_mycard_billing.html',locals())


def confirm_mycard_billing_fix(request):
    from services.alipay import getNodeTextByTagName
    xml_code = ''
#    '''
#    <BillingApplyRq><FatoryId>xxxxxx</FatoryId><TotalNum>2</TotalNum><Records>
#    <Record><ReturnMsgNo>1</ReturnMsgNo> <ReturnMsg></ReturnMsg> <TradeSeq>1210171504279954939D0B</TradeSeq>
#    </Record><Record>
#    <ReturnMsgNo>1</ReturnMsgNo> <ReturnMsg></ReturnMsg>
#    <TradeSeq>121017151329555432E415</TradeSeq>
#    </Record> </Records>
#    </BillingApplyRq>'''
    xml_data = request.POST.get('data',xml_code)
    print(xml_data)
    xml_dom = minidom.parseString(xml_data)
    orders = xml_dom.getElementsByTagName("Record")
    for order in orders:
        trade_no = getNodeTextByTagName(order,'TradeSeq')
        result_code = getNodeTextByTagName(order,'ReturnMsgNo')
        result_msg = getNodeTextByTagName(order,'ReturnMsg')

        print(trade_no,result_code,result_msg)

        if result_code == '1':
            pay_actions = PayAction.objects.filter(query_id=trade_no)

            if len(pay_actions) > 0:
                the_action = pay_actions[0]
                if the_action.pay_status == 0:
                    pay_channel = PayChannel.objects.using('read').get(id=the_action.pay_type)
                    check_url = 'https://b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/TradeQuery?AuthCode=%s'%the_action.remark
                    check_result = http_post(check_url) #查询充值结果
                    reb = re.compile('<[^<]+>')
                    check_result = reb.sub('',check_result)
                    #查詢結果代碼|查詢結果|交易結果
                    result_code,result_msg,check_code = check_result.split('|')

                    if result_code == '1' and check_code=='3' :
                        CPMemberId = the_action.pay_user;
                        confirm_url = 'https://b2b.mycard520.com.tw/MyCardBillingRESTSrv/MyCardBillingRESTSrv.svc/PaymentConfirm?CPCustId=%s&AuthCode=%s'%(CPMemberId,the_action.remark)
                        confirm_result = http_post(confirm_url) #申请扣款
                        confirm_result = reb.sub('',confirm_result)
                        #請款結果|請款訊息|智冠交易序號|連續扣款序號
                        result_data = confirm_result.split('|')
                        result_code = result_data[0]
                        result_msg = result_data[1] #order_id,loop_order_id 
                        if result_code == '1':
                            the_action.pay_status = 2
                            the_action.pay_amount = the_action.post_amount
                            the_action.pay_gold = pay_channel.get_gold(the_action.pay_amount)
                            the_action.extra = pay_channel.get_extra(the_action.pay_gold) 
                    else:
                        the_action.pay_status = -2

                    the_action.remark = result_msg

                    the_action.save(using='write')

    return render_to_response('pay/pay_post.html',{'pay_status':'SUCCESS'})
