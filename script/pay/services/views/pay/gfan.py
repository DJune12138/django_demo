# -*- coding: utf-8 -*-
from services.views import md5
from xml.dom import minidom

def confirm_gfan_get_link_id(request):
    return ''


def confirm_gfan(request, pay_channel = {}):
    
    #print(request.GET,request.raw_post_data)
    result_msg = '<response><ErrorCode>0</ErrorCode><ErrorDesc>error order info</ErrorDesc></response>'
    uid = pay_channel.get_config_value('uid', '7874351')#uid是开发者在机锋注册时获得的用户ID，登陆开发者后台可看到。
    request_xml = request.raw_post_data
    
    result_data = parse_notify_data(request_xml)
    
    server_sign =  md5('%s%s' % (uid, result_data.get('time')))
    sign = result_data.get('sign')
    print (sign, server_sign)
 
    query_id = ''
    pay_amount = 0
    remark = ''
    if sign == server_sign:
        query_id = result_data.get('order_id')
        pay_amount = float(result_data.get('cost'))
        result_msg = '<response><ErrorCode>1</ErrorCode><ErrorDesc></ErrorDesc></response>'
    else:
        remark = 'error sign'
          
    return {'query_id':query_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}

 
def parse_notify_data(data):
    '''
    通过minixml解析data
    '''
    result = {}
    dom = minidom.parseString(data)
    order = dom.getElementsByTagName("order")
    result['order_id'] = getNodeTextByTagName(order, "order_id")
    result['cost'] = getNodeTextByTagName(order, 'cost')
    result['appkey'] = getNodeTextByTagName(order, 'appkey')
    result['sign'] = getNodeTextByTagName(order, 'sign')
    result['time'] = getNodeTextByTagName(order, 'time')
    result['create_time'] = getNodeTextByTagName(order, 'create_time')
     
    return result
    

def getNodesText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

def getNodeTextByTagName(node, tagName):
    selected = node.getElementsByTagName(tagName)
    if selected:
        return getNodesText(selected[0].childNodes)
    else:
        return ""


#
#def confirm_gfan(request):
#    channel_id = 86
#    print(request.GET,request.raw_post_data)
#    result_msg = '<response><ErrorCode>0</ErrorCode><ErrorDesc>error order info</ErrorDesc></response>'
#    sign = request.GET.get('sign','')
#    time = request.GET.get('time','')
#    sign_str = '%d%s'%(channel_id,time)
#    sign_str = md5(sign_str)
#    if sign == sign_str:
#        try:
#            xml_dom = minidom.parseString(request.raw_post_data)
#            xml_root = xml_dom.documentElement
#            for childNode in xml_root.childNodes:
#                query_id = childNode.getElementsByTagName('order_id')[0].toxml().replace('<order_id>','').replace('</order_id>','')
#                pay_amount = float(childNode.getElementsByTagName('cost')[0].toxml().replace('<cost>','').replace('</cost>',''))
#                
#                pay_action = PayAction.objects.using('write').get(query_id=query_id)
#                pay_channel = PayChannel.objects.using('read').get(id=pay_action.pay_type)
#                pay_action.pay_status = 2
#                pay_action.pay_amount = pay_amount
#                pay_action.pay_gold = pay_action.pay_amount * pay_channel.exchange_rate
#                
#                pay_action.last_time = datetime.datetime.now()
#                pay_action.pay_ip = request.META.get('REMOTE_ADDR','')
#                pay_action.save(using='write')
#                
#            result_msg = '<response><ErrorCode>1</ErrorCode><ErrorDesc></ErrorDesc></response>'
#        except Exception,e:
#            print('pay confirm gfan has error',e)
#    return render_to_response('pay/pay_post.html',{'pay_status':result_msg})   