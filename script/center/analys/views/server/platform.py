# -*- coding: utf-8 -*-
#游戏平台

#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.db.models import Q 
from django.utils.html import conditional_escape 
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
from django.template import loader, RequestContext
#==========================================




from util.http import http_post
from util import str_to_datetime,datetime_to_timestamp,timestamp_to_datetime_str,filter_sql
import json, time, MySQLdb,traceback
from urls.AutoUrl import Route
import datetime,time,os
from util import trace_msg
from views.base import BaseView,get_static_root
import urllib2
from models.platform import PlatForm



@Route('^server/platform')
class platform_view(BaseView):
    
    models_cls = PlatForm
    def initialize(self):
        self.id = int(self.request.REQUEST.get('id','') or 0)
        self.ids = self.request.REQUEST.getlist('id')
        
        if self.id:
            self.model = PlatForm.objects.get(id=self.id)
        else:
            self.model = PlatForm()
            
        self.player_id = int(self.request.REQUEST.get('player_id','') or 0)
        self.player_name = self.request.REQUEST.get('player_name','')
            
    def list(self,template='server/platform_list.html'):
        record = self.models_cls.objects.all()
        return self.render_to_response(template,locals())


    def edit(self,template='server/platform_edit.html',err_msg=''):
        model = self.model
        model.id = self.model.id or 0

        return self.render_to_response(template,locals())
    
    def edit_copy(self):
        self.model.id = 0
        self.model.name = '%s - copy' % (self.model.name)
        return self.edit()
    
    def save(self,template='server/platform_edit.html'):
        code = -1
        model_id = 0
        err_msg = ''
        try:
            self.model.set_attr('name',self.request.REQUEST.get('name',''),null=False)
            self.model.set_attr('key',self.request.REQUEST.get('key',''),null=False)
            self.model.set_attr('app_key',self.request.REQUEST.get('app_key',''),null=False)
            self.model.set_attr('address',self.request.REQUEST.get('address',''),null=False)
            self.model.set_attr('channel_address',self.request.REQUEST.get('channel_address',''),null=False)
            self.model.set_attr('server_address',self.request.REQUEST.get('server_address',''),null=False)
            self.model.set_attr('remark',self.request.REQUEST.get('remark',''),null=True)
            self.model.set_attr('time_zone',self.request.REQUEST.get('time_zone',''),value_handler=int,null=False)
            self.model.save()
            
        except:
            err_msg = trace_msg()
        return self.edit(err_msg=err_msg)

    

    def remove(self,template='game/platform_remove.html'):
        self.models_cls.objects.filter(id__in=self.ids).delete()
        return self.render_to_response('feedback.html',locals())       

    def update_server_channel_file(self):
        if self.model.id:
            update_channel_server_data(self.model)

        else:
            for p in PlatForm.objects.all():
                update_channel_server_data(p)
        return self.HttpResponse('成功!')
    
def urlopen(url,parmars='',timeout=20):
    try:
        response = urllib2.urlopen(url, parmars, timeout=20)
        r_str = response.read()
        json.loads(r_str)
        return r_str
    except:
        return '{}'
    
def update_channel_server_data(platform_model):
    '''获取各个平台的 渠道和服务器 json列表!
    '''
    p = platform_model

    save_path = get_static_root('platform',p.key)
    server_json_file_path = os.path.join(save_path,'server.json')
    channel_json_file_path = os.path.join(save_path,'channel.json')
    server_address = p.server_address
    channel_address = p.channel_address
    if channel_address:
        print '更新  %s 渠道文件 [%s]' %(p.name,channel_address)
        channel_json_cont = urlopen(channel_address)
        with open(channel_json_file_path,'wb') as fp:
            fp.write(channel_json_cont)
    if server_address:
        print '更新  %s 服务器文件 [%s]' %(p.name,server_address)
        server_json_cont = urlopen(server_address)
        with open(server_json_file_path,'wb') as fp:
            fp.write(server_json_cont)
