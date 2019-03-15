#! /usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.db import connection, connections
from django.db.models import Q
from models.pay import PayAction, PayChannel
from models.server import Server
from models.channel import Channel
from django.http import HttpResponseRedirect, HttpResponse
from views.base import OperateLogManager, get_server_list, getConn
from cache import center_cache
import json, MySQLdb, datetime
from cache.center_cache import get_channel_list 
from views.widgets import get_agent_channels_dict,get_group_servers_dict,get_group_server_list
from util import trace_msg


def pay_result_list(request,table_name=''):
    page_size = 50
    page_num = int(request.GET.get('page_num', '1'))
    
    key = request.GET.get('key', '') 
    
    pay_type = int(request.GET.get('pay_type', '0'))
    server_id = int(request.GET.get('server_id', '') or 0)
    
    key_type = int(request.GET.get('key_type', '0'))
    
   
    
    #**支付通道列表 ***
    payChannel_record = {}
    payChannel_list = PayChannel.objects.all()
    
    for payChannel in payChannel_list:
        payChannel_record[payChannel.id] = payChannel.name
    #***支付通道列表 END
    
    
    list_record = []
    pay_status = int(request.GET.get('status', '0'))
    
    list_server = request.admin.get_resource('server').all()
    
    server_ids = [s.id for s in list_server]

    query = Q()
    
    if server_id > 0 and server_id in server_ids:
        server_ids = [server_id]
    query = query & Q(server_id__in=server_ids)
        
    if pay_type > 0:
        query = query & Q(pay_type = pay_type)
        
    if pay_status != 0 and pay_status != -4:
        query = query & Q(pay_status=pay_status)
        
    if pay_status == -4:
        query = query & Q(pay_status__lt=2)
    
    if key != '':
        if key_type == 0:
            query = query & Q(query_id=key)
        elif key_type == 1:
            query = query & Q(pay_user=key)
        elif key_type == 2:
            query = query & Q(order_id=key)
        elif key_type == 3:
            query = query & Q(card_no=key)
        elif key_type == 4:
            query = query & Q(remark__contains = key)
    if 'old' == table_name:
        PayAction._meta.db_table = 'pay_action_old'
    else:
        PayAction._meta.db_table = 'pay_action'
    
    if not request.admin.is_root:
        channel_ids = request.admin.get_resource('channel').all().values_list('id',flat=True)
        query = query & Q(channel_id__in=channel_ids)
        
    
    group_id = int(request.GET.get('group_id',0))   
        
    total_record = PayAction.objects.filter(query).count()
    
        
    
    if total_record > 0:
        list_record = PayAction.objects.filter(query)[(page_num - 1) * page_size:page_num * page_size]
        itemServerList = {}
        for item in list_server:
            itemServerList[item.id] = item.name
        
        for item in list_record:
            item.playerName = ''
            item.pay_type_name = payChannel_record.get(item.pay_type,'')
            item.server_name = itemServerList.get(item.server_id, '--')
    parg = {}

    group_servers_dict = get_group_servers_dict(request)
    status = pay_status

    return render_to_response('pay/pay_list.html', locals())

from views.game.pay import game_pay
#人工补单
def pay_fix(request):
    pay_id = int(request.POST.get('pay_id', '0'))
    order_id = request.POST.get('order_id', '0')
    pay_amount = float(request.POST.get('pay_amount', '0'))
       
    if pay_id == 0 or order_id == 0 or pay_amount ==0:
        return HttpResponse(-1)
    
    rate = 10
    pay_entity = PayAction.objects.using('write').get(id=pay_id)
    

    if PayChannel.objects.using('read').filter(id=pay_entity.pay_type).count() != 0:
        pay_channel_entity = PayChannel.objects.using('read').get(id=pay_entity.pay_type)
        rate = pay_channel_entity.exchange_rate 
        
    #***********写日志 *********
    the_user_id = request.admin.id
    OperateLogManager.save_operate_log(the_user_id, u'人工补单ID:%d 渠道订单%s' % (pay_id, order_id), '/pay/retroactively', OperateLogManager.get_request_ipAddress(request))
    
    #***********写日志  END **********    
     
    pay_gold = pay_amount * rate
    pay_entity.post_time = datetime.datetime.now()
    pay_entity.order_id = order_id
    pay_entity.pay_amount = pay_amount
    pay_entity.pay_gold = pay_gold
    pay_entity.pay_status = 2
    pay_entity.remark = u'%s 人工补单.' % request.admin.alias
    if pay_entity.query_id=='':
        pay_entity.query_id = pay_entity.get_query_id()
    pay_entity.save(using='write') 
    entity = {}
    entity['id'] = pay_entity.id
    entity['order_id'] = pay_entity.order_id
    entity['pay_amount'] = pay_entity.pay_amount
    entity['pay_gold'] = pay_entity.pay_gold
    entity['pay_status'] = pay_entity.pay_status
    entity['remark'] = pay_entity.remark
    game_pay(pay_entity)
    
    return HttpResponse(json.dumps(entity))
    
