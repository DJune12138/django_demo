# -*- coding: utf-8 -*-
#
#渠道相关
#
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.db.models import Q 
from django.utils.html import conditional_escape 
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
from django.template import loader, RequestContext
#==========================================

from models.statistic import QueryResult
from models.log import Log
from models.channel import Channel,Agent,ChannelOther,Conference
from models.server import Server,Group
from models.center import User, Question
from models.admin import Role
from util import md5, filter_sql,trace_msg,mkdirs
from cache import center_cache
import datetime, time
from settings import STATIC_ROOT
from views.widgets import get_agent_channels_dict,get_group_servers_dict

import json
import MySQLdb
import os

from urls.AutoUrl import Route
from views.base import notauth
import random


@Route()
def conference_edit(request,template='server/conference_edit.html'):
    '''平台编辑
    '''
    err_msg = ''
    agent_id = int(request.REQUEST.get('conference_id','') or 0)
    try:
        if agent_id:
            model = Conference.objects.prefetch_related('channel').get(id=agent_id)
            # select_group_ids = [ g.id for g in model.server_group.all()]
            # select_server_ids = [ g.id for g in model.server.all()]
            select_channel_ids = [ g.id for g in model.channel.all()]
        else:
            default_name = request.REQUEST.get('key', '')
            # password = ''.join(random.sample('123456789',6))
            model = Conference(id=0)
        
        # agent_channels_dict = get_agent_channels_dict(request)
        # group_servers_dict = get_group_servers_dict(request)
    except:
        err_msg = trace_msg()
    return render_to_response(template, locals())


def save_channnel_other(channel_ids,input_data):
    '''保存渠道的其他信息
    '''
    for cid in channel_ids:
        channel_other_model,_ = ChannelOther.objects.get_or_create(cid=cid)
        channel_other_model.save_filter_data(input_data)
        channel_other_model.save()
        
_save_path_root = os.path.join(STATIC_ROOT,'channel')
mkdirs(_save_path_root)

def make_channel_other_file(channel_ids=[]):
    '''生成静态渠道其他信息
    '''
    for c in ChannelOther.get_channel_models(channel_ids):
        file_path = os.path.join(_save_path_root,'%s.json' %  c.key)
        if c.data:
            with open(file_path,'wb') as fp:
                fp.write(c.data)
     
@Route()      
def channel_make(request):
    channel_ids = request.REQUEST.getlist('cid') 

    if request.method == 'POST':
        save_channnel_other(channel_ids,request.POST)
        _r =  HttpResponse('{"code":0}')
    else:
        _r = render_to_response('feedback.html', locals())
    make_channel_other_file(channel_ids)
    return _r

@Route()
def channel_set(request):
    '''批量设置渠道值'''
    channel_ids = set(request.REQUEST.getlist('cid'))
    set_val = request.REQUEST.get('set_value',"")
    add_val = request.REQUEST.get('add_value', "")
    if request.method == 'POST':
        ch_list = Channel.objects.filter(id__in=channel_ids)
        if set_val:
            for ch in ch_list:
                ch.allow_earn =int(set_val)
                ch.save()
        if add_val:
            for ch in ch_list:
                ch.allow_earn +=int(add_val)
                ch.save()

        _r = HttpResponse('{"code":0}')
    else:
        _r = render_to_response('feedback.html', locals())
    make_channel_other_file(channel_ids)
    return _r

@Route()
def conference_save(request):
    '''平台保存
    '''
    err_msg = ''
    print request.REQUEST.get('name','')
    print request.REQUEST.get('alias','')
    print request.REQUEST.get('game_app_key','')
    try:
        agent_id = int(request.REQUEST.get('conference_id','') or 0)

        if agent_id:
            agent = Conference.objects.get(id=agent_id)
            agent.last_time = datetime.datetime.now()

        else:
            agent = Conference()
            agent.create_time = datetime.datetime.now()
            agent.last_time = agent.create_time
        agent.alias =request.REQUEST.get('alias','')
        agent.name = request.REQUEST.get('name','')
        agent.game_app_key =request.REQUEST.get('game_app_key','')
        agent.save()
        # agent.set_attr('name',request.REQUEST.get('name',''),null=False)
        # agent.set_attr('alias',request.REQUEST.get('alias',''),null=False)
        # # agent.set_attr('username',request.REQUEST.get('username',''),null=False)
        # # agent.set_attr('password',request.REQUEST.get('password',''),null=False)
        #
        # game_app_key = request.REQUEST.get('game_app_key','')
        # agent.set_attr('game_app_key',game_app_key,null=False)
        # agent.last_time = datetime.datetime.now()
        # agent.save()
        #
        # server_ids = request.REQUEST.getlist('server_id')
        # server_group_ids = request.REQUEST.getlist('server_group_id')
        # channel_ids = request.REQUEST.getlist('channel_id')
        # agent.server.clear()
        # agent.server_group.clear()
        # agent.channel.clear()
        # agent.server.add(*Server.objects.filter(id__in=server_ids))
        # agent.server_group.add(*Group.objects.filter(id__in=server_group_ids))
        # channel_models = Channel.objects.filter(id__in=channel_ids)
        # channel_models.update(agent_name=agent.alias)
        # channel_models.update(last_time=datetime.datetime.now())
        # channel_models.update(game_app_key=agent.game_app_key)
        # if server_group_ids:
        #     try:
        #         group_key = Group.objects.filter(id=int(server_group_ids[0]))[0].group_key
        #         channel_models.update(group_key=group_key)
        #     except BaseException as e:
        #         print 'get group_key error:',e
        # agent.channel.add(*channel_models)

    except:
        err_msg = trace_msg()
        
    return render_to_response('feedback.html', locals())

@Route()
def agent_remove(request):

    agent_id = int(request.REQUEST.get('agent_id','') or 0)
    try:
        agent = Agent.objects.get(id=agent_id)
        
    except:
        err_msg = trace_msg()
        
    return render_to_response('feedback.html',locals())

