# -*- coding: utf-8 -*-
#
#GM类相关
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

from models.gm import GMDefine
from .base import GMProtocol
from util.http import http_post
import json, time, datetime, shutil
from django.shortcuts import render_to_response
from django.http import HttpResponse
from views.game.base import write_gm_log
from views.base import save_log
from models.center import Server
from cache import center_cache
import logging  
from .base import GMProtocol
from util import trace_msg,get_now_str
from views.widgets import get_group_servers_dict,get_agent_channels_dict


class GMProtocolProxy(object):
    def __init__(self,server_id,gm_def,def_params,def_result):
        self.gmp = GMProtocol(server_id)
        self.gmp.req_type = gm_def.get_req_type()
        self.gm_def = gm_def
        self.def_params = def_params or gm_def.def_params
        self.def_result = def_result or gm_def.def_result
        
    def input_params_handle(self,input_params):
        player_id = input_params.get('player_id','')
        msg = input_params.get('msg')
        if player_id:
            self.gmp.add_player_id(player_id)
        if msg:
            self.gmp.msg = json.loads(msg)
        
    def get_result(self):
        result = self.gmp.get_result()
        if self.gm_def.result_type == 'source': #直接返回不处理
            return json.loads(result)
        
        _r = {"code":-1,"msg":'',"content":""}
        
        result_code = self.get_result_code(result)
        content = self.get_result_content(result)
        if self.gm_def.result_type == 'form':                         #把结果返回为键在输出
            result = self.make_form_item_for_content(content)
        
        if self.gm_def.result_type == 'msg':                          #如果是消息,则替换返回代码的消息
            desc_field_map = self.def_result.get('desc_field_map',{})
            _r["code"] = result_code
            _r["content"] = content
            _r['msg'] = desc_field_map.get(result_code,desc_field_map.get(unicode(result_code),result_code))
            result = _r
            
        return result
    
    def make_form_item_for_content(self,content):
        form_items = self.def_result.get('form_items',{})
        assert isinstance(form_items,dict),'form_items 不是字典!'
        form_items_list = []
        new_form_items = []

        for key, value in form_items.iteritems():
            form_items_list.append((key,value))
            
        form_items_list.sort(cmp=lambda x,y:cmp(x[1].get('order', 0), y[1].get('order', 0)))

        for key,item_config in form_items_list:
            value = self.get_result_for_path_depth(content,[key])
            form_item = FormItem(key,value)
            form_item.is_modify = item_config.get('is_modify',False)
            form_item.name = item_config.get('name','')
            form_item.attr_type = item_config.get('type','text')
            new_form_items.append((
                                   key,form_item
                                   ))
        
        return new_form_items
    
    def get_dict_key_or_index(self,key_name):
        '''判断是key还是路径
        '''
        if str(key_name).isdigit():
            return int(key_name)
        return  key_name
    
    def get_result_for_path_depth(self,result,path_depth):

        tmp_result = None
        _result = None
        
        for i,key_or_index in enumerate(path_depth):
            k_or_i = self.get_dict_key_or_index(key_or_index)
            if k_or_i == '-1':                                   #路径键为-1即为本身
                _result = result
                break

            if i == 0 :
                tmp_result = _result = result
            if isinstance(tmp_result,dict):
                _result = tmp_result.get(k_or_i)
            elif isinstance(tmp_result,list) and isinstance(k_or_i,int) and  len(tmp_result)>=k_or_i:
                _result = tmp_result[k_or_i]
            tmp_result = _result
            
        return _result
    
    def get_result_code(self,result):
        '''获取结果返回码
        '''
        code_path_depth = self.def_result.get('code_path',[])
        return self.get_result_for_path_depth(result,code_path_depth)

        
    def get_result_content(self,result):
        '''获取结果内容
        '''
        content_path_depth = self.def_result.get('content_path',[])
        return self.get_result_for_path_depth(result,content_path_depth) 

    def save_log(self,*args,**kwargs):
        return self.gmp.save_log(*args,**kwargs)
    
    
