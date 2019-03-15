# -*- coding: utf-8 -*-
#
#游戏玩家装备英雄
#
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
from cache import center_cache
from util.http import http_post
from util import str_to_datetime,datetime_to_timestamp,timestamp_to_datetime_str
from views.widgets import get_group_servers_dict,get_agent_channels_dict
import json, time, MySQLdb,traceback
from urls.AutoUrl import Route
import datetime
import time
from util import trace_msg
from .base import GMProtocol

from .game_def import PLAYER_INFO_MAP,VIP_PRICE,PLAYER_BUILDING_MAP,KEJI_MAP

from models.log import DictDefine


@Route()
def equip_info(request,player_id=0,template = 'game/equip_info.html'):
    '''角色装备信息
    '''
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.GET.get('player_name','')
    
    gmp = GMProtocol(server_id)
    err_msg = ''
    try: 
        gmp.time_out = 10
        # 1:核装,2:普装,3:摆摊挂单,4:法宝,5:血脉,6:道具
        # equip_type = [1,2,3,4,5]
        clr_equip_list = gmp.get_equip_info(player_id,[1])
        stand_equip_list = gmp.get_equip_info(player_id,[2])
        sell_item_list = gmp.get_equip_info(player_id,[3])
        blood_item_list = gmp.get_equip_info(player_id,[5])
        magic_list = gmp.get_equip_info(player_id,[4])
        if not clr_equip_list:
            err_msg = "GM工具返回,没有此角色装备!"
        else:
            if type(clr_equip_list != str) and clr_equip_list:
                clr_equip = get_clr_equip(clr_equip_list["1"])
            if type(stand_equip_list != str) and stand_equip_list:
                stand_equip = get_stand_equip(stand_equip_list["2"])
                tol_equio_num = len(stand_equip)
            if type(sell_item_list != str) and sell_item_list:
                sell_item = get_sell_item(sell_item_list["3"])
                sell_item_num = len(sell_item)
            if type(magic_list != str) and magic_list:
                magic = get_magic(magic_list["4"])
                magic_num = len(magic)
            if type(blood_item_list != str) and blood_item_list:
                blood_item = get_blood_item(blood_item_list["5"])
    except Exception, e:
        player_info = {}
        err_msg = trace_msg()

    return render_to_response(template, locals())

@Route()
def equip_modify(request,player_id=0):
    '''装备修改
    '''
    _r = {"code":-1,"msg":""}
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.REQUEST.get('player_name','')
    json_msg = request.REQUEST.get('msg','')
    try:
        if json_msg:
            msg = json.loads(json_msg)
            gmp = GMProtocol(server_id)

            if 'equip-add' == request.REQUEST.get('req_type',''):
                iid_list = msg.get('iid_list','')
                num_list = msg.get('num_list','')
                add_l = [list(l) for l in zip(iid_list,num_list)]
                result = gmp.add_equip(player_id,add_l)

            if 'equip-del' == request.REQUEST.get('req_type','') or 'equip-del_nums' == request.REQUEST.get('req_type',''):
                result = gmp.del_equip(player_id,msg)

            if 'equip-add_nums' == request.REQUEST.get('req_type',''):
                result = gmp.add_equip(player_id,msg)


            _r['msg'] = gmp.rsp_map.get(result,result)
            _r['code'] = result
            gmp.save_log(request.admin.id, gmp.req_type, _r['code'],role_name=player_name,remark2=json_msg)
    except:
        err_msg = trace_msg()
        _r['msg'] = err_msg
        
    return HttpResponse(json.dumps(_r))



def get_clr_equip(data):
    # 1
    #名字  configId
    #词条属性  entryList > entryId ,attr[0] > value
    # 星级  衣服+ 武器    len(clothesStar) 
    # 星级加成 [i["add"] for i in clothesStar]
    if not data or not data["artifacts"]:
        return []
    kernelEquip = DictDefine.get_dict_for_key("kernelEquip")

    _result = {}
    _result["cloth"],_result["weapon"] = [],[]
    weapon = data["artifacts"][0] if int(data["artifacts"][0]["configId"]) < 210000 else data["artifacts"][1]
    cloth = data["artifacts"][0] if int(data["artifacts"][0]["configId"]) > 210000 else data["artifacts"][1]
    _t = {"weapon":weapon,"cloth":cloth}
    _star = {"weapon":"weaponStar","cloth":"clothesStar"}

    for t in _t:
        _result[t].append(kernelEquip.get(str(_t[t]["configId"]),_t[t]["configId"]))
        _result[t].append(len(data[_star[t]]))
        _result[t].append([i["add"] for i in data[_star[t]]])
    return _result.values()