@Route()
def conference_list(request):
    # print request.POST
    if request.POST.get('action','') == 'change_agent_name':            ##################post请求时
        ids = request.POST.getlist('id',[])
        agent_name = request.POST.get('agent_name','')
        agent_name = agent_name.strip()
        Channel.objects.using('write').filter(id__in=ids).update(agent_name=agent_name)
        return HttpResponse('{"code":0}')
    
    agents = Conference.objects.all().prefetch_related('channel')
    # model_other = ChannelOther()
    new_list = []
    agent_channel = []
    all_channel = Channel.objects.all()
    # all_ear = 0
    for agent in agents:
        for c in agent.channel.all():
            # all_ear += c.allow_earn
            agent_channel.append(c.id)
    for channel in all_channel:
        if channel.id not in agent_channel:
            new_list.append(channel)
    return render_to_response('server/conference_list.html', locals())

@Route()
def channel_edit(request, channel_id=0):
    channel_id = channel_id or int(request.REQUEST.get('channel_id', '') or 0)
    agent_id = int(request.REQUEST.get('agent_id','') or 0)
    agents = Conference.objects.using('read').all()
    model = None
    if channel_id == 0:
        default_name = request.GET.get('key', '')
        model = Channel(id=0, channel_key=default_name, name=default_name, username=default_name)
        model_other = ChannelOther()
    else:
        model = Channel.objects.get(id=channel_id)
        model_other,_ = ChannelOther.objects.get_or_create(cid=model.id)
        
    return render_to_response('server/manage_conference_edit.html', locals())

@Route()
def channel_save(request, channel_id=0, template = 'feedback.html'):
    '''渠道保存
    '''
    channel_id = channel_id or int(request.REQUEST.get('channel_id', '') or 0)
    agent_id = int(request.REQUEST.get('agent_id','') or 0)
    err_msg = ''

    model = None
    if channel_id == 0:
        model = Channel()
        model.create_time = datetime.datetime.now()
    else:
        model = Channel.objects.get(id=channel_id)
    
    model.channel_key = request.POST.get('key', '')
    model.name = request.POST.get('name', '')
    model.allow_earn = request.POST.get('allow_earn', '')
    if model.channel_key != '' and model.name != '':
        if Channel.objects.filter(channel_key=model.channel_key).exclude(id=model.id).exists():     ##################
            err_msg = '已存在相同渠道号!'
        else:
            model.last_time = datetime.datetime.now()
            model.save()
            save_channnel_other([model.id],request.POST)
            if agent_id:
                agent = Conference.objects.get(id=agent_id)
                agent.channel.add(model)
                model.game_app_key = agent.game_app_key
                model.agent_name = agent.alias
                model.save()
    else:
        err_msg = '所有数据不能为空!'
    
    return render_to_response(template, locals())

@Route()
def channel_remove(request, channel_id=0,conference_id=0):
    channel_id = int(channel_id or request.REQUEST.get('channel_id','') or 0)
    conference_id = int(conference_id or request.REQUEST.get('conference_id', '') or 0)
    try:
        if channel_id > 0:
            ccc =  Conference.objects.filter(id=conference_id)[0]
            chne = Channel.objects.filter(id=channel_id)[0]
            ccc.channel.remove(chne)
            return HttpResponse(json.dumps({"code": 0, "msg": "删除成功"}))
    except Exception as e:
        return HttpResponse(e)


#---- 渠道后台 ---
def index(request):
    channel_id = int(request.session.get('channel_id', '0'))
    if channel_id > 0: 
        the_channel = center_cache.get_channel_by_id(channel_id)
    try:    
        role = Role.objects.using('read').get(name='渠道')
        list_menu = role.menu.all()
    except:
        print('发生错误 未添加渠道角色')
    
    parg = {}
    parg["the_channel"] = the_channel
    parg["list_menu"] = list_menu
    
    return render_to_response('channel/index.html', parg)

def channel_view(request, query_id=1, channel_id=0):
    
    channel_id = int(channel_id)
    
    if channel_id == 0:
        channel_id = int(request.GET.get('channel_id', '0'))
    
    query_id = int(query_id)
    server_id = int(request.GET.get('server_id', 0))
    the_query = QueryResult.objects.using('read').get(id=query_id)
    
    #list_statistic = the_query.statistic.all()
    
    list_statistic = get_statistic_in_query(query_id)
    
    join_results = []
    for item in list_statistic:
        join_results.append(str(item[0])) #item.id
        
     
    if channel_id == 0:
        channel_id = int(request.session.get('channel_id', '0'))
        
    channel = Channel.objects.using('read').get(id=channel_id)
    
    list_server = []
    if channel != None:
        list_server = Server.objects.filter(channel__id=channel_id)
        
    where_server = ''
    if server_id > 0:
        where_server = ' and server_id=%d' % server_id
        
    the_date = datetime.datetime.now()
    sdate = request.GET.get('sdate', the_date.strftime('%Y-%m-1'))
    edate = request.GET.get('edate', the_date.strftime('%Y-%m-%d'))

    
    query_date = ''
    try:
        if sdate != '':
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query_date = ' and result_time>=\'%s\'' % sdate
        if edate != '':
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query_date += ' and result_time<=\'%s\'' % edate
    except:
        sdate = ''
        edate = ''

    query_channel = ''    
    if channel != None:    
        if channel_id > 0:
            query_channel = ' and channel_id=%d' % channel_id
    
    cursor = connections['read'].cursor()
    count_sql = 'select count(distinct result_time) result from result where statistic_id in(%s)%s%s%s' % (','.join(join_results), query_channel, where_server, query_date)
    cursor.execute(count_sql)
    total_record = int(cursor.fetchone()[0])
    
    list_record = []
    if total_record > 0:
        select_str = 'result_time'
        for item in join_results:
            select_str += ',sum(case when `statistic_id`=%s then result else 0 end) item%s' % (item, item)
        
        query_sql = 'select %s from result where statistic_id in(%s)%s%s%s group by result_time order by result_time desc' % (select_str, ','.join(join_results), query_channel, where_server, query_date)
        cursor.execute(query_sql)
        list_record = cursor.fetchall()
    
    #cursor.close()    
    
    parg = {}
    parg["channel"] = channel
    parg["server_id"] = server_id
    parg["list_server"] = list_server
    parg["sdate"] = sdate
    parg["edate"] = edate
    parg["the_query"] = the_query
    parg["list_statistic"] = list_statistic
    parg["list_record"] = list_record
    parg["query_id"] = query_id
    parg["channel_id"] = channel_id
    
    return render_to_response('channel/result_list.html', parg, context_instance=RequestContext(request, processors=[channel_channelLoginStatus]))

