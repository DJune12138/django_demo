# -*- coding: utf-8 -*-
#
#django 模板过滤器
#
from models.player import Player
from models.log import DictDefine
from models.server import GroupList
from django import template
from util import DecimalEncoder
from django.core.serializers.json import  DjangoJSONEncoder
register = template.Library()
import json

@register.filter(name='mydate')
def mydate(value,arg):
    if value.find('2012').size>0:
        return value
    else:
        return value
    
@register.filter(name='json_dumps')
def json_dumps(value):
    _r = json.dumps(value,cls=DjangoJSONEncoder,ensure_ascii=False)
    return _r


@register.filter(name='player_status')
def player_status(value):
    return dict(Player.STATUS_CHOICES).get(value,value)

from views.game.game_def import PLAYER_INFO_MAP,PLAYER_BUILDING_MAP,Player_Map

#@register.filter(name='game_country')
#def game_country(value):
#    return PLAYER_INFO_MAP.get('spi',{}).get('dict',{}).get(value,value)

@register.filter(name='get_server_list')
def get_server_list(value):
    model = GroupList.objects.using('read').get(id=value)
    iid = [int(s.id) for s in model.server.all()]
    the_dict = DictDefine.get_dict_for_key('server_name ')
    l = []
    for i in iid:
        name = the_dict.get(str(i),'')
        result = '(%s)%s' %(i,name)
        l.append(result)
    return ','.join(l)

@register.filter(name='game_country')
def game_country(value):
    return Player_Map.get('gj',{}).get(value,value)

@register.filter(name='game_building')
def game_building(value):
    return PLAYER_BUILDING_MAP.get(value,value)

@register.filter(name='get_dict_key')
def get_dict_key(key,_dict,default=''):
    try:
        if isinstance(_dict,dict):
            return _dict.get(key,_dict.get(str(key),key))
    except:
        return default
    
@register.filter(name='dict_key')
def dict_key(value,key_name):
    the_dict = DictDefine.get_dict_for_key(key_name)
    return the_dict.get(value,the_dict.get(str(value),value))


from util import timestamp_to_datetime_str
@register.filter(name='timestamp2datetime')
def timestamp_to_datetime(value, _f='datetime'):
    try:
        _r = timestamp_to_datetime_str(int(value), _f) if  value else ''
    except:
        _r = ''
    return  _r 

@register.filter(name='convertTimeJson')
def convert_times_json(value):
    ret_json = []
    for i in value:
        tmp = "%s:%s - %s:%s" % (i[0]/3600, (i[0]%3600)/60, i[1]/3600, (i[1]%3600)/60)
        ret_json.append(tmp)
    return " , ".join(ret_json)