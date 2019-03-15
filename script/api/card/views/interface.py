# -*- coding: utf-8 -*-

import json, hashlib
import time,datetime
import re
import traceback

import MySQLdb
from _mysql_exceptions import IntegrityError
from django.shortcuts import render_to_response
from django.http import HttpResponse

from models.card import Card,CardBatch,CardLog,WorkLog
from models.server import Group,Server


channel_config = {
                "7725":{"key":"7725_#key",                #签名key
                        "user_type":10,                   #用户类型
                        "guest_key":"abn",                #游客奖励奖励礼包key
                        "appraise_key":"abp",             #评价礼包key
                        "share_key":"acn"
                        },
                "0":{"key":"7725_#key",                #签名key
                        "user_type":0,                   #用户类型
                        "guest_key":"abn",                #游客奖励奖励礼包key
                        "appraise_key":"abp",             #评价礼包key
                        "share_key":"acn"
                        }
                }

reward_type_list = ['guest','appraise','share']

result_code = {
 "成功": 1000,
 "發送奖励成功": 1000,
 "系統異常": 1002,
 "傳入參數為空": 1003,
 "加密串不匹配": 1010,
 "serialNo重複": 1006,
 "背包已满": 1037,
 "该用户无此角色": 1038,
 "不存在的服务器id": 1039,
 "不存在的礼包": 1034,
}



def md5(sign_str):
    signStr=hashlib.md5()
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()


def getConn(server_id=0):
    return Server.get_conn(server_id)

def get_player_id(link_key,sid,user_type):
    player_id = 0
    try:

        the_conn = getConn(int(sid))
        cursor = the_conn.cursor()
        sql = "SELECT player_id FROM player_%s where link_key='%s' and user_type=%d;" % (sid,link_key,int(user_type))
        cursor.execute(sql)

        player_id = cursor.fetchone()[0]
        print (player_id,user_type,sid,sql)
    except:
        traceback.print_exc()
    return player_id


def get_gift_by_packageid(packageid):
    gift_package = CardBatch.objects.using('card').get(key=packageid)
    return gift_package


def insert_into_work_id(serialNo, cursor):
    '''重复检测
    '''
    sql = "INSERT INTO work_log (work_number, add_time) VALUES (%s,%s)"
    try:
        cursor.execute(sql, (serialNo, datetime.datetime.now()))
    except IntegrityError, ex:
        return 1
    return 0


def rsp(err_msg, mgr = ""):
    result_json = {}
    code = result_code.get(err_msg, -1)
    result_json["result"] = code
    if code == 1000:
        mgr = "success"
    result_json["message"] = mgr
    return HttpResponse(json.dumps(result_json))




def gift(request):
    '''服务端礼包接口
    '''
    print("gift...")
    g = lambda x,y:request.POST.get(x,request.GET.get(x,y))
    sign = g("sign", "").lower()
    userid  = g("userid", "") #efun的userid
    roleid  = g("roleid", "") #是角色ID
    serialNo = g("serialNo", "") #是唯一标示，如果这个标示重复就不会发奖励
    serverid = g("serverid", "") #服务器标示
    packageid  = g("packageid", "") #奖励的物品id
    packetnum = g("packetnum", "") #奖励的数量
    gameCode = g("gameCode", "") #游戏标识
    activityCode = g("activityCode", "") #活动代码（标识）(非必选参数)

    config = channel_config.get(gameCode, [])
    if 0 >= config.__len__():
        return rsp("傳入參數為空")

    sign_key = config['key']
    user_type = config['user_type']
    s_sign = '%s%s%s%s%s%s%s%s' % (userid, roleid, serverid, gameCode, serialNo, packageid, packetnum, sign_key)
    s_sign = md5(s_sign)
    print s_sign
    if sign != s_sign:
        return rsp("加密串不匹配")
    if '' == packetnum:
        packetnum = int(1)
    else:
        packetnum = int(packetnum)
    if packetnum > 20:
        return rsp("系統異常")

    try:
        return make_gift(userid,user_type,roleid,serverid,packageid,packetnum,serialNo)
    except Exception, ex:
        traceback.print_exc()
        return rsp("系統異常", str(ex))
    return rsp("成功")