def get_statistic_in_query(queryid):
    sql = "SELECT S.id, S.`name`, S.exec_interval, S.log_type, S.remark FROM query_result_statistic AS QR, statistic AS S WHERE QR.statistic_id = S.id AND QR.queryresult_id = %d ORDER BY QR.id" % queryid
    cursor = connections['read'].cursor()
    cursor.execute(sql)
    list_record = cursor.fetchall()
    return list_record

def channel_list_allchannel(request, query_id=1, channel_id=0):
    query_id = int(query_id)
    query_server = request.GET.getlist("s")
    if not QueryResult.objects.using('read').filter(id=query_id).exists():
        return HttpResponse("该查询已不存在,已被删除")
    the_query = QueryResult.objects.using('read').get(id=query_id)
    
    list_statistic = the_query.statistic.all()
    join_results = []
    for item in list_statistic:
        join_results.append(str(item.id))
        
    channel_id = int(channel_id) 
    if channel_id == 0:
        channel_id = int(request.session.get('channel_id', '0')) 
    channel = center_cache.get_channel_by_id(channel_id)
    
    list_server = []
    if channel != None:
        list_server = Server.objects.using('read').filter(channel__id=channel_id)
        for serverItem in list_server:
            serverItem.is_show = False
            if len(query_server) > 0:
                if str(serverItem.id) in query_server:
                    serverItem.is_show = True
            else:
                serverItem.is_show = True
            
        
    where_server = ''
    if len(query_server) > 0:
        where_server = ' and server_id in (%s)' % (','.join(query_server))
    
    the_date = datetime.datetime.now()
    sdate = request.GET.get('sdate', the_date.strftime('%Y-%m-1'))
    edate = request.GET.get('edate', the_date.strftime('%Y-%m-%d'))

    
    query_date = ''
    try:
        if sdate != '':
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query_date = ' and result_time>=\'%s\'' % sdate
        if edate != '':
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query_date += ' and result_time<=\'%s\'' % edate
    except:
        sdate = ''
        edate = ''

    query_channel = ''    
#    if channel!=None:    
#        if channel_id>0:
#            query_channel = ' and channel_id=%d'%channel_id
        
    #page_size = 30
    #page_num = int(request.GET.get('page_num', '1'))
    
    #list_channel = Channel.objects.using('read').all()
    cursor = connections['read'].cursor()
    count_sql = 'select count(distinct result_time) result from result where statistic_id in(%s)%s%s%s' % (','.join(join_results), query_channel, where_server, query_date)
    print 'count_sql:'
    print count_sql
    cursor.execute(count_sql)
    total_record = int(cursor.fetchone()[0])
    
    list_record = []
    if total_record > 0:
        select_str = 'result_time'
        for item in join_results:
            select_str += ',sum(case when `statistic_id`=%s then result else 0 end) item%s' % (item, item)
        
        query_sql = 'select %s from result where statistic_id in(%s)%s%s%s group by result_time' % (select_str, ','.join(join_results), query_channel, where_server, query_date)
        print 'query_sql:'
        print(query_sql)
        cursor.execute(query_sql)
        list_record = cursor.fetchall()
    
    #cursor.close()    
    
    parg = {}
    parg["channel"] = channel
    parg["list_server"] = list_server
    parg["sdate"] = sdate
    parg["edate"] = edate
    parg["list_statistic"] = list_statistic
    parg["list_record"] = list_record
    parg["the_query"] = the_query
    
    return render_to_response('channel/result_list_allchannel.html', parg, context_instance=RequestContext(request, processors=[channel_channelLoginStatus]))


def login_key(request):
    channel_id = int(request.session.get('channel_id', '0'))
    try:
        channel = center_cache.get_channel_by_id(channel_id)
        
        if request.method == 'POST':
            new_key = request.POST.get('key', '')
            if new_key != '' and new_key != channel.login_key:
                channel.login_key = new_key
                channel.save(using='write')
    
    except Exception, e:
        print('change login key has error', e)
    
    parg = {}
    parg["channel"] = channel
    
    return render_to_response('channel/login_key.html', parg)
    
def pay_list(request):
    page_size = 50
    
    # 获取  “搜索” 参数
    page_num = int(request.GET.get('page_num', '1'))
    server_id = int(request.GET.get('server_id', '0'))
    
    user_id = 0
    try:
        user_id = int(request.GET.get('user_id', '0'))
    except Exception:
        user_id = 0
        
    #the_date = datetime.datetime.now()
    sdate = request.GET.get('sdate', '')
    edate = request.GET.get('edate', '')
    
    channel_id = int(request.session.get('channel_id', '0'))# 获取登陆人 channel id
    
    keyword = request.GET.get("keyword", "")
    
    # 获取  “搜索” 参数 END
    
    #获取Server 对象 和 Server列表
     
    list_server = Server.objects.using('read').filter(channel__id=channel_id) #根据当前channel id 获取服务器列表
    itemServerList = {}
    for item in list_server:
        itemServerList[item.id] = item.name
     
    if server_id == 0: # 获取 Get参数没有 传 server_id 则在  Session 中获取 
        server_id = int(request.session.get("server_id", '0'))
        
    if server_id == 0 and len(list_server) > 0:
        server_id = list_server[0].id
    
    
    if server_id > 0:
        server = Server.objects.using('read').get(id=server_id)        
    
    #获取Server 对象  END
     
    
    channel = center_cache.get_channel_by_id(channel_id) # 获取当前 渠道对象 
          
    #获取查询结果
    result = get_payDataSource(keyword, user_id, server_id, sdate, edate, channel, server, page_size, page_num)
    
    list_record = result['dataSource']
    total_record = result['total']
     
    #数据处理
    STATUS_CHOICES = {0:'已提交', 1:'已转发', 2:'已支付,金币发放中', 3:'金币发放中', 4:'充值成功,金币已发放'}
    result_list = [] 
    
    for item in list_record: 
        item = list(item)
        server_id = item[3]
        if server_id > 0:  
            item[3] = itemServerList.get(server_id, '--')
        else:
            item[3] = "--"
        
        pay_status = item[5]
        remark = item[8]
        if  pay_status < 0:
            item[5] = u'失败:%s' % remark
        else:
            item[5] = STATUS_CHOICES[pay_status]
        post_time = item[11]
        item[11] = post_time.strftime('%m-%d %H:%M:%S')
        result_list.append(item)
         
    parg = {}
    parg["channel"] = channel
    parg["list_server"] = list_server
    parg["keyword"] = keyword
    parg["user_id"] = user_id
    parg["result_list"] = result_list
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response('channel/pay_list.html', parg, context_instance=RequestContext(request, processors=[channel_channelLoginStatus]))