def get_stand_equip(data):
    # 2
    #名字 configId
    # 强化等级 extraData > strength
    # 玉石 jades  
    # 玉链 activeJadeLink  jadeLinks[int(activeJadeLink)-1]
    if not data:
        return []
    _result = []
    stand_equip = DictDefine.get_dict_for_key("stand_equip")
    jades = DictDefine.get_dict_for_key("jades")
    jadeLinks = DictDefine.get_dict_for_key("jadelinks")
    for s in data:
        _t = []
        _t.append(stand_equip.get(str(s["configId"]),s["configId"]))
        _t.append(s["extraData"]["strength"])
        _t.append([jades.get(str(s["extraData"]["jades"][i] ),s["extraData"]["jades"][i]) for i in s["extraData"]["jades"]])
        _t.append(jadeLinks.get(str(s["extraData"]["jadeLinks"][int(s["extraData"]["activeJadeLink"])-1]["id"]),s["extraData"]["jadeLinks"][int(s["extraData"]["activeJadeLink"])-1]) if s["extraData"]["jadeLinks"] else 0)
        _result.append(_t)
    return _result

def get_sell_item(data):
    if not data:
        return []
    _result = []
    daoju = DictDefine.get_dict_for_key("equipment")
    for i in data:
        _temp = []
        _temp.append(daoju.get(str(i["itemId"]),i["itemId"]))
        _temp.append(i["count"])
        _temp.append(time.strftime("%Y:%m:%d %H:%M:%S",time.localtime(i["stackTime"])))
        _temp.append(i["price"])
        _result.append(_temp)
    return _result

def get_magic(data):
    # strength   star state 1 佩戴 2 未佩戴 3 共鸣 
    if not data:
        return []
    _result = []
    _state = {1:"佩戴",2:"未佩戴",3:"共鸣"}
    magicWeapon = DictDefine.get_dict_for_key("magicWeapon")
    for m in data:
        _t = []
        _t.append(magicWeapon.get(str(m["configId"]),m["configId"]))
        _t.append(m["extraData"]["strength"])
        _t.append(m["extraData"]["star"])
        _t.append(_state[m["extraData"]["state"]])
        _result.append(_t)
    return _result
    
def get_blood_item(data):
    # 5
    #穴位 acupoint
    # 等级 level
    # 血脉 baseattr 》 type 名  attr 进度
    if not data:
        return []
    _blood = {1:"摧山古脉",2:"羲风玄脉",3:"殷阳古脉",4:"崩川古脉"}
    _result = []
    _result.append(data["acupoint"])
    _result.append(data["level"])
    t = []
    for b in data["baseAttr"]:
        t.append([[_blood[b["type"]]],b["attr"]])
    _result.append(t)
    print _result
    return _result


@Route()
def equip_item_info(request,player_id=0,template = 'game/equip_item_info.html'):
    '''角色装备信息
    '''
    player_id = player_id or int(request.REQUEST.get('player_id',0))
    server_id = int(request.REQUEST.get('server_id',0))
    player_name = request.GET.get('player_name','')
    
    gmp = GMProtocol(server_id)
    err_msg = ''
    try: 
        gmp.time_out = 10
        # 1:核装,2:普装,3:摆摊挂单,4:法宝,5:血脉,6:道具,7:宠物
        # equip_type = [1,2,3,4,5]
        equip_item = [6]
        equip_item_list = gmp.get_equip_info(player_id,equip_item)
        if not equip_item_list:
            err_msg = "GM工具返回,没有此角色装备!"
        else:
            equip_item = get_equip_item(equip_item_list["6"])
            tol_equio_num = len(equip_item)
    except Exception, e:
        player_info = {}
        err_msg = trace_msg()

    return render_to_response(template, locals())


def get_equip_item(data):
    if not data:
        return []
    daoju = DictDefine.get_dict_for_key("equipment")
    kernelEquip = DictDefine.get_dict_for_key("kernelEquip")
    _result = []
    for item in data["mainBag"]:
        daojuId = item["configId"]
        _name = daoju.get(str(daojuId),daojuId)
        _name = kernelEquip.get(str(_name),_name) if _name == daojuId else _name
        _t = [_name]
        _t.append(item["amount"])
        _result.append(_t)
    return _result