def pay_reissue(request):
    '''重发订单
    '''
    err_msgs = []
    pay_ids = request.REQUEST.getlist('pay_id')
    try:
        if pay_ids:
            pay_actions = PayAction.objects.using('write').filter(id__in=pay_ids)
            for p in pay_actions:
                err_msg = game_pay(p)
                err_msg = '成功!' if not err_msg  else err_msg
                err_msgs.append('%s:%s' % (p.order_id,err_msg))
    except:
        err_msg = trace_msg()
        err_msgs.append(err_msg)
        
    return HttpResponse('<br>'.join(err_msgs))


def pay_check(request, pay_id=0):
    pay_id = int(pay_id or int(request.REQUEST.get('pay_id','') or 0 ))
    list_record = []
    err_msg = ''
    try:
        pass
        pay_action = PayAction.objects.using('read').get(id=pay_id)
        if abs(pay_action.pay_status) == 3:
            server_id = pay_action.server_id
            #the_server = Server.objects.using('read').get(id=pay_action.server_id)
            #the_db_config = json.loads(the_server.log_db_config)
            #conn = Server.get_conn(pay_action.server_id)
            #conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], passwd=the_db_config['password'], port=the_db_config.get('port',3306), db=the_db_config['db'])
#            conn = Server.get_conn(pay_action.server_id)
#            conn.autocommit(True)
#            query_sql = 'select log_time,log_type,log_previous,log_now from log_gold where log_user=%d and log_type=3108 order by id desc limit 1000' % pay_action.pay_user
#            cursor = conn.cursor()
#            cursor.execute(query_sql)
#            list_record = cursor.fetchall()
#           cursor.close()
    except Exception, e:
        err_msg = '发生未知错误%s' % e
    
    parg = {}
    parg["pay_id"] = pay_id
    parg["list_record"] = list_record
    parg["err_msg"] = err_msg
    
    return render_to_response('pay/pay_check.html', locals())

def pay_confirm(request, pay_id=0):
    '''订单确认,不补发
    '''
    pay_id = int(pay_id or int(request.REQUEST.get('pay_id','') or 0 ))
    err_msg = ''
    try:
        pay_action = PayAction.objects.using('write').get(id=pay_id)
        pay_action.pay_status = 4
        if not pay_action.last_time:
            pay_action.last_time = pay_action.post_time
        pay_action.save(using='write') 
    except:
        err_msg = ''
    
    parg = {}
    parg["err_msg"] = err_msg
    
    return render_to_response('pay/pay_confirm.html', parg)
 
