# -*- coding: utf-8 -*-
from analys.cache.memcached_util import get_value as cache_get_value, CACHE_TYPE
from analys.models.center import Server, Group, Channel
from analys.models.admin  import Admin

from django.db.models import Q

MASTER_SERVER_FLAG = 'master_server_id'

def get_value(key, mc_util, get_data, *args):
    return cache_get_value(key, CACHE_TYPE.CENTER_CACHE, mc_util, get_data, *args)
    
def get_server_list(group_id = 0, mc_util = None):
    key = 'SERVER_LIST_%s' % group_id
    expre = lambda args:Server.objects.using('read').filter(~Q(status = 1)).order_by('-status')
    if group_id > 0 :
        if 0 < get_server_count():  
            expre = lambda args:get_group(group_id, mc_util).server.all()
        else:
            expre = lambda args:None
    return get_value(key, mc_util, expre, group_id)

def get_channel_server_list(channel_id, mc_util = None):
    key = 'CHANNEL_%s_SERVER_LIST' % channel_id
    return get_value(key, mc_util, lambda args:Server.objects.using('read').filter(channel__id=channel_id))

def get_server_list_by_status(status_list, mc_util=None):
    status_list.sort()
    key = 'SERVER_LIST_%s' % (reduce(lambda x,y:'%s%s'%(x,y), status_list))
    expre = lambda args:Server.objects.using('read').filter(Q(status__in = status_list)).order_by('id')
    return get_value(key, mc_util, expre)

#获取除 有字服的服务器列表
def get_master_server_list(group_id=0, mc_util = None):
    key = 'MASTER_SERVER_LIST_%s' % group_id
    expre = lambda args:__get_master_server_list(args[0], args[1])
    return get_value(key, mc_util, expre, group_id, mc_util)

def __get_master_server_list(group_id, mc_util):
    result_list = []
    server_list = get_server_list(group_id, mc_util)
    for server in server_list:
        if '' == get_server_config(server.id, MASTER_SERVER_FLAG, '', mc_util):
            result_list.append(server)
    return result_list

def get_server_by_id(server_id, mc_util = None):
    key = 'SERVER_ID_%s' % server_id
    return get_value(key, mc_util, lambda args: _get_server(server_id, mc_util))
 
def get_user_list_by_role_id(role_id, mc_util = None):
    key = 'ADMIN_LIST_BY_ROLE_%s' % role_id
    return get_value(key, mc_util, lambda args:Admin.objects.using('read').filter(role__id = role_id))

import json
def get_server_config(server_id, key, default, mc_util = None):
    server = get_server_by_id(server_id, mc_util)
    result = default
    if None == server:
        return default
    try:
        if server.json_data != '':
            server.json_data = '{%s}' % server.json_data
            cfg = json.loads(server.json_data)
            result = cfg.get(key, default)
        else:
            return default
    except Exception, ex:
        print '<<center_cache get_server_config >>:', ex
        return default 
    return result
    
    
def _get_server(server_id, mc_util = None):
    server_list = get_server_list(0, mc_util)
    result = None
    for item in server_list:
        if item.id == server_id:
            result = item
            break
    
    if None == result:
        result = Server.objects.filter(id = server_id)
        if 0 != result.__len__():
            result = result[0]
    
    return result
            
def get_cache_server_list_group_by(mc_util = None):
    key = 'SERVER_LIST_GROUP_BY'
    return get_value(key, mc_util, lambda args: _get_server_list_group_by(args[0]), mc_util)
        
def _get_server_list_group_by(mc_util):
    group_list = get_group_list(mc_util)
    result = []
    server_dic = {}
    for group in group_list:
        server_list = []
        group_server_list = get_group_server_list(group.id, mc_util)
        if 0 != group_server_list:
            for server in group_server_list:
                if -1 == server_dic.get(server.id, -1):
                    server_dic[server.id] = server
                    server_list.append(server)
            result.append(server_list)
            
    return result

def get_master_server_dict_group_by(mc_util = None):
    key = 'MASTER_SERVER_LIST_GROUP_BY'
    return get_value(key, mc_util, lambda args: _get_master_server_dict_group_by(args[0]), mc_util)

def _get_master_server_dict_group_by(mc_util):
    group_list = get_group_list(mc_util)
    result = {}
    server_dic = {}
    for group in group_list:
        server_list = []
        group_server_list = get_group_server_list(group.id, mc_util)
        if 0 != group_server_list.__len__():
            for server in group_server_list:
                if -1 == server_dic.get(server.id, -1):
                    if '' == get_server_config(server.id, MASTER_SERVER_FLAG, '', mc_util):
                        server_dic[server.id] = server
                        server_list.append(server)
            result[group] = (server_list)
            
    return result

def get_user_server_list(the_user, mc_util = None):
    key = 'USER_%s_SERVER_LIST' % the_user.id
    return get_value(key, mc_util, lambda args:args[0].server.all().order_by('create_time'), the_user)

def get_server_count(mc_util=None):
    key = 'SERVER_COUNT'
    return get_value(key, mc_util, lambda args:Server.objects.all().count())


def get_group(group_id=0, mc_util=None):
    key = 'GROUP_%s' % group_id
    return get_value(key, mc_util, lambda args:Group.objects.get(id=args[0]), group_id)

def get_group_list(mc_util = None ,iscache=True):
    key = 'GROUP_LIST'
    method = lambda args:Group.objects.all()
    return get_value(key, mc_util, method) if iscache else method(0)


def get_group_server_list(group_id, mc_util = None):
    group = get_group(group_id)
    key = 'GROUP_%s_SERVER' % group_id
    return get_value(key, mc_util, lambda args:args[0].server.all(), group)

def get_channel_list(mc_util = None,iscache=True):
    key = 'CHANNEL_LIST'
    method =lambda args: Channel.objects.all().order_by('name')
    return get_value(key, mc_util, method) if iscache else method(0)

def get_channel_by_id(channel_id, mc_util = None):
    key = 'CHANNEL_ID_%s' % channel_id
    return get_value(key, mc_util, lambda args:_get_channel(channel_id, mc_util))

def _get_channel(channel_id, mc_util):
    channel_list = get_channel_list(mc_util)
    result = None
    for item in channel_list:
        if channel_id == item.id:
            result = item
            break
    if result == None:
        result = Channel.objects.get(id= channel_id)
    return result
        
def get_user_channel_list(the_user, mc_util = None):
    key = 'USER_%s_CHANNEL_LIST' % the_user.id
    return get_value(key, mc_util, lambda args:args[0].channel.all().order_by('name'), the_user)


def get_user_by_id(model_id, mc_util = None):
    model_id = int(model_id)
    key = 'USER_%s' % model_id
    return get_value(key, mc_util, lambda args:Admin.objects.using('read').get(id=model_id))
    
def get_user_menu_list(user_id, mc_util = None):
    key = 'USER_MENU_LIST_%s' % user_id
    the_user = get_user_by_id(user_id, mc_util)
    return get_value(key, mc_util, lambda args: the_user.role.menu.all())
    
    
