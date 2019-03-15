# -*- coding: utf-8 -*-
#
#游戏玩家相关
#django 常用导入
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

from django.utils.datastructures import SortedDict 
from views.game.base import  write_gm_log
from views.base import getConn, get_server_list, quick_save_log
from models.server import Server
from util.http import http_post
from util import str_to_datetime,datetime_to_timestamp,timestamp_to_datetime_str,filter_sql
from views.widgets import get_group_servers_dict,get_agent_channels_dict
import json, time, MySQLdb,traceback
from urls.AutoUrl import Route
import datetime,time
from util import trace_msg
from .base import GMProtocol,GMActionType

from .game_def import PLAYER_INFO_MAP,VIP_PRICE,PLAYER_BUILDING_MAP,KEJI_MAP
from views.base import notauth,json_response,BaseView
from models.game import ActivityTemplate
from .game_def import PLAYER_INFO_MAP,VIP_PRICE,PLAYER_BUILDING_MAP,KEJI_MAP



@Route('^game/activity_template')
class activity_template_view(BaseView):
    
    def initialize(self):
        self.id = int(self.request.REQUEST.get('id','') or 0)
        self.ids = self.request.REQUEST.getlist('id')
        
        if self.id:
            self.model = ActivityTemplate.objects.get(id=self.id)
        else:
            self.model = ActivityTemplate()

            
    def list(self,template='game/activity_template_list.html'):
        type_name = self.request.REQUEST.get('type','') 
        if type_name:
            list_data = ActivityTemplate.objects.filter(type=type_name)
        else:
            list_data = ActivityTemplate.objects.all()
            
        return self.render_to_response(template,locals())

    
    def edit(self,template='game/activity_template_edit.html'):
        model = self.model
        model.id = model.id or 0
        
        return self.render_to_response(template,locals())

    @json_response
    def save(self,template='game/activity_template_edit.html'):
        code = -1
        model_id = 0
        msg = ''
        try:
            msg = self.request.REQUEST.get('msg','{}')
            name = self.request.REQUEST.get('name','')
            type_name = self.request.REQUEST.get('type','')
            info = self.request.REQUEST.get('info','')
            assert name,'名字不能空!'
            assert type_name,'类型名字不能空!'
            assert ActivityTemplate.objects.filter(name=name,type=type_name).count()==0,'已存在相同模版名'
            self.model.name = name
            self.model.msg = msg
            self.model.type = type_name
            self.model.info = info
            self.model.create_user_name = self.request.admin.alias
            self.model.save()
            code = 0
            model_id = self.model.id
            msg = '%s 保存成功!' % name
        except Exception,e:
            msg = str(e)
        return code,msg,model_id
    

    def remove(self,template='game/player_template_edit.html'):
        try:
            ActivityTemplate.objects.filter(id__in=self.ids).delete()
            msg = '成功!'
        except:
            msg = trace_msg()
        return self.HttpResponse(msg)       
    
    