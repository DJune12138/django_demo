#! /usr/bin/python
# -*- coding: utf-8 -*-
#
#主页,登录相关
#
#django 常用导入
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================


import sys
import datetime, time
from views.base import notauth
from django.core.serializers import serialize,deserialize
from models.admin import Admin, Role 
from models.channel import Agent,Channel
from util import trace_msg
from util import TIMEFORMAT,DATETIMEFORMAT
import traceback
from urls.AutoUrl import Route
from settings import TITLE as Title
@Route()
def doc(request):
    return render_to_response('doc.html', locals()) 

@Route()
def index(request):
    '''主页
    '''
    list_menu = request.admin.get_resource('menu').filter(is_show=1).order_by('order')
    now_timestamp = int(time.time())
    TITLE = Title
    return render_to_response('index.html', locals())


@Route()
def home(request):
    from models.platform import PlatForm
    platform_list = request.admin.get_resource('platform')
    return render_to_response('home.html',locals())

class LoginError(Exception):pass



def check_login_status(request):
    '''登录状态检测
    '''
    now = datetime.datetime.now()
    err_msg = ''
    err_count = request.session.setdefault('err_count', 0)
    max_count = 10
        
    if err_count >= max_count:
        lock_time = request.session.setdefault('lock_time',now + datetime.timedelta(minutes=max_count))
        if now < lock_time:
            request.session.clear()
            return '错误登录次数过多,请在  %s 后再登录！' % lock_time.strftime(TIMEFORMAT)
        else:
            del request.session['err_count']
            del request.session['lock_time']
    
    if request.POST.get('verify', '') != request.session.get('verify',''):#验证码
            return '验证码错误 !'   



@Route('^login$')
@notauth
def login(request):
    '''登录
    '''
    now = datetime.datetime.now()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('passowrd', '').strip()
        request.COOKIES["username"] = username

        try:
            login_status_err_msg = check_login_status(request)
            if login_status_err_msg:
                raise LoginError(login_status_err_msg)
                 
            if username == password :
                raise  LoginError( '请联系管理员修改密码!')
            if not username or not password :
                raise  LoginError( '账号或密码为空!')
            the_admins = Admin.objects.filter(username=username)
            if the_admins:
                the_admin = the_admins[0]
            else:
                raise  LoginError( '%s 账户不存在!' % username)
            if the_admin.status != Admin.Status.NORMAL:
                raise  LoginError( '账户已  %s' % the_admin.get_status_display())
            if the_admin.md5_password() == the_admin.md5_password(password):
                request.session.clear()
                request.session['admin_id'] = the_admin.id
                the_admin.login_count += 1
                the_admin.last_time = now
                the_admin.last_ip = request.real_ip
                the_admin.session_key = request.session.session_key
                the_admin.save()
                redirect_url = request.REQUEST.get('from_url','/index')
                return HttpResponseRedirect(redirect_url)
            else:
                raise  LoginError( '密码错误!')
        except LoginError,err_msg:   
            err_msg = err_msg
            request.session['err_count'] = request.session.get('err_count',0) +1
        
    return render_to_response('login.html', locals())



@Route('^logout$')
@notauth
def logout(request):
    '''登出
    '''
    agent_id = request.session.get('agent_id', None)    #渠道登录的
    request.session.clear()
    if agent_id:
        return HttpResponseRedirect("/channel/login")
    return HttpResponseRedirect("/login")


@Route('^channel/login')
@notauth
def channel_login(request):
    anget_name = '渠道'
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('passowrd', '').strip()
        request.COOKIES["username"] = username
        
        try:
            login_status_err_msg = check_login_status(request)
            if login_status_err_msg:
                raise LoginError(login_status_err_msg)
            if username == password :
                raise  LoginError( '请联系管理员修改渠道密码!')
            if not username or not password :
                raise  LoginError( '账号或密码为空!')
            the_admins = Agent.objects.filter(username=username)
            if the_admins:
                the_admin = the_admins[0]
            else:
                raise  LoginError( '%s 账户不存在!' % username)

            if the_admin.password == password:
                request.session.clear()
                request.session['agent_id'] = the_admin.id
                the_admin.login_count += 1
                the_admin.last_time = datetime.datetime.now()
                the_admin.last_ip = request.real_ip
                the_admin.session_key = request.session.session_key
                the_admin.save()
                redirect_url = request.REQUEST.get('from_url','/index')
                return HttpResponseRedirect(redirect_url)
            else:
                raise  LoginError( '密码错误!')
        except LoginError,err_msg:   
            err_msg = err_msg
            request.session['err_count'] = request.session.get('err_count',0) +1
    return render_to_response('login.html', locals())