#渠道后台的查询
def channel_query_result(request, query_id=0,): 
    page_num = int(request.GET.get('page_num', '1'))
    sdate = request.GET.get('sdate', '')
    edate = request.GET.get('edate', '')
    server_id = int(request.GET.get('server_id', -1))
    channel_id = int(request.session.get('channel_id', '0'))  # 获取登陆人 channel id
    
    if channel_id <= 0 :
        return HttpResponse("请登录")
    
    page_size = 50  
    
    list_server = Server.objects.using('read').filter(channel__id=channel_id)
    if server_id <= 0:
        if list_server.__len__() > 0 :
            server_id = list_server[0].id
        else:
            return HttpResponse("所在渠道没有服务器")
        
    list_statistic_sort = get_statistic_in_query(int(query_id))#获取 统计项
    
    join_results = []
    list_statistic_name = []
    exec_interval = 0
    canSelectServer = False
    for item in list_statistic_sort:
        exec_interval = item[2]       #exec_interval
        join_results.append(str(item[0]))      #id
        list_statistic_name.append(item[1])    #name
    
    
    
    nowdate = datetime.datetime.now()
   
    query_date = ''
    try:
        if sdate != '':
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m-%d')# %H:%M:%S
            query_date = ' and result_time>=\'%s\'' % sdate
        if edate != '':
            if query_date != '':
                query_date += ' and '
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query_date += ' result_time<=\'%s\'' % edate
    except:
        sdate = ''
        edate = ''
         
    query_channel_str = ' and channel_id = %s' % (channel_id)
     
    query_server_str = ' and server_id = %s' % (server_id)
        
    page_size = 30
    page_num = int(request.GET.get('page_num', '1'))
    if page_num < 1:
        page_num = 1
    
    spos = (page_num - 1) * page_size
    
    cursor = connections['read'].cursor()
    count_sql = 'select count(distinct result_time) result from result where statistic_id in(%s)%s%s%s' % (','.join(join_results), query_server_str, query_channel_str, query_date)
    
    cursor.execute(count_sql)
    total_record = int(cursor.fetchone()[0])
    
    list_record = []
    if total_record > 0:
        select_str = 'result_time'
        for item in join_results:
            select_str += ',sum(case when `statistic_id`=%s then result else 0 end) item%s' % (item, item)
        
        query_sql = 'select %s from result where statistic_id in(%s)%s%s%s group by create_time order by create_time desc limit %d,%d' % (select_str, ','.join(join_results), query_server_str, query_channel_str, query_date, spos, page_size)
        print(query_sql)
        cursor.execute(query_sql)
        list_record = cursor.fetchall()
    #cursor.close()
    
     
#    print(total_record,query_sql)
    
    list_record_arr = []
    for item in list_record:
        item = list(item)
        item[0] = time.mktime(item[0].timetuple()) * 1000;
        list_record_arr.append(item)
    list_record_arr = str(list_record_arr).replace('(', '[').replace(')', ']').replace('L', '')
    list_statistic_name = str(list_statistic_name).replace('u\'', '\'')
    
    parg = {}
    parg["list_server"] = list_server
    parg["server_id"] = server_id
    parg["sdate"] = sdate
    parg["edate"] = edate
    parg["list_statistic_sort"] = list_statistic_sort
    parg["list_record"] = list_record
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response('channel/channel_query_view.html', parg)
    
     

def get_payDataSource(keyword, user_id, server_id, sdate, edate, channel, server, page_size, page_num):
    #result = {'result': {}, 'total':0 }
    result = get_NoPayChannel_payList(keyword, user_id, server_id, sdate, edate, channel, server, page_size, page_num)
#    if get_payChannel_count(channel.key) > 0 : #当前渠道时候具有自己的支付渠道
#        result = get_HasPayChannel_payList(keyword, user_id, server_id, sdate, edate, channel, server, page_size, page_num)
#    else: 
#        result = get_NoPayChannel_payList(keyword, user_id, server_id, sdate, edate, channel, server, page_size, page_num)
    return result
         
#获取没有支付通道的支付列表
def get_NoPayChannel_payList(keyword, user_id, server_id, sdate, edate, channel, server, page_size, page_num):
    result = {'result': {}, 'total': 0}
    limit = " LIMIT %d, %d " % ((page_num - 1) * page_size, page_num * page_size)
    
    sql = ''' SELECT a.id, a.query_id, a.order_id,   a.server_id,   a.pay_user,   a.pay_status, a.card_no,    a.last_time, a.remark, a.post_amount, a.pay_amount, a.post_time, a.pay_gold,b.name as channel_name, a.extra 
    FROM  pay_action a, pay_channel b WHERE a.pay_type = b.id  AND  a.channel_id = %s %s order by a.id desc %s '''

    
    count_sql = ''' SELECT COUNT(0) FROM pay_action a WHERE a.channel_id = %s %s '''
    
    query = ' '
    if keyword != '':
        keyword = keyword.replace('\'', '')
        query += " AND (a.order_id='%s' OR a.query_id='%s' ) " % (keyword, keyword)
     
    if user_id > 0:
        query += " AND a.pay_user=%d " % user_id
    if server_id > 0:
        query += " AND a.server_id=%d " % server.id 
    
    try:
        if sdate != '':
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query += " AND a.last_time > '%s' " % sdate 
        if edate != '':
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query += " AND a.last_time < '%s' " % sdate 
    except Exception, e:
        print('pay list has error', e)
        
    sql = sql % (channel.id, query, limit)
    
    count_sql = count_sql % (channel.id, query)
    
    cursor = connections['read'].cursor()   
    
    list_record = []
    #获取总数据量
    cursor.execute(count_sql)
    total_record = int(cursor.fetchone()[0]) 
    if total_record > 0:#如果总数大于0 才查询数据 
        cursor.execute(sql)
        list_record = cursor.fetchall()
    
    
    result['dataSource'] = list_record
    result['total'] = total_record
    
    return result
     