def pay_user_rank(request):
    server_id = int(request.GET.get('server_id', '0'))
    page_num = int(request.GET.get('page_num', '1'))
    sdate = request.GET.get('sdate', '')
    edate = request.GET.get('edate', '')
    err_msg = ''
    page_size = 30
    
    list_server = get_server_list()
    
    if server_id < 1 and len(list_server) > 0:
        server_id = list_server[0].id
    
    query_date = ''
    try:
        if sdate != '':
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S') #%H:%M:%S
            query_date = ' a.last_time>=\'%s\'' % sdate
        if edate != '':
            if query_date != '':
                query_date += ' and '
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            query_date += ' a.last_time<\'%s\'' % edate
    except Exception, e:
        print('menu error:', e)
        sdate = ''
        edate = ''
        
    pager_str = 'limit %s,%s' % ((page_num - 1) * page_size, page_size)
    server_id = center_cache.get_server_config(server_id, 'master_server_id', server_id)
    if server_id > 0:    
        try:
            the_server = Server.objects.get(id=server_id)
            the_db_config = json.loads(the_server.log_db_config)
            conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], passwd=the_db_config['password'], port=the_db_config.get('port',3306), db=the_db_config['db'], charset='utf8')
            conn.autocommit(True)
        except:
            err_msg = '数据库链接出错!'

    query_sql = ' SELECT a.pay_user,SUM(a.pay_gold) AS total_gold\
 FROM pay_action a,channel ch\
 WHERE a.channel_id=ch.id AND pay_status=4 and {{qserver}} and {{qdate}}\
 GROUP BY a.pay_user order by total_gold desc'
  
    query_sql = query_sql.replace('\r\n\t', ' ').replace('\r\n', ' ')
    if query_date != '' :
        query_sql = query_sql.replace("{{qdate}}", query_date)
    else :
        query_sql = query_sql.replace('and {{qdate}}', '').replace('where {{qdate}}', '')
     
    query_sql = query_sql.replace("{{qserver}}", " server_id=%s" % str(server_id))
    
    query_count_sql = 'select count(1) from (%s) newTable' % query_sql
    
    cursor = connections['read'].cursor()
    
    cursor.execute(query_count_sql)
    total_record = int(cursor.fetchone()[0])
    
    query_sql = query_sql + ' ' + pager_str
    
    cursor.execute(query_sql)     
    pay_list_temp = cursor.fetchall()
    #cursor.close()
    
    pay_list = []
    
    cursor = conn.cursor()
    query_role_sql = "SELECT lcr.log_user,lcr.f1 FROM log_create_role lcr WHERE lcr.log_result=%s limit 0,1"
    for payItem in pay_list_temp:
        query_role_sql2 = query_role_sql % payItem[0]
        cursor.execute(query_role_sql2)
        roleObject = cursor.fetchone()
        
        playerId = ''
        playerName = ''
        if roleObject != None:
            playerId = roleObject[0]
            playerName = roleObject[1]
            
        pay_list.append((payItem[0], playerId, playerName, payItem[1]))
    cursor.close()
    
    parg = {}
    parg["list_server"] = list_server
    parg["sdate"] = sdate
    parg["edate"] = edate
    parg["pay_list"] = pay_list
    parg["server_id"] = server_id
    parg["err_msg"] = err_msg
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response('pay/pay_user_rank.html', parg)


def user_pay(request):
    query_channel = request.POST.getlist('c')#channel_id
    user_id = request.POST.get("user_id", '')
    user_name = request.POST.get("user_name", "")
    sdate = request.POST.get("sdate", "")
    edate = request.POST.get("edate", "")
    query_server = request.POST.getlist('s')#server_id
    page_num = int(request.GET.get("page_num", "1"))
    
    if user_id == "":
        user_id = "0"
    user_id = int(user_id)
    
    page_size = 50
    
    list_channel = center_cache.get_channel_list()
    for item1 in list_channel:
        if query_channel.__len__() > 0:
            if str(item1.id) in query_channel:
                item1.is_show = 1 
        else:
            item1.is_show = 1
    
    list_server = get_server_list()
    for serverItem in list_server:
        if len(query_server) > 0:
            if str(serverItem.id) in query_server:
                serverItem.is_show = 1    
        else:
            serverItem.is_show = 1
    
    query_where = " a.pay_status=4"
    
    try:
        if sdate != "":
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            query_where += " and a.last_time>='%s'" % sdate
        if edate != "":
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            query_where += " and a.last_time<='%s'" % edate 
    except:
        sdate = ""
        edate = ""
        
    if query_channel.__len__() > 0 and query_channel.__len__() != list_channel.__len__():
        query_where += ' and c.id in(%s)' % (','.join(query_channel))
        
    if query_server.__len__() > 0 and query_server.__len__() != list_server.__len__():
        query_where += " and a.server_id in (%s)" % (','.join(query_server))
    
    if user_id > 0:
        query_where += " and a.pay_user=%s" % user_id
        
    user_name = user_name.strip()
    if user_name != "":
        query_where += " and b.username='%s'" % user_name
