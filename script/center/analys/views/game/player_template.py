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
from models.player_template import PlayerTemplate
from .game_def import PLAYER_INFO_MAP,VIP_PRICE,PLAYER_BUILDING_MAP,KEJI_MAP




@Route('^game/player_template')
class player_template_view(BaseView):
    
    def initialize(self):
        self.player_template_id = int(self.request.REQUEST.get('id','') or 0)
        self.player_template_ids = self.request.REQUEST.getlist('id')
        
        if self.player_template_id:
            self.player_template_model = PlayerTemplate.objects.get(id=self.player_template_id)
        else:
            self.player_template_model = PlayerTemplate()
        self.player_id = int(self.request.REQUEST.get('player_id','') or 0)
        self.player_name = self.request.REQUEST.get('player_name','')
            
    def list(self,template='game/player_template_list.html'):
        record = PlayerTemplate.objects.all()
        player_id = self.player_id
        player_name = self.player_name
        return self.render_to_response(template,locals())

    
    def edit(self,template='game/player_template_edit.html'):
        model = self.player_template_model
        model.id = model.id or 0
        keji_name_dict = KEJI_MAP
        
        keji_value_dict = {}
        keji_value_list = self.player_template_model.json_data.get('psc',[])
        for keji_item in keji_value_list:
            keji_value_dict[keji_item['id']] = keji_item['lv']
        for k,v in keji_name_dict.iteritems():
            keji_value_dict[k] = keji_value_dict.get(k,'')

        return self.render_to_response(template,locals())

    @json_response
    def save(self,template='game/player_template_edit.html'):
        code = -1
        model_id = 0
        msg = ''
        try:
            json_data = self.request.REQUEST.get('json_data','{}')
            name = self.request.REQUEST.get('name','')
            self.player_template_model.name = name
            self.player_template_model.json_data = json_data
            self.player_template_model.remark = self.request.REQUEST.get('remark','')
            self.player_template_model.save()
            code = 0
            model_id = self.player_template_model.id
        except:
            msg = trace_msg()

        return code,msg,model_id
    

    def remove(self,template='game/player_template_edit.html'):
        self.player_template_model.delete()
        return self.render_to_response('feedback.html',locals())       


    def import_to_player(self):
        err_msg = ''
        try:
            server_id = self.player_id >> 20
            gm_data = self.player_template_model.json_data
            
            country_val = gm_data.get('country',0)
            resource_list = gm_data.get('resource',[])
            war_story_process_list = gm_data.get('war_story_process',[])
            psc = {'psc':gm_data.get('psc',{}) }
            rcode_list = []
            gmp = GMProtocol(server_id)
            # 发资源
            rcode,_ = gmp.send_resouces([self.player_id], resource_list)
            rcode_list.append(rcode)
            # 改国家
            rcode = gmp.motify_player_kingdom(self.player_id,country_val)
            rcode_list.append(rcode)
            # 改进度
            rcode = gmp.modify_war_story_process(self.player_id, war_story_process_list)
            rcode_list.append(rcode)
            
            # 改科技
            rcode = gmp.player_modify_info(self.player_id,psc)
            rcode_list.append(rcode)
            
            if rcode_list.count(0) == len(rcode_list):
                result = 0
            else:
                err_msg = '失败[%s]' % rcode_list
                result = -1
                
            remark1 = self.player_template_model.name
            
            gmp.save_log(self.request.admin.id, GMActionType.import_player_template, result,role_name=self.player_name,remark1=remark1)
            
        except:
            err_msg = trace_msg()
            
        return self.render_to_response('feedback.html',locals())    
        
        