#获取有支付通道的支付列表 
def get_HasPayChannel_payList(keyword, user_id, server_id, sdate, edate, channel, server, page_size, page_num):
    
    result = {'result': {}, 'total': 0}
    
    
    limit = " LIMIT %d, %d " % ((page_num - 1) * page_size, page_num * page_size)
     
    
    sql = ''' SELECT a.id, a.query_id, a.order_id,   a.server_id,   a.pay_user,   a.pay_status, a.card_no,    a.last_time, a.remark, a.post_amount, a.pay_amount, a.post_time, a.pay_gold,b.name as channel_name, a.extra

    FROM  pay_action a, pay_channel b WHERE a.pay_type = b.id AND a.pay_type IN ( SELECT id FROM pay_channel WHERE channel_key like '%s%%' ) %s order by a.id desc %s '''

    count_sql = '''   SELECT COUNT(0) FROM pay_action a WHERE a.pay_type IN ( SELECT id FROM pay_channel WHERE channel_key like '%s%%' ) %s  '''
    query = ' '
    if keyword != '':
        keyword = keyword.replace('\'', '')
        query += " AND (a.order_id='%s' OR a.query_id='%s' ) " % (keyword, keyword)
     
    if user_id > 0:
        query += " AND a.pay_user=%d " % user_id
    if server_id > 0:
        query += " AND a.server_id=%d " % server.id 
    
    try:
        if sdate != '':
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query += " AND a.last_time > '%s' " % sdate 
        if edate != '':
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query += " AND a.last_time < '%s' " % sdate 
    except Exception, e:
        print('pay list has error', e)
        
    sql = sql % (channel.key, query, limit)
     
    count_sql = count_sql % (channel.key, query)
    
    cursor = connections['read'].cursor()
    
    list_record = []
    #获取总数据量
    cursor.execute(count_sql)
    total_record = int(cursor.fetchone()[0]) 
    if total_record > 0:#如果总数大于0 才查询数据 
        cursor.execute(sql) 
        list_record = cursor.fetchall()
     
    result['dataSource'] = list_record
    result['total'] = total_record 
    return result

# 根据渠道KEY 获取 支付渠道
def get_payChannel(channel_key):
    sql = " SELECT id, server_id, channel_key, name, icon, link_id, func_name, pay_type, post_url, notice_url, pay_config, remark, exchange_rate, status, order, unit FROM pay_channel WHERE channel_key like '%s%%' " % channel_key
    cursor = connections['read'].cursor()
    cursor.execute(sql)
    list_record = cursor.fetchall()
    return list_record

# 根据渠道KEY 获取支付渠道总数 
def get_payChannel_count(channel_key):
    sql = " SELECT COUNT(0) FROM pay_channel WHERE channel_key like '%s%%' " % channel_key
    cursor = connections['read'].cursor()
    cursor.execute(sql)
    count_list = cursor.fetchone()
    total_record = int(count_list[0])
    return total_record

def player_list(request, server_id=0): 
    page_size = 30
    page_num = int(request.REQUEST.get("page_num", "1"))
    is_ajax = request.REQUEST.get('ajax', False)
    if(page_num < 1):
        page_num = 1
    
    list_channel = center_cache.get_channel_list()
    itemChannelList = {}
    for item in list_channel:
        itemChannelList[item.id] = item.name
    

   
    player_key = request.REQUEST.get('key', '')
    key_type = request.REQUEST.get('key_type', '0')
    user_type = int(request.REQUEST.get('user_type', '-1'))
    export = request.REQUEST.get('export','')
    channel_id = int(request.session.get('channel_id', '0'))
    #if channel_id > 0:
        #channel = center_cache.get_channel_by_id(channel_id)
    #print('channel_id', channel_id)
    list_server = Server.objects.using('read').filter(channel__id=channel_id)
    itemServerList = {}
    
    for item in list_server:
        itemServerList[item.id] = item.name
        
    server_id = int(request.REQUEST.get("server_id", "0"))
    
    if server_id <= 0:
        server_id = int(request.session.get("serverId", "0"))
    if server_id <= 0 and len(list_server) > 0:
        server_id = list_server[0].id
    if server_id > 0:
        server = Server.objects.using('read').get(id=server_id)
    
    total_record = 0
    player_list = []
    if server_id > 0:
        the_db_config = json.loads(server.log_db_config)
        conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], passwd=the_db_config['password'], port=the_db_config.get('port',3306),db=the_db_config['db'], charset="utf8")
        #conn.autoCommit(True)
        cursor = conn.cursor()
         
        query = []
        
        if channel_id > 0:
            query.append('channel_id=%d' % channel_id)
      
        if player_key != "":
            if key_type == '0':
                query.append('player_id=\'%s\'' % player_key)
            elif key_type == '1':
                query.append('player_name like \'%s%%\'' % player_key.encode('utf-8'))
            elif key_type == '2':
                query.append('link_key=\'%s\'' % player_key)
            elif key_type == '3':
                query.append('mobile_key=\'%s\'' % player_key)
        if user_type > -1:
            query.append('user_type=%d' % player_key)
            
        if len(query) > 0:
            sql1 = 'select count(1) from player_%d where %s' % (server_id, ' and '.join(query))
            if not export:
                sql2 = 'select player_id,player_name,link_key,login_num,mobile_key,last_time,create_time,status from player_%d where %s order by id desc limit %d,%d' % (server_id, ' and '.join(query), (page_num - 1) * page_size,page_size)
            else:
                sql2 = 'select player_id,player_name,link_key,login_num,mobile_key,last_time,create_time,status from player_%d where %s order by id desc' % (server_id, ' and '.join(query))
        else:
            sql1 = 'select count(1) from player_%d' % server_id
            sql2 = 'select player_id,player_name,link_key,login_num,mobile_key,last_time,create_time,status from player_%d order by id desc limit %d,%d' % (server_id, (page_num - 1) * page_size, page_size)
        
        cursor.execute(sql1)
        count_list = cursor.fetchone()
        total_record = int(count_list[0])
        if total_record > 0: 
            cursor.execute(sql2)
            if not export:
                player_list = cursor.fetchall()
            elif channel_id:
                return export_player_list(channel_id,server_id,cursor)
        cursor.close()
    
    parg = {}
    parg["server_id"] = server_id
    parg["player_key"] = player_key
    parg["player_list"] = player_list
    parg["list_server"] = list_server
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    if is_ajax:
        return render_to_response('channel/player_list_block.html', parg)
        
    return render_to_response('channel/player_list.html', parg)