#        query_user_list=User.objects.filter(username=username,channel_key=channel.0key)
#        if len(query_user_list)>0:
#            query_where+=" and pay_user=%s"%query_user_list[0].id
    
    query_pagesize = " limit %s,%s" % ((page_num - 1) * page_size, page_num * page_size)
    
    query_sql = "select a.pay_user,b.username,sum(a.pay_amount) total_amount from pay_action a,users b,channel c where a.pay_user=b.id and a.channel_id=c.id and %s group by pay_user order by total_amount desc %s" % (query_where, query_pagesize)
    query_count = "select count(distinct a.pay_user) from pay_action a,users b,channel c where a.pay_user=b.id and a.channel_id=c.id and %s" % query_where
    
    print "channel_pay_rank_list:"
    print query_count
    print query_sql
    
    cursor = connection.cursor()
    cursor.execute(query_count)
    total_record = int(cursor.fetchone()[0])
    
    list_record = []
    if total_record > 0:
        cursor.execute(query_sql)
        list_record = cursor.fetchall()
    
    #cursor.close()
    
    if user_id <= 0:
        user_id = ""
    
    parg = {}
    parg["list_server"] = list_server
    parg["list_channel"] = list_channel
    parg["user_id"] = user_id
    parg["user_name"] = user_name
    parg["sdate"] = sdate
    parg["edate"] = edate
    parg["list_record"] = list_record
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response('pay/user_pay.html', parg);

def batch_change_extra(request):
    if request.method == 'POST':
        _r = {"code":1,"msg":""}
        rp = request.POST
        extra_on = rp.get('extra_on','')
        pay_channel_ids = request.POST.getlist('pay_channel_id')
        if extra_on:
            try:
                extra_on = extra_on == 'true'
                extra = json.loads(request.POST.get('extra','[]'))
                sdate = int(request.POST.get('sdate','0'))
                edate = int(request.POST.get('edate','0'))
                
                for p in PayChannel.objects.filter(id__in=pay_channel_ids):
                    _d = p.get_config_dict()
                    if extra_on:
                        assert sdate and sdate,'没有设置时间!'
                        _d['extra'] = extra
                        _d['sdate'] = sdate
                        _d['edate'] = edate
                        if _d.has_key('extra_off'):
                            del _d['extra_off']
                    else:
                        extra =  _d.get('extra',[])
                        _d['extra_off'] = extra
                        if extra:del _d['extra']
                    p.pay_config = json.dumps(_d,ensure_ascii=False)
                    print p.pay_config
                    p.save(using="write")
                _r["code"] = 0
            except Exception,e:
                _r["msg"] = str(e)
    return HttpResponse(json.dumps(_r)) 

def pay_channel_list(request):
    if request.GET.get('action','') == 'batch_change_extra':
        return batch_change_extra(request)
    func_name = request.GET.get('func','')
    list_record = PayChannel.objects.using('read').all().order_by("order")
    
    list_func = set()
    
    for item in list_record:
        list_func.add(item.func_name)
        if func_name != '':
            if item.func_name == func_name:
                item.is_show = True
            else:
                item.is_show = False
        else:
            item.is_show = True
            
    parg = {}
    parg['list_record'] = list_record
    parg['list_func'] = list_func
    parg['func_name'] = func_name
    return render_to_response('pay/pay_channel_list.html', parg);

def pay_channel_edit(request, payChannelId=0):
    pay_channel_id = int(payChannelId)
    is_copy = request.REQUEST.get('is_copy','')

            
            
    if 0 == pay_channel_id:
        pay_channel_id = int(request.GET.get('model_id', request.POST.get('model_id', 0)))
        
    model = None
    model_id = 0
    if pay_channel_id == 0:
        model = PayChannel(id=0)
    else:
        model = PayChannel.objects.get(id=pay_channel_id)
        if is_copy:
            model.id = 0
            model.name = '%s-copy' %  model.name
        model_id = model.id
    channel_list = Channel.objects.all()
    select_channel_ids = []
    if model.id > 0:
        for item in channel_list:
            if model.channel_key.find(',%s,' % item.id) > -1:
                select_channel_ids.append(item.id)

    channel_ids = model.channel_key
    if channel_ids != '':
        if channel_ids[0] == ',':
            channel_ids = channel_ids[1:]
        if channel_ids[-1] == ',':
            channel_ids = channel_ids[:-1]
    
    parg = {}
    parg["model"] = model
    parg['model_id'] = model_id
    parg["agent_channels_dict"] = get_agent_channels_dict(request)
    parg["select_channel_ids"] = select_channel_ids
    parg["channel_ids"] = channel_ids
    return render_to_response('pay/pay_channel_edit.html', parg);