def gm(request, gm_id=0,template='game/gm_form.html'):
    '''GM 接口
    '''
    gm_id = gm_id or  int(request.REQUEST.get('gm_id','') or 0 )
    server_id = int(request.REQUEST.get('server_id','') or 0 )
    is_ajax = request.REQUEST.get('is_ajax','') or request.is_ajax()
    input_params = request.POST
    err_msg = result = ''
    now_time_str = get_now_str()
    def_params = {}
    def_result = {}
    try:
        gm_def = GMDefine.objects.get(id = gm_id) 
        def_result = gm_def.def_result
        def_params = gm_def.def_params
        print def_params
        if gm_def.result_type == 'from' :
            template='game/gm_from.html'
        if request.method == 'POST' or gm_def.result_type == 'msg':
            template = 'game/gm_post.html'
            other_templates = [ 'game/%s.html' % t for t in def_result.get('templates','').split(',') if t] 
        if server_id:
            gmp = GMProtocolProxy(server_id,gm_def,def_result,def_params)
            gmp.input_params_handle(input_params)
            result = gmp.get_result() 

    except GMDefine.DoesNotExist:
        err_msg = 'GM协议未定义'
    except:
        err_msg = trace_msg()
        result = {"code":-1,"msg":"%s" % err_msg} 

    if not is_ajax:
        group_servers_dict = get_group_servers_dict(request)
        select_server_ids = [server_id]
    else:
        return HttpResponse(json.dumps(result))
        
    return render_to_response(template, locals())



class FormItem(object):
    def __init__(self, key ,value, enum={}, attr_type='text',is_modify=True, is_append=False, ):
        self.key = key
        self.name = ''
        self.is_modify = is_modify
        self.is_append = is_append
        self.value = value
        self.enum = enum
        self.attr_type = attr_type
    
    def get_value(self):
        if '' != self.enum and None != self.enum and {} != self.enum:
            return self.enum.get(self.value, self.value) 
        
        value_type = self.attr_type
        if value_type in ['text', 'textarea']:
            return self.value
         
        if value_type in ['json', 'array']:
            result = json.dumps(self.value)
            
            result_type = type(self.value)
            
            if dict != result_type and list != result_type:
                if value_type == 'json':
                    return {}
                else:
                    return []
            return result

        if 'boolean' == value_type:
            if self.value:
                return 'true'
            else:
                return 'false'
        if 'timestamp' == value_type:
            return datetime.datetime.fromtimestamp(self.value).strftime('%Y-%m-%d %H:%M:%S')
        
        return self.value
        