from views.base import GlobalPathCfg
def export_player_list(channel_id,server_id,cur):
    _d = {"url":"",
          "code":1}
    save_dir = os.path.join(GlobalPathCfg().get_static_folder_path(),'export','query')
    file_name = '%s_%s_player_list.xls' % (channel_id,server_id)
    file_path = os.path.join(save_dir,file_name)
    try:
        fp = open(file_path,'wb')
        fp.write('<table>')
        while 1:
            result = cur.fetchmany(1000)
            if not result:
                break
            for row in result:
                fp.write('<tr><td>')
                row_str = '</td><td>'.join([ str(c) for c in row])
                fp.write(row_str)
                fp.write('</td></tr>')
        fp.write('</table>')
        fp.close()
        _d["code"] = 0 
        _d["url"] = '/static/export/query/%s' % file_name
    except Exception,e:
        _d["msg"] = str(e)
    return HttpResponse(json.dumps(_d))

def user_list(request):
    page_size = 30
    page_num = int(request.GET.get('page_num', '1'))
    the_date = datetime.datetime.now()
    sdate = request.GET.get('sdate', the_date.strftime('%Y-%m-1'))
    edate = request.GET.get('edate', the_date.strftime('%Y-%m-%d'))

    if page_num < 1:
        page_num = 1
    
    user_key = request.GET.get('key', '')
    
    query = None
    server_id = int(request.GET.get('server_id', '0'))
    
    channel_id = int(request.session.get('channel_id', '0'))
    if server_id == 0:
        server_id = int(request.session.get("server_id", '0'))

    query_date = ''
    try:
        if sdate != '':
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query_date = ' and create_time>=\'%s\'' % sdate
        if edate != '':
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d').strftime('%Y-%m-%d')
            query_date = ' and create_time<=\'%s\'' % edate
    except:
        sdate = ''
        edate = ''
        
    channel = center_cache.get_channel_by_id(channel_id)
#    server=Server.objects.get(id=server_id)
    
#    try:
#        the_db_config = json.loads(server.log_db_config)
#        conn = MySQLdb.connect(host=the_db_config['host'],user=the_db_config['user'],passwd=the_db_config['password'],db=the_db_config['db'])
#    except:
#        # '数据库链接出错!'
#        return HttpResponse("连接错误!") 
#
#    cursor = conn.cursor()
#    
#    sql1="SELECT count(1) FROM log_create_role WHERE log_server=%s AND log_channel=%s%s"%(server_id,channel_id,query_date)
#    sql2="SELECT log_result,log_server,log_channel,log_user,f1,log_time FROM log_create_role WHERE log_server=%s AND log_channel=%s%s"%(server_id,channel_id,query_date)
#    cursor.execute(sql1)
#    
#    total_record=int(cursor.fetchone()[0])
#    
#    cursor.execute(sql2)
#    list=cursor.fetchall()
#    
#    cursor.close()  
    query = Q(channel_key=channel.key)
    if user_key != '':
        key_type = int(request.GET.get('key_type', '0'))
        user_key = user_key.replace('\'', '\'\'')
        if key_type == 0:
            try:
                query = query & Q(id=int(user_key))
            except:
                print('key_value has error')
        else:
            query = query & Q(username__icontains=user_key)

    total_record = User.objects.using('read').filter(query).count()
    list_record = []
    if total_record > 0:
        list_record = User.objects.using('read').filter(query)[(page_num - 1) * page_size:page_num * page_size]
    
    parg = {}
    parg["channel"] = channel
    parg["user_key"] = user_key
    parg["list_record"] = list_record
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response('channel/user_list.html', parg, context_instance=RequestContext(request, processors=[channel_channelLoginStatus]))


def user_lock(request, user_id, is_lock):
    model_id = int(user_id)
    is_lock = int(is_lock)
    if model_id > 0 :
        channel_id = int(request.session.get('channel_id', '0'))
        try:
            channel = center_cache.get_channel_by_id(channel_id)
            model = User.objects.using('read').get(id=model_id, channel_key=channel.key)
            if is_lock == 1:
                if not model.is_lock():
                    model.status -= 5
            else:
                if model.is_lock():
                    model.status += 5

            model.save(using='write')
        except Exception, e:
            print('lock user error:', e)
            
    return render_to_response('feedback.html')


def user_password(request, user_id):
    user_id = int(user_id)
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if user_id > 0 and password != '':
            try:
                channel_id = int(request.session.get('channel_id', '0'))
                channel = center_cache.get_channel_by_id(channel_id)
                the_user = User.objects.using('read').get(id=user_id, user_type=0, channel_key=channel.key)
                the_user.password = md5(password.lower())
                the_user.save(using='write')
                msg = '操作成功!'        
            except Exception, e:
                print('set password error:', e)
                msg = e

    parg = {}
    parg["user_id"] = user_id
    parg["msg"] = msg
    
    return render_to_response('player/user_password.html', parg)


def player_block(request, server_id=0, player_id=0):
    channel_id = int(request.session.get('channel_id', '0'))
    player_id = int(player_id)
    server_id = int(server_id)

    if player_id > 0 :
        server = Server.objects.using('read').get(id=server_id)
        the_db_config = json.loads(server.log_db_config)
        conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], port=the_db_config.get('port',3306),passwd=the_db_config['password'], db=the_db_config['db'], charset="utf8")
        conn.autocommit(True)
        cursor = conn.cursor()
        try:
            if request.GET.get('is_lock', '1') == '1':
                the_status = -1
            else:
                the_status = 0

            query_sql = 'update player_%d set status=%d where player_id=%d and channel_id=%d' % (server_id, the_status, player_id, channel_id)
            cursor.execute(query_sql)
            cursor.close()
        except Exception, e:
            print('lock user error:', e)
    
    parg = {}
    parg["player_id"] = player_id 

    return render_to_response('player/player_block.html', parg)

def player_query(request):
    channel_id = int(request.session.get('channel_id', '0'))
    server_id = int(request.GET.get('server_id', '0'))
    key_type = int(request.GET.get('key_type', '0'))
    keyword = request.GET.get('keyword', '')
    player_list = []
    list_server = Server.objects.filter(channel__id=channel_id)
    if server_id > 0 and keyword != '':
        try:
            server = Server.objects.get(id=server_id)
            the_db_config = json.loads(server.log_db_config)
            conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], passwd=the_db_config['password'],port=the_db_config.get('port',3306), db=the_db_config['db'], charset="utf8")
            conn.autocommit(True)
            cursor = conn.cursor()
