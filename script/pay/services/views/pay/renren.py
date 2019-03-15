# -*- coding: utf-8 -*-
from services.views import md5
from services.models import Player
from services.http import http_post
import time, urllib, datetime, json 

def confirm_renren_get_link_id(request):
    return ''
    
def global_param(sid, currenttime, now_date):
    areaid = 1
    serverid = 1000 + sid
    #domain = 's%s.fytx.renren.com' % sid
    domain = 's1.fytx.renren.com'
    platformid = 'renren.com'
    gamecode = 'fytx'
    
    timestamp = int(time.mktime(now_date.timetuple()))
    
    
    pdata = {}
    pdata["areaid"] = areaid
    pdata["serverid"] = serverid
    pdata["domain"] = domain
    pdata["gamecode"] = gamecode
    pdata["platformid"] = platformid
    pdata["currenttime"] = currenttime
    pdata["timestamp"] = timestamp
    return pdata
    
def confirm_renren(request, pay_channel={}):
    
    result_list = []
    
    now_date = datetime.datetime.now()
    
    #查询用户订单信息
    request_url = 'http://local.rrgdev.org/u.queryrecharge.php'
    
    #20120912212950
    currenttime = now_date.strftime('%Y%m%d%H%M%S')
    
    app_key = pay_channel.get_config_value('app_id', '4F6944A57CD2879A42FCB20F6A1C1B5C')
    
    #私有参数
    ip = request.META['REMOTE_ADDR']
    player_id = int(request.GET.get('playerid', 0))
    server_id = int(request.GET.get('serverid', 0))
    
    err_msg = ''
    userid = None
    try:
        userid = getPlayer(server_id, player_id)
    except:
        err_msg = '用户无效'
        print 'error:::player_id not find'
    
    if None != userid:
        
        pdata = global_param(server_id, currenttime, now_date)
        
        sign = ''
        sign = sign + 'areaid=%s' % pdata['areaid']
        sign = sign + 'currenttime=%s'% pdata['currenttime']
        sign = sign + 'domain=%s' % pdata['domain']
        sign = sign + 'gamecode=%s' % pdata['gamecode']
        sign = sign + 'ip=%s' % ip
        #sign = sign + 'method=%s' % 'u.queryrecharge'
        sign = sign + 'platformid=%s' % pdata['platformid']
        sign = sign + 'serverid=%s' % pdata['serverid']
        sign = sign + 'timestamp=%s' % pdata['timestamp']
        sign = sign + 'userid=%s' % userid 
        sign = sign + app_key
        
        sign = md5(sign)
        
        pdata['ip'] = ip
        pdata['userid'] = userid
        pdata['sig'] = sign
        
        post_data = urllib.urlencode(pdata)
        try:
            #print 'requset_url:::', request_url
            #print 'post_data:::', post_data
            result_data = http_post(request_url, post_data)
            #print 'result_data:::', result_data
#            file_object = open('/data/renren_response_file.txt', 'w')
#            file_object.write(result_data)
#            file_object.close()
        except Exception, ex:
            print 'query user order error'
            print ex
            err_msg = '网络出问题'
            
        order_list = get_order_list(result_data)
         
        
        if '' == err_msg:
            if type(order_list) == int:
                err_msg = error_map.get(order_list)
            else:
