# -*- coding: utf-8 -*-
#
#管理员相关
#
#django 常用导入
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect,render
from django.views.generic import ListView,View
from django.template import loader, RequestContext
#==========================================

from urls.AutoUrl import Route
from util import trace_msg
from models.admin import Admin, Role
from models.center import Channel, Server
from django.http import HttpResponseRedirect

import datetime


@Route()
def admin_list(request):
    '''管理员列表
    '''
    
    list_record = request.admin.get_manageable_admin()
    return render_to_response('system/admin_list.html', locals())

@Route()
def admin_edit(request, admin_id=0):
    '''管理员编辑
    '''
    admin_id = admin_id or int(request.REQUEST.get('id', '0'))
    if admin_id :
        model = request.admin.get_manageable_admin().get(id=admin_id)
        model.password = ''
    else:
        model = Admin()
        model.id = admin_id
    return render_to_response('system/admin_edit.html', locals())


@Route()
def admin_save(request, admin_id=0):
    '''管理员保存
    '''
    try:
        admin_id = int(request.REQUEST.get('id', '0'))
        if admin_id:
            the_admin = request.admin.get_manageable_admin().get(id=admin_id)
        else:
            the_admin = Admin()
        username = request.REQUEST.get('username', '')
        if not admin_id and  Admin.objects.filter(username=username).exists():
            err_msg = '已存在相同登录名[%s]' % username
        else:
            the_admin.set_attr('username',request.REQUEST.get('username', '').strip(),null=False)
            the_admin.set_attr('alias',request.REQUEST.get('alias', '').strip(),null=False)
            the_admin.set_attr('password',request.REQUEST.get('password', '').strip(),the_admin.md5_password,null=False)
            role_ids = request.REQUEST.getlist('role_id')
            if role_ids:
                the_admin.set_attr('role_ids',request.REQUEST.getlist('role_id'),null=True)
                the_admin.save()
            else:
                err_msg = '至少选择一个角色!'

    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html',locals())
 
 
@Route()
def admin_remove(request, admin_id=0):
    '''删除管理员
    '''
    try:
        is_recover = request.GET.get('recover', False)
        admin_ids = request.REQUEST.getlist('id')
        if admin_ids:
            the_admins = request.admin.get_manageable_admin().filter(id__in=admin_ids)
            for the_admin in the_admins:
                    if not is_recover:
                        the_admin.status = Admin.Status.DELETED
                    else:
                        the_admin.status = Admin.Status.NORMAL
                    the_admin.save()
    except Exception,e:
        err_msg = trace_msg()    
    return render_to_response('feedback.html',locals())
 

@Route()
def admin_edit_self(request):
    '''管理员编辑自己
    '''
    the_admin = request.admin
    if request.method == 'POST':
        old_password = request.POST.get('old_password','')
        new_password = request.POST.get('new_password','')
        new_password2 = request.POST.get('new_password2','')
        
        if not new_password or not new_password2 or not old_password:
            err_msg = '密码都不能为空!'
        elif new_password != new_password2:
            err_msg = '新密码两次不一样!'
        else:
            if the_admin.is_agent:
                from models.channel import Agent
                agent_objs = Agent.objects.filter(username=the_admin.username)
                if agent_objs:
                    the_admin = agent_objs[0]
            else:
                old_password = the_admin.md5_password(old_password)
                new_password = the_admin.md5_password(new_password)
                
            if the_admin.password == old_password:
                the_admin.password = new_password
                the_admin.save(using='write')
                #from views import logout
                #return logout(request)
                return render_to_response('feedback.html',locals())
            else:
                err_msg = '旧密码输入不正确!'
    return render_to_response('system/admin_edit_self.html', locals())



