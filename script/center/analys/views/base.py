#! /usr/bin/python
# -*- coding: utf-8 -*-
#
#视图的基本
#
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================

from django.db.models import Q
from models.admin import Admin
from models.channel import Channel
from models.log import Log
from models.server import Server
from util import trace_msg
from settings import TEMPLATE_DIRS, DATABASES,STATIC_ROOT
import hashlib, datetime, json, MySQLdb, urllib, os,re

import functools
def notauth(obj):
    '''免登录认证标记
    '''
    @functools.wraps(obj)
    def warp_func(request,*a,**kw):
        func = obj
        if hasattr(obj,'as_view'):
            func = apply(obj.as_view)
        return func(request,*a,**kw)
    setattr(warp_func,'notauth',True)
    return warp_func



def json_response(func):
    '''返回json处理
    '''
    @functools.wraps(func)
    def json_warp_func(*args,**kwargs):
        _r = {"code":-1,"msg":"","content":[]}
        response = func(*args,**kwargs)
        if isinstance(response,(tuple,list)):
            response_len = len(response)
            _r["code"] = response[0]
            if response_len>=2:
                _r["msg"] = response[1]
            if response_len>=3:
                _r["content"] = response[2]  
            response = HttpResponse(json.dumps(_r, ensure_ascii=True))
        elif isinstance(response,dict):
            _r.update(response)
            response = HttpResponse(json.dumps(_r, ensure_ascii=True))
        return response
    
    return json_warp_func

class BaseView(View):
    '''基本视图
    '''
    
    deny_method_names = ['get', 'init','render_to_response','HttpResponse'] +\
                        ['post', 'put', 'delete', 'head', 'options', 'trace']
                        
    def get(self,request,path,*args,**kwargs):
        
        self._magic_prepare()
        path = self.filter_uri(path)

        if path not in self.deny_method_names:
            method = getattr(self,path,None)
            if hasattr(method, '__call__'):
                self.initialize()
                return method()
        return self._default()
    
    def _default(self):
        return HttpResponse('reject this view!')
    
    def  initialize(self):
        '''初始化
        '''
        pass
    
    def _magic_prepare(self):
        self.get_arguments = self.request.REQUEST.getlist
        self.get_argument = self.request.REQUEST.get
    
    def post(self,*args,**kwrags):return self.get(*args,**kwrags)
    def put(self,*args,**kwrags):return self.get(*args,**kwrags)
    def delete(self,*args,**kwrags):return self.get(*args,**kwrags)
    def options(self,*args,**kwrags):return self.get(*args,**kwrags)
    def trace(self,*args,**kwrags):return self.get(*args,**kwrags)
    
    def filter_uri(self,path):
        return path.strip('_')
    
    def render_to_response(self,template_name,dict_value,*args,**kwargs):
        dict_value.update({"request":self.request})
        return render_to_response(template_name,dict_value,*args,**kwargs)
    
    def HttpResponse(self,*args,**kwargs):
        return HttpResponse(*args,**kwargs)
    
    
    @classmethod
    def as_view(cls,*args,**kw):
        return super(BaseView,cls).as_view(*args,**kw)
    


class OperateLogManager(object):
    @staticmethod
    def save_operate_log(admin_id, msg, url, ipaddress, log_data = 0):
        tmp = msg
        try:
            tmp = tmp.decode('utf-8')
            msg = tmp
        except:
            pass
        msg2 = u''
        msg3 = u''
        msg4 = u''
        
        msg_len = msg.__len__()
        
        msg1 = msg
        
        
        if msg_len >= 99:
            msg1 = msg[:99]
            msg2 = msg[99:99+99]
        if msg_len >= 99*2:
            msg3 = msg[99*2:99*3]
        if msg_len >= 99*3:
            msg4 = msg[99*3:99*4]
        if msg_len >= 99*4:
            msg5 = msg[99*4:99*5]
        if msg_len >= 99*5:
            msg6 = msg[99*5:99*6]
             
        #写登录日志
        save_log('operate', 29, 0, 0, admin_id, log_data, 0, msg1, url, ipaddress, msg2, msg3, msg4)
            
    @staticmethod
    def get_request_ipAddress(request):
        return request.META['REMOTE_ADDR']

def quick_save_log(log_name, log_type, log_server, log_channel, log_user, log_data, log_result, msg):
    
    msg_len = msg.__len__()
    f1 = msg
    f2=''
    f3=''
    f4=''
    f5=''
    f6=''
    if msg_len >= 99:
        f1 = msg[:99]
        f2 = msg[99:99+99]
    if msg_len >= 99*2:
        f3 = msg[99*2:99*3]
    if msg_len >= 99*3:
        f4 = msg[99*3:99*4]
    if msg_len >= 99*4:
        f5 = msg[99*4:99*5]
    if msg_len >= 99*5:
        f6 = msg[99*5:99*6]
    
    save_log(log_name, log_type, log_server, log_channel, log_user, log_data, log_result, f1, f2, f3, f4, f5, f6)
    