def pay_channel_save(request, payChannelId=0):
    
    if request.POST.get('action','') == 'ajax_save':
        ids = request.POST.getlist('id',[])
        _d = {}
        amount = float(request.POST.get('amount',0))
        currency = request.POST.get('currency','').strip()
        if amount:
            _d['amount'] = amount
        if currency:
            _d['currency'] = currency
        PayChannel.objects.using('write').filter(id__in=ids).update(**_d)
        return HttpResponse('{"code":0}')
    
    pay_channel_id = int(payChannelId)
    if 0 == pay_channel_id:
        pay_channel_id = int(request.GET.get('model_id', request.POST.get('model_id', 0)))
    model = None
    model_id = 0
    if pay_channel_id > 0:
        model = PayChannel.objects.get(id=pay_channel_id)
        model_id = model.id
    if model == None:
        model = PayChannel()
        #model.id = 0
    channel_ids = request.POST.get('channel_ids', '')
    channel_ids = channel_ids.replace(u'，', ',')
    if '' != channel_ids:
        if channel_ids[0] != ',':
            channel_ids = ',%s' % channel_ids
        if channel_ids[-1] != ',':
            channel_ids = '%s,' % channel_ids
     
    model.server_id = int(request.POST.get("server_id", 0))
    model.channel_key = channel_ids 
    model.name = request.POST.get("name", "")
    model.link_id = request.POST.get("link_id", "")
    model.icon = request.POST.get("icon", "")
    model.func_name = request.POST.get("func_name", "")
    model.pay_type = int(request.POST.get("pay_type", 0))
    model.post_url = request.POST.get("post_url", "")    ######################
    # model.post_url = json.dumps(request.POST.get("post_url", ""))
    model.notice_url =request.POST.get("notice_url", "")   ######################
    # model.notice_url = json.dumps(request.POST.get("notice_url", ""))
    model.pay_config = request.POST.get("pay_config", "")
    model.unit = request.POST.get('unit', "")
    model.remark = request.POST.get("remark", "")
    model.exchange_rate = float(request.POST.get("exchange_rate", 0))
    model.status = int(request.POST.get("status", 0))
    model.order = int(request.POST.get("order", 0))
    model.currency = request.POST.get("currency","").strip()
    model.amount = float(request.POST.get("amount", 0))
    model.card_key = request.POST.get("card_key","").strip()
    model.gold = int(request.POST.get("gold","") or 0)
    if model.name != "":
        try:
            model.save(using='write')   
        except Exception, e:
            err_msg = trace_msg()
            print('payChannel save error:', e)
        return render_to_response("feedback.html",locals())
    parg = {}
    parg["model"] = model
    parg["model_id"] = model_id
    
    return render_to_response("pay/pay_channel_edit.html", parg)

def pay_channel_remove(request, payChannelId=0):
    pay_channel_id = int(payChannelId)
    if 0 == pay_channel_id:
        pay_channel_id = int(request.GET.get('model_id', request.POST.get('model_id', 0)))
    model = None
    if pay_channel_id > 0:
        model = PayChannel.objects.get(id=pay_channel_id)
    if model != None:
        try:
            model.delete(using='write')
        except Exception, e:
            print("payChannel delete error:", e)
    return HttpResponseRedirect("/pay/channel/list")