#            role_name = role_name.decode('utf-8')
            keyword = keyword.replace('\'', '\'\'')
            query_sql = {0:'select log_result,log_user,f1,log_time from log_create_role where f1 like \'%s%%\' and log_channel in(0,%d)' % (keyword, channel_id),
                         1:'select log_result,log_user,f1,log_time from log_create_role where log_user=\'%s\' and log_channel in(0,%d)' % (keyword, channel_id),
                         2:'select log_result,log_user,f1,log_time from log_create_role where log_result=\'%s\' and log_channel in(0,%d)' % (keyword, channel_id)}.get(key_type, '')
                         
            if query_sql != '':             
                cursor.execute(query_sql)
                player_list = cursor.fetchall()
            
            cursor.close()
        except Exception, e:
            print('player_query has error', e)
    
    parg = {}
    parg["list_server"] = list_server
    parg["server_id"] = server_id
    parg["keyword"] = keyword
    parg["player_list"] = player_list
    
    return render_to_response('channel/player_query.html', parg)

def question_list(request, user_id=0):
    channel_id = int(request.session.get('channel_id', '0'))
    
    channel = center_cache.get_channel_by_id(channel_id)
    server_id = int(request.GET.get('server_id', request.POST.get('server_id', '0')))
    if server_id == 0:
        server_id = int(request.session.get("server_id", '0'))
    
    list_server = center_cache.get_channel_server_list(channel.id)
    
    if server_id == 0 and len(list_server) > 0:
        server_id = list_server[0].id
    
    itemServerList = {}
    for item in list_server:
        itemServerList[item.id] = item.name
        
    if server_id > 0:
        server = center_cache.get_server_by_id(server_id)
   
    data_list = []
    user_id = request.GET.get('user_id', '')
    is_search_id = True
    if user_id != '':
        try:
            user_id = int(user_id)
        except:
            is_search_id = False
    
    #如果是角色名字查询
    if not is_search_id and server_id > 0:
        #因为player表分别在不同服务器下面所以要获取该服务器的链接信息
        the_db_config = json.loads(server.log_db_config)
        conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], port=the_db_config.get('port',3306),passwd=the_db_config['password'], db=the_db_config['db'], charset="utf8")
        conn.autocommit(True)
        cursor = conn.cursor()
        
        sql = "SELECT id FROM player_%d WHERE player_name LIKE \'%s%%\' " % (server_id, user_id)
        sql = filter_sql(sql)
        cursor.execute(sql)
        player_list = cursor.fetchall()
        
        if 0 < player_list.__len__():
            user_id = player_list[0][0]
    

    page_num = int(request.GET.get('page_num', '1'))
    page_size = 20
    total_record = 0
    total_page = 1
    if page_num < 1:
        page_num = 1

    query = None
    if user_id != '':
        if query != None:
            query = query & Q(post_user=user_id)
        else:
            query = Q(post_user=user_id)
    
    if server_id == 0:
        return HttpResponse('请选择服务器')
    
    if server_id > 0:
        if query != None:
            query = query & Q(server_id=server_id)
        else:
            query = Q(server_id=server_id)
    
    if query != None:
        query = query & Q(channel_id=channel_id)
    else:
        query = Q(channel_id=channel_id)
            
    if query == None:
        total_record = Question.objects.all().count()
        data_list = Question.objects.all()[(page_num - 1) * page_size:page_num * page_size]
    else:
        total_record = Question.objects.filter(query).count()
        if total_record > 0:
            data_list = Question.objects.filter(query)[(page_num - 1) * page_size:page_num * page_size]
    
    for item in data_list:
        if item.server_id > 0:
            item.serverName = itemServerList.get(item.server_id, '--')
        else:
            item.serverName = "--"

    if total_record > page_size:
        total_page = total_record / page_size
        if total_record % page_size > 0:
            total_page += 1
    
    parg = {}
    parg["channel"] = channel
    parg["server_id"] = server_id
    parg["user_id"] = user_id
    parg["list"] = data_list
    parg["list_server"] = list_server
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response("channel/question_list.html", parg, context_instance=RequestContext(request, processors=[channel_channelLoginStatus]))

def manage_question_list_user(request, user_id=0):
    channel_id = int(request.session.get('channel_id', '0'))
    channel = center_cache.get_channel_by_id(channel_id)
    
    server_id = 0#int(request.session.get("server_id",'0'))
    
    data_list = []
    user_id = int(user_id)
    page_num = int(request.GET.get('page_num', '1'))
    question_id = int(request.GET.get('question_id', '0'))
#    if int(question_id)>0:
#        select_question=Question.objects.get(id=question_id)
    
    page_size = 5
    total_record = 0
    total_page = 1
    if page_num < 1:
        page_num = 1
    if user_id > 0:
        if server_id > 0:
            total_record = Question.objects.filter(post_user__id=user_id, post_user__channel_key=channel.key, server_id=server_id).count()
            if total_record > 0:
                data_list = Question.objects.filter(post_user__id=user_id, post_user__channel_key=channel.key, server_id=server_id)[(page_num - 1) * page_size:page_num * page_size]
            
        else:
            total_record = Question.objects.filter(post_user__id=user_id, post_user__channel_key=channel.key).count()
            if total_record > 0:
                data_list = Question.objects.filter(post_user__id=user_id, post_user__channel_key=channel.key)[(page_num - 1) * page_size:page_num * page_size]
    else:
        if server_id > 0:
            total_record = Question.objects.filter(post_user__channel_key=channel.key, server_id=server_id).count()
            if total_record > 0:
                data_list = Question.objects.filter(post_user__channel_key=channel.key, server_id=server_id)[(page_num - 1) * page_size:page_num * page_size]
            
        else:
            total_record = Question.objects.filter(post_user__channel_key=channel.key).count()
            if total_record > 0:
                data_list = Question.objects.filter(post_user__channel_key=channel.key)[(page_num - 1) * page_size:page_num * page_size]
    
    list_server = Server.objects.filter(channel__id=channel.id)
    itemServerList = {}
    for item in list_server:
        itemServerList[item.id] = item.name
        
    for item in data_list:
        if item.server_id > 0:
            item.serverName = itemServerList.get(item.server_id, '--')
        else:
            item.serverName = "--"
            
        item.playerName = item.post_user.username
    
    if total_record > page_size:
        total_page = total_record / page_size
        if total_record % page_size > 0:
            total_page += 1
    