def save_log(log_name, log_type, log_server, log_channel, log_user, log_data, log_result, f1,f2,f3,f4,f5,f6):
    code = 1
    try:
        Log._meta.db_table = 'log_%s' % log_name
        log = Log()
        log.log_type = log_type
        log.log_server = log_server
        log.log_channel = log_channel 
        log.log_user = log_user
        log.log_data =  log_data
        log.log_result = log_result
        log.f1 = f1
        log.f2 = f2
        log.f3 = f3
        log.f4 = f4
        log.f5 = f5
        log.f6 = f6
        log.log_time = datetime.datetime.now()
        log.save(using='write')
        code = 0
    except Exception, ex:
        code = -1
        print ex
    
    return code
    
def md5(s):
    signStr = hashlib.md5() 
    signStr.update(s.encode('utf-8'))
    return signStr.hexdigest()


def getConn(server_id=0):
    return Server.get_conn(server_id)


def url_encode(url):
    params = url.split('&')
    data = {}
    for item in params:
        tmp = item.split('=')
        name = tmp[0]
        value = tmp[1]
        data[name] = value
    return urllib.urlencode(data)

def get_server_list():
    return Server.objects.using('read').filter(~Q(status = 1)).order_by('-status')


def filter_sql(sql):
    import re
    p = re.compile( '(update|delete|modify|column|lock|drop|table)', re.I)
    sql = p.sub( '', sql)
    return sql

def get_abs_path(expression):
    root_path = os.path.dirname(__file__)
    folder_path = os.path.abspath(os.path.join(root_path, expression))
    return folder_path
            
def get_abs_path_and_mkdir(expression):
    folder_path = get_abs_path(expression)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    return folder_path

def mkdir(path,mode=0755):
    if not os.path.exists(path):
        os.makedirs(path,mode)
    return path
    
def del_files(folder_path):
    for file_item in os.listdir(folder_path):
        try:
            itemsrc = os.path.join(folder_path, file_item)
            if os.path.isfile(itemsrc):
                os.remove(itemsrc)
        except:
            pass

    
def get_static_root(*child_dir_names):
    the_dir =  os.path.join(STATIC_ROOT,*(str(x) for x in child_dir_names))
    mkdir(the_dir)
    return the_dir
    
class GlobalPathCfg(object):
    
    def __init__(self):
        self.static_folder_name = 'static'
    
    def get_static_folder_path(self):
        path = get_abs_path(r'../../%s' % self.static_folder_name)
        return path
    
    def get_current_url(self,request):
        current_url = '%s%s' % (request.get_host(), request.get_full_path())
        return current_url

    
    #****************创建索引SQL保存文件路径**********
    def get_create_index_save_path(self, file_name):
        static_path = self.get_static_folder_path()
        path = static_path + '/sql'
        mkdir(path)
        path = path + '/' + file_name
        return path
    
    #**********公告相关*************
    def get_notice_html_template_path(self):
        return '%s/server/notice_template.html' % get_abs_path(TEMPLATE_DIRS[0])
    
    
    def get_template_path(self):
        return get_abs_path(TEMPLATE_DIRS[0])
    
    #获取公告html访问url
    def get_notice_html_url(self, request ,file_name, is_ssl):
        pro = 'http'
        if int(is_ssl) == 1 : pro = 'https'
        return '%s://%s/%s/notice/html/%s' % (pro,request.get_host() ,self.static_folder_name, file_name)
    
    #获取公告html保存路径
    def get_notice_html_save_path(self, file_name):
        static_path = self.get_static_folder_path()
        path = os.path.join(  STATIC_ROOT,'notice','html')
        mkdir(path)
        path = os.path.join(  path,file_name)
        return path

    def get_notice_html_save_path_client(self,file_name):
        path = os.path.join(STATIC_ROOT,'client','static','notice','html')
        mkdir(path)
        path = os.path.join(path,file_name)
        return path

    def get_static_root(self,*child_dir_names):
        return get_static_root(*child_dir_names)
    
    #**********公告相关  END **********
    
#w     以写方式打开，
#a     以追加模式打开 (从 EOF 开始, 必要时创建新文件)
#r+     以读写模式打开
#w+     以读写模式打开 (参见 w )
#a+     以读写模式打开 (参见 a )
#rb     以二进制读模式打开
#wb     以二进制写模式打开 (参见 w )
#ab     以二进制追加模式打开 (参见 a )
#rb+    以二进制读写模式打开 (参见 r+ )
#wb+    以二进制读写模式打开 (参见 w+ )
#ab+    以二进制读写模式打开 (参见 a+ )