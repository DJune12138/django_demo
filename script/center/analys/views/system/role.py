#! /usr/bin/python
# -*- coding: utf-8 -*-
# 
# 角色权限相关
#
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================

from urls.AutoUrl import Route
from views.system.menu import MenuTree
from views.base import notauth
from models.menu import Menu
from models.admin import Role, Resource
from models.center import Channel, Server, Group
from util import trace_msg
from views.widgets import (get_group_servers_dict,
                           get_agent_channels_dict
                            )

@Route()
def role_list(request):
    '''角色列表
    '''
    if request.admin.is_manager:
        list_record = request.admin.get_resource('role')
    return render_to_response('system/role_list.html', locals())


@Route()
def role_edit(request, id=0):
    '''角色编辑
    '''
    id = int(request.REQUEST.get('id', '0'))
    is_copy =  request.REQUEST.get('copy','')
    resource = {}
    if id :
        role = request.admin.get_resource('role').get(id=id)
        if is_copy:
            role.name = '%s-copy' % role.name
    else:
        role = Role()
        role.id = id
    roles = request.admin.get_resource('role').exclude(id=role.id)
    menus = MenuTree(request.admin.get_resource('menu').all().order_by('parent_id')).get_list_record()
    agent_channels_dict = get_agent_channels_dict(request)
    group_servers_dict = get_group_servers_dict(request)
    platforms =  request.admin.get_resource('platform')
    return render_to_response('system/role_edit.html',locals())


@Route()
def role_save(request, id=0):
    '''角色保存
    '''
    try:
        id = int(request.REQUEST.get('id', '0'))
        if id > 0:
            role = request.admin.get_resource('role').get(id=id)
        else:
            role = Role()
        role.set_attr('name',request.REQUEST.get('name',''),null=False)
        role.set_attr('remark',request.REQUEST.get('remark',''),null=True)
        role.set_attr('type',request.REQUEST.get('type',Role.RoleType.NORMAL),null=False)
        role.create_resource('menu',request.REQUEST.getlist('menu_id'))
        role.create_resource('channel',request.REQUEST.getlist('channel_id'))
        role.create_resource('agent',request.REQUEST.getlist('agent_id'))
        role.create_resource('server',request.REQUEST.getlist('server_id'))
        role.create_resource('server_group',request.REQUEST.getlist('server_group_id'))
        role.create_resource('platform',request.REQUEST.getlist('platform_id'))
        manager_role_ids = [] # 只有管理员才能管理其他角色
        if int(role.type) == Role.RoleType.ADMIN:
            manager_role_ids = request.REQUEST.getlist('manager_role_id')
        role.create_resource('role',manager_role_ids)
        role.save()
        for r in request.admin.get_roles().filter(type=Role.RoleType.ADMIN):
            r.add_resource_member('role',role.id)
            
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html', locals())

@Route()
def role_remove(request, id=0):
    '''删除角色
    '''
    try:
        role_ids = request.REQUEST.getlist('id')
        if role_ids:
            for r in request.admin.get_resource('role').filter(id__in=role_ids):
                    r.delete(using='write')
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html',locals())


