#! /usr/bin/python
# -*- coding: utf-8 -*-
# 
# 资源
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
from views.base import notauth

from models.admin import Role, Resource
from models.center import Channel, Server, Group
from models.resource import Resource
from util import trace_msg


@Route()
def resource_list(request):
    '''资源列表
    '''
    list_record = Resource.objects.all()
    return render_to_response('system/resource_list.html',locals())


@Route()
def resource_edit(request, resource_id=0):
    '''资源编辑
    '''
    resource_id = int(request.REQUEST.get('resource_id', '0'))
    resource = {}
    if resource :
        resource = request.admin.get_resource('role').get(id=resource_id)
    else:
        resource = Resource()
        resource.id = resource_id
    return render_to_response('system/resource_edit.html', locals())


@Route()
def resource_save(request, role_id=0):
    '''资源保存
    '''
    try:
        role_id = int(request.REQUEST.get('role_id', '0'))
        if role_id > 0:
            role = request.admin.get_resource('role').get(id=role_id)
        else:
            role = Role()
        role.set_attr('name',request.REQUEST.get('name',''),null=False)
        role.set_attr('type',request.REQUEST.get('type','0'),null=False)
        role.create_resource('menu',request.REQUEST.getlist('menu_id'))
        role.create_resource('channel',request.REQUEST.getlist('channel_id'))
        role.create_resource('server',request.REQUEST.getlist('server_id'))
        role.create_resource('servergroup',request.REQUEST.getlist('server_group_id'))
        role.create_resource('role',request.REQUEST.getlist('manager_role_id'))
        role.save()
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html', locals())


@Route()
def resource_remove(request, role_id=0):
    '''删除资源
    '''
    try:
        resource_ids = request.REQUEST.getlist('resource_id')
        for r in Resource.objects.filter(id__in=resource_ids):
                r.delete(using='write')
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html',locals())

@Route()
def resource_get_role(request):
    '''获取拥有这个资源id的角色
    '''
    resource_name = request.REQUEST.get('resource_name','')
    resource_member_id = int(request.REQUEST.get('id','0'))
    template_name = request.REQUEST.get('template_name','system/resource_list.html')
    if resource_name:
        resources = []
        for r in request.admin.get_resource_obj().filter(name=resource_name):
            print r
        print resources
        resource_roles = Role.objects.filter(resource__id__in=resources)
        print resource_roles
    return HttpResponse('')
    