def pay_server_paychannel(request):
    query_server = request.POST.getlist('s')#server_id
    query_paychannel = request.POST.getlist('c')
    page_num = int(request.GET.get("page_num", "1"))
    
    sdate = request.POST.get('sdate', '')
    edate = request.POST.get('edate', '')
    
    page_size = 50
    
    query_where = " and a.pay_status=4" 
    
    try:
        if sdate != "":
            sdate = datetime.datetime.strptime(sdate, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            query_where += " and a.last_time>='%s'" % sdate
        if edate != "":
            edate = datetime.datetime.strptime(edate, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            query_where += " and a.last_time<='%s'" % edate
    except:
        sdate = ""
        edate = ""
    
    list_server = get_server_list()
    for serverItem in list_server:
        if len(query_server) > 0:
            if str(serverItem.id) in query_server:
                serverItem.is_show = 1    
        else:
            serverItem.is_show = 1
            
    list_paychannel = PayChannel.objects.all().order_by("id")
    for pcItem in list_paychannel:
        if len(query_paychannel) > 0:
            if str(pcItem.id) in query_paychannel:
                pcItem.is_show = 1 
            else:
                pcItem.is_show = 0
        else:
            pcItem.is_show = 1
    
    if len(query_server) > 0 and len(query_server) != len(list_server):
        query_where += " and a.server_id in (%s)" % (','.join(query_server))
    
    if len(query_paychannel) > 0 and len(query_paychannel) != len(list_paychannel):
        query_where += " and a.pay_type in (%s)" % (','.join(query_paychannel))
    
    query_sql = "SELECT  (SELECT `name` FROM servers WHERE `id`=a.server_id),\
    `name`,DATE(a.last_time),COUNT(DISTINCT pay_user),COUNT(pay_user),\
    SUM(pay_amount),SUM(pay_gold),SUM(pay_amount)/COUNT(DISTINCT pay_user)\
    FROM pay_action a,pay_channel b WHERE a.pay_type=b.id %s\
    GROUP BY a.server_id,a.pay_type,DATE(a.last_time)\
    ORDER BY a.server_id,a.pay_type,DATE(a.last_time)" % query_where
    query_count = "select count(*) from (%s) newTable" % query_sql
    
    query_limit = " limit %d,%d" % ((page_num - 1) * page_size, page_size)
    query_sql += query_limit
    
    print "pay_server_paychannel"
    print query_count
    print query_sql
    
    cursor = connection.cursor()
    cursor.execute(query_count)
    total_record = int(cursor.fetchone()[0])
    
    list_pay = []
    if total_record > 0:
        cursor.execute(query_sql)
        list_pay = cursor.fetchall()
    
    parg = {}
    parg["list_server"] = list_server
    parg["list_paychannel"] = list_paychannel
    parg["sdate"] = sdate
    parg["edate"] = edate
    parg["list_pay"] = list_pay
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
            
    return render_to_response("pay/pay_server_paychannel.html", parg)

#更新pay action 的渠道 ID
def update_pay_action_channel(request):
    
    sdate = request.GET.get('sdate', request.POST.get('sdate', ''))
    edate = request.GET.get('edate', request.POST.get('edate', ''))
    
    
    sid = int(request.GET.get('sid', request.POST.get('sid', 0)))
    eid = int(request.GET.get('eid', request.POST.get('eid', 0)))
    page_size = 100
    
    if eid - sid > page_size:
        eid = sid + page_size
    
    where_sql = ' (channel_id = 0 OR channel_id IS NULL) AND pay_status >= 4 AND pay_amount > 0 '
    
    if '' != sdate and '' != edate:
        sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m-%d')
        edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m-%d')
        where_sql = where_sql + " AND last_time BETWEEN '%s' AND '%s' " % (sdate, edate)
    
    center_con = connections['write']
    center_cur = center_con.cursor()
    pargs = {"status":1}
    
    if 0 == sid or 0 == eid:
        count_sql = 'SELECT MIN(id), MAX(id) FROM pay_action  WHERE %s ' % where_sql
        center_cur.execute(count_sql)
        result_item = center_cur.fetchone()
        min_id = 0
        max_id = 0
        if None != result_item:
            if None != result_item[0] and None != result_item[0]:
                min_id, max_id = int(result_item[0]), int(result_item[1])
        pargs["min_id"] = min_id
        pargs["max_id"] = max_id
        pargs["page_size"] = page_size 
         
        sid = min_id 
        eid = sid + page_size
    
    
    sql = 'SELECT id,server_id,channel_key,pay_user FROM pay_action WHERE %s AND id BETWEEN %s AND %s ' % (where_sql, sid, eid) 
    
    
    center_cur.execute(sql)
    list_data = center_cur.fetchall()
    
    channel_list = get_channel_list()
    for item in list_data:
        item_id = item[0]
        server_id = item[1]
        channel_key = item[2]
        pay_user = item[3]
        
        channel_id = 0
        
        if '' != channel_key and None != channel_key:
            
            for channel_item in channel_list:
                if channel_item.channel_key == channel_key:
                    channel_id = channel_item.id
            
        if 0 == channel_id:
            con = None
            cur = None
            try:
                con = getConn(server_id)
                cur = con.cursor()
                tmp_sql = 'SELECT channel_id FROM player_%s WHERE player_id=%s' % (server_id, pay_user)
                cur.execute(tmp_sql)
                list_player_result = cur.fetchall()
                if 0 < list_player_result.__len__():
                    channel_id = list_player_result[0][0]
            except:
                continue
            finally:
                if None != cur:
                    cur.close()
                
                if None != con:
                    con.close()
                
            
        
        if 0 != channel_id:
            update_sql = 'UPDATE pay_action SET channel_id=%s WHERE id=%s '
            center_cur.execute(update_sql % (channel_id, item_id))
    
    sid = eid + 1
    eid = sid + page_size
    
    pargs["sid"] = sid
    pargs["eid"] = eid
    pargs["status"] = 0
    return HttpResponse(json.dumps(pargs))

def add(request, func_name = ''):
    server_id = int(request.GET.get('server_id', request.POST.get('server_id', 0)))
    player_id = int(request.GET.get('player_id', request.POST.get('player_id', 0)))
    
    list_pay_channel = []
    if '' == func_name:
        list_pay_channel = PayChannel.objects.all()
    else:
        list_pay_channel = PayChannel.objects.filter(func_name = func_name)
    
    pargs = {}
    pargs["list_pay_channel"] = list_pay_channel
    pargs["server_id"] = server_id
    pargs["player_id"] = player_id
    
    return render_to_response('pay/add.html', pargs)
    
from views.game.pay import game_pay
#添加订单
def do_add(request):
    
    the_user = request.admin
    
    pay_channel = int(request.GET.get('pay_channel', request.POST.get('pay_channel', 0)))
    server_id = int(request.GET.get('server_id', request.POST.get('server_id', 0)))
    player_id = int(request.GET.get('player_id', request.POST.get('player_id', 0)))
    try:
        amount = float(request.GET.get('amount', request.POST.get('amount', 0)))
    except:
        return HttpResponse('金额只能输入数字')
    order_id = request.GET.get('order_id', request.POST.get('order_id', ''))
    
    if order_id.__len__() > 50:
        return HttpResponse('订单号过长')
    if amount > 9999:
        return HttpResponse('金额过多')
    
    ip = OperateLogManager.get_request_ipAddress(request)
    try:
        OperateLogManager.save_operate_log(the_user.id, '添加订单, pay_channel:%s server_id:%s player_id:%s  amount:%s' % (pay_channel, server_id, player_id, amount), '/pay/add', ip, 0)
    except Exception, ex:
        print ex
    finally:
        print 'add order, pay_channel:%s server_id:%s player_id:%s  amount:%s ' % (pay_channel, server_id, player_id, amount)
    
    channel_id = 0
    msg = ''
    try:
        conn = getConn(server_id)
        cur = conn.cursor()
        sql = 'SELECT channel_id FROM player_%s where player_id = %s' % (server_id, player_id)
        print sql
        cur.execute(sql)
        result_list = cur.fetchall()
        if 0 < result_list.__len__():
            channel_id = result_list[0][0]
        else:
            msg = '用户不存在'
    except Exception, ex:
        print ex
        msg = '用户不存在'
        
    the_pay_channel = PayChannel.objects.get(id = pay_channel)
    
    if the_pay_channel.func_name == 'zhichong': #直冲渠道看不见
        channel_id = 0
    
    now = datetime.datetime.now()
    if '' == msg:
        the_action = PayAction()
        the_action.query_id = the_action.get_query_id()
        the_action.order_id = order_id
        the_action.channel_key = ''
        the_action.channel_id = channel_id
        the_action.server_id = server_id
        the_action.pay_type = the_pay_channel.id
        the_action.pay_user = player_id
        the_action.pay_ip = ip
        the_action.pay_status = 2 
        the_action.card_no = ''
        the_action.card_pwd = ''
        the_action.post_time = now
        the_action.last_time = now
        the_action.post_amount = amount
        the_action.pay_amount = amount
        the_action.charge_id = -1
        the_action.charge_type = 0
        the_action.pay_gold = the_pay_channel.get_gold(amount)
        the_action.extra = the_pay_channel.get_extra(the_action,pay_channel_str='zhichong')
        the_action.remark = '手工添加 , 账号%s ' % the_user.id
        the_action.save()
        game_pay(the_action)
    else:
        return HttpResponse(msg)

    return HttpResponse('添加成功,订单号:%s' % the_action.query_id)