def get_result(content_json, reason_phrase, gm_def, result_code, usm):
    result = None  
    result_def = json.loads(gm_def.result_define)
    if gm_def.result_type == 'json_result':
        result = {}
        result['content_json'] = json.dumps(content_json)
    
    elif gm_def.result_type == 'msg':
        result = result_def.get('msg_values',{})
        #print '-==============================='
        #print result
        #print result.get(str(content_json))
        result = result.get(str(content_json), u'错误,错误码:%s' % content_json)
    elif gm_def.result_type == 'form':
        
        list_infos = [] 
        
        form_items = result_def['form_items']
        
        form_items_list = []
        for key, value in form_items.items():
            #print key
            form_items_list.append({'key': key,'json':value})
        form_items = form_items_list
        
        form_items.sort(cmp=lambda x,y:cmp(x['json'].get('order', 0), y['json'].get('order', 0)))
        
        for _item in form_items:
            key = _item.get('key')
            def_item = _item.get('json')
            allow_empty = def_item.get('allow_empty', 0)
            has_value = False
            content_json_type = type(content_json)
            if dict == content_json_type:
                for r_key, value in content_json.items():
                    if key != r_key:
                        continue
                    has_value = True
                    item = FormItem(key, False, False, value, {}, 'text')
                    item.name = def_item.get('name', key) 
                    item.is_modify = def_item.get('is_modify', False)
                    item.is_textarea = def_item.get('is_textarea', False)
                    item.is_append = def_item.get('is_append', False)
                    item.attr_type = def_item.get('type', 'text')
                    item.enum =  def_item.get('enum', {})
    
                    list_infos.append(item)
            elif list == content_json_type:
                item = FormItem(key, False, False, value, {}, 'text')
                item.name = def_item.get('name', key) 
                item.is_modify = def_item.get('is_modify', False)
                item.is_textarea = def_item.get('is_textarea', False)
                item.is_append = def_item.get('is_append', False)
                item.attr_type = def_item.get('type', 'text')
                item.enum =  def_item.get('enum', {})
                item.value = json.dumps(content_json)
                list_infos.append(item)
                
            if not has_value and allow_empty:
                
                 
                item = FormItem(key, False, False, '', {}, 'text')
                item.name = def_item.get('name', key) 
                item.is_modify = def_item.get('is_modify', False)
                item.is_textarea = def_item.get('is_textarea', False)
                item.is_append = def_item.get('is_append', False)
                item.attr_type = def_item.get('type', 'text')
                item.enum =  def_item.get('enum', {})
                
                list_infos.append(item)
        
        result = {}
        result['form_action'] = result_def.get('form_action', '')
        result['form_type'] = result_def.get('form_type', '') 
        result['form_key'] =  result_def.get('form_key', '')
        
        server_list_chkbox = result_def.get('server_list_chkbox', False)
        
        if server_list_chkbox:
            
            group_server_dic = {}
            if usm.is_root:
                group_list = center_cache.get_group_list()
                for item in group_list:
                    group_server_dic[item.name] = center_cache.get_server_list(item.id)
            else:
                group_server_dic['服务器'] = usm.get_resource('server')
            
            result['group_server_dic'] = group_server_dic
            
        result['server_list_chkbox'] = server_list_chkbox
        result['list_infos'] = list_infos
        
    elif gm_def.result_type == 'list':
        list_items_def = result_def.get('list_items', {})
        list_action = result_def.get('action', [])
        
        #排序
        #先转数组 
        
        field_array = []
        for key, value in list_items_def.items():
            
            field_array.append({"key":key, "json":value}) 
        #排序  
        try:
            field_array.sort(cmp=lambda x,y:cmp(x['json'].get('order', 0), y['json'].get('order', 0)))
        except Exception, ex:
            print ex
        list_data  = []
        if list != type(content_json):
            try:
                print content_json
                content_json = json.loads(content_json)
            except Exception, ex:
                print 'get_reult type is list json loads error:'
                print ex
                content_json = []
        try:
            #每一行
            for item in content_json:
                row = {}
                
                field_dic = {}
                cells = []
                #每个字段
                for field_def in field_array:
                    key = field_def.get('key', '')
                    json_item = field_def.get('json', {})
                    value = item.get(key, '')
                    field_dic[key] = value
                    if type(json_item) == dict:
                        value_type = json_item.get('type', 'text')
                        if value_type == 'number':
                            value = float(value)
                        elif value_type in ['array', 'json']:
                            try:
                                value = json.loads(value)
                            except:
                                pass
                        elif value_type == 'timestamp':
                            try:
                                value = int(time.mktime(datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').timetuple()))
                            except Exception, ex:
                                print ex
                        elif value_type == 'int':
                            try:
                                value = int(value)
                            except:
                                pass
                    cells.append(value)
                 
                action_url = ''
                links = []
                for action in list_action:
                    action_title = action.get('title', '')
                    action_url = action.get('form_action', '')
                     
                    param_list = action.get('param_list', []) 
                    #print param_list
                    tmp_f = '?' 
                    for param in param_list:
                        param_name = param.get('param_name', '')
                        if '' == param_name:
                            continue
                        value_source = param.get('value_source', '')
                        value = field_dic[value_source]
                        if '' == param_name or '' == value_source:
                            continue
                        #print (action_url, tmp_f, value)
                        action_url = '%s%s%s=%s' % (action_url, tmp_f, param_name ,value)
                        tmp_f = '&'
                         
                    links.append({"title":action_title, 'link':action_url})
                
                row['cells'] = cells
                row['links'] = links
                
                list_data.append(row)
        except Exception, ex:
            print 'append row error:'
            print ex
              
        result = {}
        result['list_data'] = list_data
        result['list_field'] = field_array
    return result
         
        
        