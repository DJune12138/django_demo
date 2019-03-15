#! /usr/bin/python
# -*- coding: utf-8 -*-
#日志接口


from django.db.models import Q
from django.shortcuts import render_to_response, HttpResponseRedirect, HttpResponse
from urls import Route
from util import datetime_to_str,convert_to_datetime,md5,trace_msg,datetime_or_str_to_timestamp,filter_sql

import json

import re,time


try:
    from models.channel import Channel
    from models.server import Server,Group
except:
    from models.center import Channel,Server,Group


app_key='fytx_123@#39823'

def check_sign(request):
    msg = 'sign error'
    post_params = request.raw_post_data or request.META.get('QUERY_STRING', '')
    sign = request.REQUEST.get('sign','')
    sign_str = '%s%s' % (re.sub('&sign=([^&]+)','',post_params) ,app_key)
    my_sign =  md5(sign_str)
    post_timestamp = int(request.REQUEST.get('_t','') or 0)
    print sign_str,sign,my_sign
    if ( int(time.time()) - post_timestamp ) >10:
        msg = 'time out'
    else:
        if sign == my_sign:
            msg = ''
    return msg

#统计数据接口
def statistic_data(request):
    select_sql = '''SELECT  log_user,DATE_FORMAT(`log_time`,'%Y-%m-%d %H:%i:%S'),`log_type`,`log_server`,`log_channel`,`log_tag`,`log_now`,`log_previous`,`log_data`,`log_result`
FROM log_statistic_result WHERE {column} BETWEEN {sdate} AND {edate}  and log_server in ({the_server_ids_str})'''
    rsp = {'tol_num':0,
          'data':[],
          'msg':''
          }

    try:
        msg = check_sign(request)
        if not msg:
            sdate = request.REQUEST.get('sdate','')
            edate = request.REQUEST.get('edate','')
            limit_type = request.REQUEST.get('type','')
            offset = request.REQUEST.get('offset','')
            limit = request.REQUEST.get('limit','')
            is_create_time = request.REQUEST.get('is_create_time','')
            
            limit_type_list = limit_type.split(',')
            limit_type_list = [ str(x) for x in limit_type_list if x]

            
            if sdate and  edate and offset and limit :
                offset = int(offset)
                limit = int(limit)
                convert_to_datetime(sdate)
                convert_to_datetime(edate)
                limit = 50000 if limit>50000 else limit
                column_name = 'log_time'
                
                if is_create_time: #如果是按创建时间来的话就转为时间戳,log_user字段是创建的时间戳
                    column_name = 'log_user'
                    sdate = datetime_or_str_to_timestamp(sdate)
                    edate = datetime_or_str_to_timestamp(edate)
                else:
                    sdate = "'%s'" % sdate
                    edate = "'%s'" % edate
                    
                    
                    
                the_server_ids = [ str(x) for x in Server.objects.all().values_list('id',flat=True)]
                the_server_ids_str = ','.join(the_server_ids)
                    
                select_sql = select_sql.format(column=column_name,sdate=sdate,edate=edate,the_server_ids_str=the_server_ids_str)

                select_sql = select_sql.format(column=column_name,sdate=sdate,edate=edate)
                if limit_type_list:
                    select_sql = '%s AND log_type in (%s)' % (select_sql,','.join(limit_type_list))
                select_sql = '%s LIMIT %d,%d' % (select_sql,offset,limit)
                conn = Server.get_conn(0)
                cur = conn.cursor()
                select_sql = filter_sql(select_sql)
                print select_sql
                cur.execute(select_sql)
                rsp['data'] = cur.fetchall()
                rsp['tol_num'] = len(rsp['data'])
                conn.close()
        rsp['msg'] = 'sign error'
    except:
        rsp['msg'] = trace_msg()
        print  rsp['msg']

    return HttpResponse(json.dumps(rsp,ensure_ascii=False))


#平台渠道接口
def agent_channel(request):
    r = {'code':-1,'msg':'','data':[]}
    if 1:
        agnet_dict = {}
        channel_list = Channel.objects.all().values('agent_name','channel_key','name','id')
        for c in channel_list:
            agnet_dict.setdefault(c['agent_name'],[])
            if c not in agnet_dict[c['agent_name']]:
                agnet_dict[c['agent_name']].append(c)
        r['code'] = 0
        r['data'] = agnet_dict
    else:
        r['msg'] = 'sign err!'
    return HttpResponse(json.dumps(r,ensure_ascii=False))

#分区服务器接口
def group_server(request):
    r = {'code':-1,'msg':'','data':[]}
    if 1:
        group_dict = {}
        group_list = Group.objects.prefetch_related('server').all()
        for g in group_list:
            server_list = g.server.all()
            
            group_dict.setdefault(g.name,[])
            for s in server_list:
                server_dict  = {'id':s.id,
                                'name':s.name,
                                'create_time':datetime_to_str(s.create_time)
                                }
                group_dict[g.name].append(server_dict)

        r['code'] = 0
        r['data'] = group_dict
    else:
        r['msg'] = 'sign err!'
    return HttpResponse(json.dumps(r,ensure_ascii=False))