def make_gift(userid,user_type,roleid,serverid,packageid,packetnum,serialNo,gameCode=''):
    try:
        from django.db import connections
        cursor = connections['card'].cursor()
        #cursor.execute('LOCK TABLES work_log WRITE;')
        package = get_gift_by_packageid(packageid)
        if package.end_time < datetime.datetime.now():
                return rsp("系統異常", "time out")
        if '' == roleid:
            roleid = get_player_id(userid,int(serverid),int(user_type))
            if not roleid:
                return rsp("该用户无此角色")
        else:
            roleid = int(roleid)

        prize = package.prize
        try:
            if 0 != insert_into_work_id(serialNo, cursor):
                return rsp("serialNo重複")
        except Exception, ex:
            traceback.print_exc()
            return rsp("serialNo重複")

        for i in range(packetnum):
            cardlog = CardLog()
            cardlog.card_key =  package.key
            cardlog.card_name = package.name
            cardlog.channel_key = gameCode
            cardlog.server_id = int(serverid)
            cardlog.player_id = int(roleid)
            cardlog.prize = prize
            cardlog.status = 0
            cardlog.number = str(int(time.time() * 1000))
            cardlog.save(using='card')



    except Exception, ex:
        traceback.print_exc()
        return rsp("系統異常", str(ex))
    return rsp("成功")


def chk_sign(request, app_key):
    g = request.REQUEST
    keys = request.REQUEST.keys()
    keys.sort()
    sign = ''
    s_sign = ''
    for k in keys:
        if k == 'sign':
            sign = g.get('sign')
            continue
        value = g.get(k, '').replace('\r', '').replace('\n', '').replace('&', '')
        s_sign = '%s%s=%s' % (s_sign, k, value)
    s_sign = md5('%s%s' %(s_sign, app_key))
    print sign, s_sign

    if sign == s_sign:
        return True
    return False


def reward(request,reward_type_str='',channel_name=''):
    '''礼包奖励 发放
    '''
    try:
        if reward_type_str  not in reward_type_list:
            return rsp("不存在的礼包")
        config = channel_config.get(channel_name,{})
        if config:
            reward_key = config.get('%s_key' % reward_type_str,'')
            if reward_key:
                userid = request.REQUEST.get('user_id','')
                if userid:
                    serverid = int(request.REQUEST.get('server_id','') or 0)
                    roleid  = int(request.REQUEST.get("role_id", "") or 0 ) #是角色ID
                    channel_key = request.REQUEST.get('qd','')
                    user_type = config['user_type']
                    serialNo = '%s_%s_%s' % (reward_type_str,serverid,userid)
                    _roleid = get_player_id(userid,int(serverid),int(user_type))
                    if int(roleid) == _roleid:
                        return make_gift(userid,user_type,roleid,serverid,reward_key,1,serialNo,gameCode=channel_key)
                    else:
                        return rsp("该用户无此角色")
    except Exception, ex:
        traceback.print_exc()
        return rsp("系統異常", str(ex))
    return rsp("傳入參數為空")


def reward_get(request,reward_type_str='',channel_name=''):
    '''礼包奖励获取
    '''
    ret = {'status':0}
    try:
        userid = request.REQUEST.get('user_id','')
        serverid = int(request.REQUEST.get('server_id','') or 0)
        if serverid:
            serialNo = '%s_%s_%s' % (reward_type_str,serverid,userid)
        else:
            serialNo = '%s_%s' % (reward_type_str,userid)
        if reward_type_str  in reward_type_list:
            reward_key = channel_config.get(channel_name,{}).get('%s_key' % reward_type_str,'')
            if reward_key:
                is_already_reward = WorkLog.objects.using('card').filter(work_number=serialNo).exists()

                package = get_gift_by_packageid(reward_key)
                ret['prize'] = json.loads(package.prize)
                ret['status'] = 1 if is_already_reward else 0
    except:
        pass
    return HttpResponse(json.dumps(ret))

