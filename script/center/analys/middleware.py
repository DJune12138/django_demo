# -*- coding: utf-8 -*-
#
#认证,和自定request的中间件
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

import MySQLdb
from MySQLdb import DatabaseError
import functools
from models.admin import Admin
from models.channel import Agent
from models.log import LogDefine , Log
from models.menu import Menu
from util import trace_msg
from util.memcached import MemcachedUtil
from util import md5
import datetime
import time,json
import logging 
import new
import traceback
from django.views import debug
import sys
from settings import DEBUG
#日志记录
_log = logging.getLogger('root')

  

def get_real_ip(request):
    '''获取真实ip
    '''
    return request.META.get('HTTP_REMOTE_ADDR2','') or request.META.get('HTTP_X_FORWARDED_FOR','') or request.META.get('REMOTE_ADDR')            

class CustomRequestMiddleware(object):
    '''自定义request处理,增加一些方法和属性
    '''
    def process_request(self, request):
        request.POST._mutable = True #
        request.GET._mutable = True  #可以使用reuqest.GET.setlist('key',[value])方法
        request.real_ip = get_real_ip(request)
        request.is_debug = DEBUG
        request._start_time = time.time()
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        pass
    
    def process_response(self,request,response):
        return response
        
    def process_exception(self, request, exception):
        '''出错处理
        '''
        #etype, value, tb = sys.exc_info()
        #traceback.print_tb(tb)
        pass
        #print trace_msg()
        #_log.warning(trace_msg())
        return debug.technical_500_response(request, *sys.exc_info())
        
    def print_sql(self):
        '''打印sql
        '''
        print '-' * 20,'sqls:','-' * 20
        for i,d in enumerate(connection.queries):
            print '<%s> %s : %s' % (i+1,d['time'],d['sql'])

class AuthMiddleware(object):
    '''认证的中间件
    '''
    
    def process_request(self, request):
        pass
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        '''静态文件及有"notauth" 属性view_func 免认证
        '''

        if hasattr(view_func,'notauth') or view_func.__module__ == 'django.views.static' :#不需处理的函数不管
            is_allow = True
            if  (request.path_info.find('/login') == 0 and request.method == 'POST'):
                request.admin = Admin()
                request.admin.id = 0
                self.save_operate_log(request, '登录后台')
        else:
            the_admin = None
            agent_id = request.session.get('agent_id', None)    #渠道登录的
            if agent_id!=None:
                the_admin =Agent.get_admin(agent_id)
            else:
                admin_id = request.session.get('admin_id', None)
                the_admin = Admin.get_admin(admin_id)
            request.admin = the_admin
            if not request.admin :
                return HttpResponseRedirect('/login?from_url=%s' %request.get_full_path())
            
            #if request.session.session_key != request.admin.session_key:
           #     return HttpResponse('别处登录!')
            
            admin_menus = request.admin.resource.menu.using('read') #
            _admin_menu_map = {}
            for m in admin_menus.all():
                menu_name = m.name
                #if isinstance(menu_name,unicode):
                #    menu_name = menu_name.encode('utf-8')
                _admin_menu_map[menu_name] = m
            request.allow_menu = _admin_menu_map         
            is_allow = self.check_url_permsssion(request)
            
        if not is_allow:
            if request.is_ajax():
                return HttpResponse('{"code":1,"content":[],"msg":"没有权限!"}')
            return render_to_response('block.html',locals())
          
            #return self.cache_view(request, view_func, view_args, view_kwargs)
        
    def process_response(self,request,response):
        return response
    
    def process_exception(self, request, exception):
        pass
        
    
    def check_url_permsssion(self,request):
        '''检查请求URL的权限
        '''
        is_allow = False
        match_menu = None
        
        url_path = request.path_info
        params  = dict(request.REQUEST)
        
        #管理员的菜单里查询匹配项目
        for k,menu in request.allow_menu.iteritems():
                if  url_path == menu.url_path and menu.is_match_url_parmas(params) :
                    match_menu = menu
                    is_allow = True
                    break
        
        if match_menu:
            if match_menu.is_log:
                self.save_operate_log(request, match_menu.name)

        if request.admin.is_root:#管理员直接过
            is_allow = True
            
        return is_allow
    

    
    
    def cache_view(self,request, view_func, view_args, view_kwargs):
        '''页面级别的缓存
        '''
        cache_method_list = ['']
        _mc = MemcachedUtil()
        params = str(request.REQUEST)
        view_func_name = view_func.__name__
        key = md5('%s_%s_%s' % (request.admin.id,view_func.__name__,params))
        response = _mc.get(key)
        if not response:
            response = view_func(request,*view_args,**view_kwargs)
            _mc.set(key, response, 1800)
        return response
    
    def save_operate_log(self,request,msg,log_type=29):
        '''写操作日志
        '''
        try:
            Log._meta.db_table = 'log_operate'
            log = Log()
            log.log_type = log_type
            log.log_server = 0
            log.log_channel = 0 
            log.log_user = request.admin.id
            log.log_data =  0
            log.log_result = 0
            log.f1 = msg[:100]
            log.f2 = request.get_full_path()[:100]
            log.f3 = request.real_ip
            post_params = unicode(json.dumps(dict(request.POST),ensure_ascii=False))
            log.f4 = post_params[:100]
            log.f5 = post_params[100:200]
            log.f6 = post_params[300:400]
            log.log_time = datetime.datetime.now()
            log.save(using='write')
        except Exception,e:
            traceback.print_exc()
            create_table_sql = Log.get_create_table_sql('log_operate')
            conn = connection
            cur = conn.cursor()
            print create_table_sql
            cur.execute(create_table_sql)

    

            
            