#    if int(question_id)>0:
#        Log._meta.db_table = 'log_create_role'
#        create_role_list=Log.objects.filter(log_user=user_id,log_server=select_question.server_id)
#        if len(create_role_list)>0:
#            create_role=create_role_list[0]
    if int(question_id) > 0:
        Log._meta.db_table = 'Users'
        selectUser = User.objects.get(id=user_id)
    
    parg = {}
    parg["selectUser"] = selectUser
    parg["list"] = data_list
    
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response('channel/question_user_list.html', parg);

def channel_login(request):
    username = request.COOKIES.get('username', '')
    password = ''
    
    parg = {}
    parg["username"] = username
    parg["password"] = password
    
    return render_to_response('channel/login.html', parg)


def channel_login_do(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    err_msg = ''
    channel = None
    if username != '':
        try:
            channels = Channel.objects.filter(username=username)
            if len(channels) > 0:
                channel = channels[0]
            else:
                err_msg = '账号不存在!'
                parg = {}
                parg["err_msg"] = err_msg
                return render_to_response('channel/login.html', parg)
        except:
            print('no channel ', username)
            
    if channel != None and channel.password == password:
        channel.logins += 1
        channel.last_ip = request.META.get('REMOTE_ADDR', '') 
        channel.last_time = datetime.datetime.now()
        channel.save(using='write')
        request.session["channel_id"] = channel.id
        request.COOKIES["username"] = username
        
        channel_channelLoginStatus(request)
        
        return HttpResponseRedirect("/channel")  
    else:
        err_msg = '账号或密码错误!'
    
    parg = {}
    parg["username"] = username
    parg["password"] = password
    parg["err_msg"] = err_msg
    
    return render_to_response('channel/login.html', parg)

def channel_logout(request):
    request.session.clear()
    return HttpResponseRedirect("/channel/login")


def change_password(request):
#    channel_id = int(request.session.get('channel_id','0'))
#    the_channel = None
#    if channel_id > 0 :
#        the_channel = Channel.objects.get(id=channel_id)
    return render_to_response('channel/change_password.html')


def change_password_do(request):   
    old_password = request.POST.get('old_password', '')
    new_password = request.POST.get('new_password', '')
    template_name = 'channel/change_password.html'
    channel_id = int(request.session.get('channel_id', '0'))
    err_msg = ''
    the_channel = None
    if channel_id > 0 :
        the_channel = center_cache.get_channel_by_id(channel_id)

    if the_channel and the_channel.password == old_password :
        the_channel.password = new_password
        the_channel.save(using='write')
        err_msg = u'密码已经修改成功!'
    else:
        err_msg = u'旧密码输入不正确!'
    
    parg = {}
    parg["err_msg"] = err_msg
    
    return render_to_response(template_name, parg)


def channel_change_server(request):
    serverId = request.GET.get("serverId", 0)
    #server= Server.objects.get(id=serverId)#
    request.session["server_id"] = serverId;
    return HttpResponse("");

def channel_pay_rank_list(request):
    channel_id = int(request.session.get('channel_id', '0'))
    user_id = request.GET.get("user_id", '')
    user_name = request.GET.get("user_name", "")
    sdate = request.GET.get("sdate", "")
    edate = request.GET.get("edate", "")
    server_id = int(request.GET.get('s', '0'))#server_id
    page_num = int(request.GET.get("page_num", "1"))
    is_search = request.GET.get("is_search", False)
    
    if user_id == "":
        user_id = "0"
    user_id = int(user_id)
    
    page_size = 50
    
    list_server = Server.objects.using('read').filter(channel__id=channel_id).order_by("create_time")
    
    if not is_search:
        return render_to_response("channel/pay_rank_list.html", locals())
    
    if server_id == 0:
        return HttpResponse('请选择服务器')
    
    channel = center_cache.get_channel_by_id(channel_id)
    
    query_where = " a.query_id != '' and a.query_id IS NOT NULL and a.pay_amount != 0 and a.channel_id=%s and a.pay_status=4" % channel.id
    
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
        
    
    query_where += " and a.server_id = %d " % server_id
    
    limit_str = "LIMIT 50"
    if user_id > 0:
        query_where += " and a.pay_user=%s" % user_id
        limit_str = ' '
    
     
    query_sql = "select a.pay_user,sum(a.pay_amount) total_amount from pay_action a where %s group by pay_user order by total_amount desc %s" % (query_where, limit_str)
    query_count = "select count(distinct pay_user) from pay_action a where %s" % query_where
    
    print "channel_pay_rank_list:"
    print query_count
    print query_sql
    
    cursor = connections['read'].cursor()
    cursor.execute(query_count)
    total_record = int(cursor.fetchone()[0])
    #raise Exception, query_sql
    list_record = []
    if total_record > 0:
        cursor.execute(query_sql)
        list_record = cursor.fetchall()
    
    #cursor.close()
    
    if user_id <= 0:
        user_id = ""
    
    parg = {}
    parg["channel"] = channel
    parg["list_server"] = list_server
    parg["server_id"] = server_id
    parg["user_id"] = user_id
    parg["sdate"] = sdate
    parg["edate"] = edate
    parg["list_record"] = list_record
    
    
    return render_to_response("channel/pay_rank_list.html", parg) 

def channel_channelLoginStatus(request):
#    channel_id = int(request.session.get('channel_id','0'))
#    channel = Channel.objects.get(id=channel_id)
#    
#    serverOptionList=Server.objects.filter(channel__id=channel.id)
#    
#    server_id=int(request.session.get("server_id",'0'))
#    if len(serverOptionList)>0 and server_id<=0:
#        request.session["server_id"]=serverOptionList[0].id
#        server_id=serverOptionList[0].id
#   
#    loginStatus={"serverOptionList":serverOptionList,"server_id":server_id}
#    return loginStatus
     return {}


def change_channel_server(request):
    channel_id = request.GET.get('channelId', '0')
    server_id = request.GET.get('serverId', '0')
    
#    print 'channel_id'
#    print 'server_id'

    #channel=Channel.objects.get(id=channel_id)
    #server= Server.objects.get(id=server_id)
    #if channel!=None and server!=None:
    request.session["channel_id"] = channel_id
    request.session["serverId"] = server_id

    #server1.channel.objects.all()
    
    parg = {}
    parg["channel_id"] = channel_id
    parg["server_id"] = server_id
    
    return render_to_response('index.html', parg)