#                file_object = open('/data/renren_order.log', 'w')
#                file_object.write(result_data)
#                file_object.close()
                
                #pids = ','.join([item.get('id') for item in order_list])
                
                pids = []
                for item in order_list:
                    pids.append(item.get('id'))
                    order_id = item.get('order_id')
                    currency = item.get('currency', '')
                    amount = 0
                    remark = ''
                    result_msg = '充值失败,请重新请款'
                    result_list.append({'server_id':server_id,'currency':currency,'player_id':player_id,'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg})
                try:
                    pids = ','.join(pids)
                    
                    try:
                        finish_order_list = do_exchangerecharge(userid, server_id, player_id, ip, pids, currenttime, now_date, app_key)
                    except Exception, ex:
                        print 'exchangerecharge error:'
                        print ex
                        err_msg = '网络出问题'
                    
                    if '' == err_msg:
                        if type(finish_order_list) == int:
                            err_msg = error_map.get(finish_order_list)
                        else:
                            
                            result_msg = 'success'
                            result_list = []
                            for item in finish_order_list:
                                order_id = item.get('order_id')
                                amount = float(item.get('amount', 0))
                                f_currency = item.get('currency', '')
                                amount = filter_amount_by_currency(f_currency, amount, pay_channel)
                                remark = ''
                                result_list.append({'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg})
                except Exception, ex:
                    print 'internal error'
                    print ex
    
    return result_list


def filter_amount_by_currency(currency, amount, pay_channel):
    
    currency = currency.strip().upper()
    if 'CNY' != currency and 'RRDOU' != currency:
        amount = 0
        
    r = float(pay_channel.get_config_value(currency, 1))
    
    amount = amount * r
    
    return amount
    

#pids_str : 1003,1005
def do_exchangerecharge(userid, server_id, player_id, ip, pids_str, currenttime, now_date, app_key):
    
    request_url = 'http://local.rrgdev.org/u.exchangerecharge.php'
    
    print 'exchangerechange begin:::'
    
    pdata = global_param(server_id, currenttime, now_date)
    
    sign = ''
    sign = sign + 'areaid=%s' % pdata['areaid']
    sign = sign + 'currenttime=%s'% pdata['currenttime']
    sign = sign + 'domain=%s' % pdata['domain']
    sign = sign + 'gamecode=%s' % pdata['gamecode']
    sign = sign + 'ip=%s' % ip
    sign = sign + 'pids=%s' % pids_str
    sign = sign + 'platformid=%s' % pdata['platformid']
    sign = sign + 'serverid=%s' % pdata['serverid']
    sign = sign + 'timestamp=%s' % pdata['timestamp']
    sign = sign + 'userid=%s' % userid 
    sign = sign + app_key
    
    sign = md5(sign)
    
    #私有参数
    pdata['userid'] = userid
    pdata['pids'] = pids_str
    pdata['ip'] = ip
    pdata['sig'] = sign
    
    post_data = urllib.urlencode(pdata)
    
    result_data = http_post(request_url, post_data)
    
#    file_object = open('/data/renren_exchangerecharge.log', 'w')
#    file_object.write(result_data)
#    file_object.close()
#    print 'exchangerechange end:::'
    return get_order_list(result_data)
    

def get_order_list(data):
    data = json.loads(data)
    
    state = data.get('error_code', None)
    if None != state:
        return int(state)
    
    order_list = data.get('recharge')
    
    return order_list


error_map = {
        1:"签名验证失败",
        2 :"时间戳过期",
        3 :"有参数为空或格式不正确",
        4 :"可能为以下其中之一 :活动码已发放完,充值接口被关闭, 玩家充值信息查询不成功,玩家充值信息兑换不成功（已兑换过） ",
        5 :"用户已经被锁定",
        6 :"密保未通过",
        7 :"cookie验证未通过",
        8 :"token验证未通过",
        11:"帐号未激活",
        20 :"用户登录验证失败",
        21 :"注册到人人失败",
        31 :"接口功能禁用，请申请权限",
        999 :"系统异常，操作不成功 "
}
    
def getPlayer(server_id,player_id):
    from services.views.pay import getConn
    conn = getConn(server_id)
    link_key = None
    try:
        query_sql = "select link_key from player_%d where player_id='%s'"%(server_id,player_id)
        print(query_sql)
        cursor = conn.cursor()
        cursor.execute(query_sql)
        pay_user_record = cursor.fetchone()

        if pay_user_record!=None:
            link_key = int(pay_user_record[0]) 
    except Exception,e:
        print('get player id has error',e)
#    finally:
#        conn.close()
    return link_key