#! /usr/bin/python
# -*- coding: utf-8 -*-
#游戏服接口


from django.db.models import Q
from django.shortcuts import render_to_response, HttpResponseRedirect, HttpResponse
from util.http import http_post

import datetime, json, time
try:
    from models.server import  Server,Group
except:
    from models.center import  Server,Group
from views import log
from views.base import md5,notauth
import json
import traceback
from urls import Route
from util import datetime_to_str

from settings import PREFIX

IgnoreServerIdList = []
IgnoreServerNameList = ['测试','測試','test','跨服','审核','審核','跨服','流水','后备','备用']
def filter_server(s):
    if s.id in IgnoreServerIdList or  s.create_time > datetime.datetime.now() or s.status==-1 \
                or filter(lambda x:x in s.name.lower(),IgnoreServerNameList).__len__()>0 :
        return True
    return False

@Route('^interface/server_list[/]?$') 
@notauth
def server_list(request,builtin=False):
    '''游爱自动备份接口
    [
    { 
‘unit_agent_name’: [统一平台名称],    // 中央后台统一的服所属运营平台名称，如未设置统一平台名称，该服信息更新时，中央后台的服信息将不更新
‘agent_name’: [平台名称],    // 服所属运营平台名称
        ‘server_name’: [单服标识],    // 单服标识(如：S1 S2)
        ‘chinese_server_name’: [单服中文标识],    // 单服中文标识(如：人剑合一)，没有可以设置与单服标识一样
        ‘api_url’: [单服网址],    // 单服网址
        ‘open_time’: [开服时间]    // 具体到分钟，格式：2011-10-10 02:30
        ‘close_time’: [关服时间]    // 具体到分钟，格式：2012-05-10 02:30
},
    … // 更多服
]

    '''
    sign_key = 'L9cnKuDxGJRPVeUIZQHNA40eozVAZqX7'
    keys = ['sign','unixtime','method']
    _p = lambda x,y='':request.POST.get(x,request.GET.get(x,y))
    sign,unixtime,method =  [  _p(k,'') for k in keys]
    server_list = []
    if sign and unixtime and method:
        if sign.encode('utf-8') == md5('%s%s%s'%(sign_key,unixtime,method)):
            
            for s in Server.objects.all():
                if filter_server(s):
                    continue

                server = {}
                try:
                    s_j_data = json.loads(s.log_db_config)
                    server['unit_agent_name'] = 'mixed'#s_j_data.get('unit_agent_name','')
                    server['agent_name'] = 'mixed'#s_j_data.get('agent_name','')
                    server['server_name'] = '%s%s' % (PREFIX,s.id) #s_j_data.get('server_name','')
                    server['chinese_server_name'] = s.name
                    server['api_url'] = s_j_data.get('api_url','')
                    server['open_time'] = datetime_to_str(s.create_time)
                    server['close_time'] = ''#s_j_data.get('close_time','')
                    server_list.append(server)
                except Exception,e:
                    traceback.print_exc()
           
        else:
            _r = 'Signature Invalid'
    else:
        _r = 'Not Modified'
    if builtin:return server_list
    _r = json.dumps(server_list,ensure_ascii=False)
    return HttpResponse(_r)
    
@Route('^interface/server_list_cn[/]?$') 
@notauth
def server_list_cn(request):
    ios_interface_url = 'http://ios.server.fytxonline.com/interface/server_list?method=server_list&unixtime=1395300340&sign=16a94d89d641f5b89e11b6445fa69eb9'
    cn_server_list = server_list(request,True)
    ios_server_list = []
    try:
        _r = http_post(ios_interface_url)
        if _r:
            ios_server_list = json.loads(_r)
        cn_server_list += ios_server_list
    except Exception,e:
         pass
    _r = json.dumps(cn_server_list,ensure_ascii=False)
    return HttpResponse(_r)