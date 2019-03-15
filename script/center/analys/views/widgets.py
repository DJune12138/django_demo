# -*- coding: utf-8 -*-
#
# 输入部件
#
# django 常用导入
# =========================================
from django.core.urlresolvers import reverse
from django.db import connection, connections
from django.utils.html import conditional_escape
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, HttpResponseRedirect
from django.views.generic import ListView, View
# ==========================================

from django.core.serializers import serialize, deserialize
from django.utils.datastructures import SortedDict
import json

from models.log import DictDefine, DictValue
from models.channel import Channel, Agent
from models.server import Server, Group

import logging

from urls.AutoUrl import Route
from util.constant import tab_name_id
from views.base import notauth

# 日志记录
_logger = logging.getLogger(__file__)


def get_group_servers_dict(request, group_id=0, get_server_list=False):
    '''服务器分区列表获取，配合widget/group_server.html
    '''

    group_servers_dict = SortedDict()

    exclude_list = set()

    if group_id:
        groups = request.admin.get_resource('server_group').filter(id=group_id)  # .prefetch_related('server')
    else:
        groups = request.admin.get_resource('server_group').all()  # .prefetch_related('server')

    other_servers = request.admin.get_resource('server').prefetch_related('group_set')

    not_group_set = set()
    has_add_group_server_set = set()
    for s in other_servers:
        g_s_list = s.group_set.all()

        if g_s_list:
            for g in g_s_list:
                if g in groups:
                    group_servers_dict.setdefault(g, set())
                    group_servers_dict[g].add(s)
                    has_add_group_server_set.add(s)
                else:
                    not_group_set.add(s)
        else:
            not_group_set.add(s)
        exclude_list.add(s)

    if not_group_set:
        not_group = Group()
        not_group.id = 0
        not_group.name = '其他'
        group_servers_dict[not_group] = not_group_set - has_add_group_server_set

    if get_server_list:
        server_list = exclude_list
        return group_servers_dict, server_list
    else:
        return group_servers_dict


def groups_servers(request):
    """业务需求，把搜索栏的服务器按照服务器分组来排列显示"""

    m = eval(DictValue.objects.using('read').get(dict_id=tab_name_id).json_dict)
    groups_servers_dict = dict()
    for num, name in m.items():
        lis = list()
        lis.append(num)
        lis.append(name)
        tup = tuple(lis)
        servers_list = request.admin.get_resource('server').filter(tabId=int(num))
        servers = list()
        for server in servers_list:
            servers.append(server)
        groups_servers_dict[tup] = servers
    return groups_servers_dict


def get_group_server_list(request, group_id=0, get_server_ids=False):
    group_servers_dict, server_ids = get_group_servers_dict(request, group_id=0, get_server_ids=True)
    group_list = group_servers_dict.keys()
    server_set = set()
    for g, server_list in group_servers_dict.iteritems():
        if g.id == group_id:
            for s in server_list:
                server_set.add(s)
    return group_servers_dict, group_list, server_set


def get_agent_channels_dict(request, get_channel_list=False):
    '''渠道接口
    '''
    agent_channels_dict = {}

    exclude_list = set()
    channel_angets = request.admin.get_resource('channel').prefetch_related('agent_set')

    other_agent = Agent()
    other_agent.id = 0
    other_agent.name = ''
    other_agent.alias = '其他'
    agent_channels_dict[other_agent] = []

    for c in channel_angets:
        c_a_list = c.agent_set.all()
        if c_a_list:
            for a in c_a_list:
                agent_channels_dict.setdefault(a, [])
                agent_channels_dict[a].append(c)
        else:
            agent_channels_dict[other_agent].append(c)
        exclude_list.add(c)

    if not agent_channels_dict[other_agent]:
        agent_channels_dict.pop(other_agent)

    if get_channel_list:
        channel_list = exclude_list
        return agent_channels_dict, channel_list
    else:
        return agent_channels_dict


def get_group_channels_dict():
    """在分区等业务重构后，渠道不再隶属于平台，改为隶属于分区"""

    # 查出分区的查询集
    groups = Group.objects.all()

    # 查出每个分区对应的渠道查询集，并组成字典
    dic = {}
    for group in groups:
        channels = group.channel.all()
        dic[group] = channels

    # 返回字典
    return dic
