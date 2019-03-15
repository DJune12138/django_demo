# -*- coding: utf-8 -*-
#角色相关列表
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.db.models import Q
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.template.context import RequestContext
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================

from django.shortcuts import render_to_response, HttpResponse
from models.server import Server, Group
from models.channel import Channel
from models.player import Player
from models.log import LogDefine
from views.base import getConn,json_response
from cache import center_cache
from views.base import quick_save_log
import datetime
import json
import MySQLdb
from django.db import connection
from views.game.base import  write_gm_log
from views.widgets import get_group_servers_dict,get_agent_channels_dict
from urls.AutoUrl import Route
from util import trace_msg,datetime_to_str,timestamp_to_datetime_str
from views.game.base import GMActionType
from models.log import Log 
from views.game.base import GMProtocol


@Route()
def player_block(request,server_id=0):
    '''封号
    '''
    player_ids = request.REQUEST.getlist('player_id')
    server_id = int(request.REQUEST.get('server_id',0))
    _r = {"code":-1,"msg":""}
    if request.method == 'POST' and player_ids:
        try:
            remark = request.REQUEST.get('remark','')
            conn = getConn(server_id)
            cursor = conn.cursor()
            the_status = -1 
            gmp = GMProtocol(server_id)
            if request.REQUEST.get('block_type','') == '1' :
                the_status = -1 
                log_type = GMActionType.block_player
                result = gmp.block_player(player_ids)
                if result != 0:
                    return HttpResponse(json.dumps(_r))
            else:
                the_status = 0
                log_type = GMActionType.unblock_player
                result = gmp.unblock_player(player_ids)
                if result != 0:
                    return HttpResponse(json.dumps(_r))
            query_sql = 'update player_%d set status=%d where player_id in (%s)'%(server_id,the_status,','.join(player_ids))
            cursor.execute(query_sql)
            cursor.close()
            for player_id in player_ids:
                write_gm_log(request.admin.id,
                  log_type,
                  log_type,
                  server_id,
                  player_id,
                  '',
                  0,
                  '',
                  '',
                  remark1 = remark,
                  )
            _r["code"] = 0
            
        except Exception,e:
            err_msg = trace_msg()
            _r["msg"] = err_msg
    return HttpResponse(json.dumps(_r))


def change_player_name(player_id,game_name):
    #_sid = get_server_id(player_id)
    _sid = int(player_id)>>20
    _r = {'code':1}
    try:
        conn = getConn(_sid)
        sql = "update player_%s set player_name='%s' where player_id=%d ;" % (_sid,game_name.encode('utf-8'),player_id)
        cur = conn.cursor()
        cur.execute(sql)
        _r['code']  = 0
        _r['msg'] =  'OK!'
    except Exception,e:
        err_msg = trace_msg()
        _r['msg'] = err_msg
    return json.dumps(_r)


def change_user_type(request):
    '''修改用户类型
    '''
    player_id = int(request.GET.get('player_id','0'))
    if player_id:
        sid = player_id >>20
        cursor = getConn(sid).cursor()
        if request.method == 'POST':
            user_type = request.POST.get('user_type','')
            if user_type!='':
                update_sql = "update player_%s set user_type=%d where player_id=%d" % (sid,int(user_type),player_id)
                cursor.execute(update_sql)
                return render_to_response('feedback.html')
        else:
            sql = 'select user_type from player_%d where player_id=%d;' % (sid,player_id)
            cursor.execute(sql)
            user_type = cursor.fetchone()[0]
    return render_to_response('game/change_user_type.html',locals())   

def player_info(request):
    g = lambda x,y: request.GET.get(x, request.POST.get(x,y))
    server_id = g('server_id', '')
    player_id = g('id', '')
    
    server_id = int(server_id)
    
    code = 1
    msg = ''
    item = {}
    try:
        conn = getConn(server_id)
        cur = conn.cursor()
        sql='select player_id,player_name,channel_id,user_type,link_key,login_num,mobile_key,last_time,create_time,status from player_%s WHERE player_id = %s ' 
        cur.execute(sql, (server_id, player_id))
        data_list = cur.fetchall()
        if 0 < data_list.__len__():
            tmp = data_list[0]
            s = item.setdefault
            s('player_id', tmp[0])
            s('player_name', tmp[1])
            s('channel_id', tmp[2])
            s('channel_name', center_cache.get_channel_by_id(str(tmp[2])).name)
            s('user_type', tmp[3])
            s('link_key', tmp[4])
            s('login_num', tmp[5])
            s('mobile_key', tmp[6])
            s('last_time', tmp[7].strftime('%Y-%m-%d %H:%M:%S'))
            s('create_time', tmp[8].strftime('%Y-%m-%d %H:%M:%S'))
            s('status', tmp[9])
            
            print item
            code = 0
    except Exception, ex:
        print 'player_info error:', ex
        msg = '查询出错'
        code = -1
        
    result = {'code':code}
    if 0 == code:
        result.update(item)
    else:
        result.update({"msg":msg})
    print result
    return HttpResponse(json.dumps(result))
        
        
        
from views.log.query import query_view 
from views.game.base import GMProtocol
from models.log import DictDefine

max_time=259200

@Route()
def player_list(request):
    '''玩家列表
    '''

    server_id = int(request.REQUEST.get('server_id','') or 0)
    player_id = int(request.REQUEST.get('player_id','') or 0)
    single = request.REQUEST.get("type","")
    query_name='玩家角色管理'

    charge_map = DictDefine.get_dict_for_key("recharge_type")
    request.POST.setlist("charge_map",charge_map.values())
    print '玩家角色管理',request.POST.getlist('server_id','')
    request.has_shutup = True
    if server_id:
        shutup_player_list = {}
        
        gmp = GMProtocol(server_id)
        result = gmp.player_shutup_list(0)
        resutl = json.dumps(result)

        for l in result[0]:
            try:
                timestamp_to_datetime_str(l[2])
            except Exception as e:
                l[2]=l[1]+max_time
            shutup_player_list[l[0]] = [timestamp_to_datetime_str(l[1]),
                                        timestamp_to_datetime_str(l[2])]
        player_ids = shutup_player_list.keys()

    if server_id and player_id and single == 'single':
        conn = Server.get_conn(server_id)
        cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        sql = """select '',p.player_id,%s,p.player_name,CONVERT(IFNULL(pp.log_level,'1'),SIGNED) level,p.channel_id,p.other,p.user_type,p.link_key,p.login_num,p.mobile_key,p.last_time,p.last_ip,p.create_time,p.status ,
        '' as action
        from player_%s p
        LEFT JOIN ( select log_user,MAX(log_level) as log_level from log_player_level group by log_user ) pp
        ON p.player_id=pp.log_user where player_id = %s"""%(server_id,server_id,player_id)
        cur.execute(sql)

        player = cur.fetchone()[0]
        conn.close()
        if player:
            last_time = player["last_time"].strftime('%Y-%m-%d %H:%M:%S')
            create_time = player["create_time"].strftime('%Y-%m-%d %H:%M:%S')
            for t in Player.TYPE_CHOICES:
                if player["user_type"] == t[0]:
                    user_type = t[1]
            for s in Player.STATUS_CHOICES:
                if player["status"] == s[0]:
                    status = s[1] 
            request.playerData = [["",player["player_id"],server_id,player["player_name"],
                                    player["level"],player["channel_id"],player["other"],user_type,
                                    player["link_key"],player["login_num"],player["mobile_key"],last_time,
                                    player["last_ip"],create_time,status,""]]

            def list_data_handle(list_data):
                new_list_data = []
                for p in request.playerData:
                    if p[1] in player_ids:
                        new_list_data.append(list(p) + shutup_player_list.get(player_id,[0,0]))
                if new_list_data:
                    return new_list_data
                return request.playerData
            return query_view(request,query_name=query_name,list_data_handle=list_data_handle)

    
    if request.REQUEST.get('is_shutup',''):
        try:
            player_ids = player_ids or [1]
            request.POST.setlist('player_id',player_ids)
            print shutup_player_list
            def list_data_handle(list_data):
                new_list_data = []
                for row in list_data:
                    player_id = row[1]
                    new_list_data.append( list(row) + shutup_player_list.get(player_id,[0,0]) )
                return new_list_data
            return query_view(request,query_name=query_name,list_data_handle=list_data_handle)
        except:
            err_msg = trace_msg()
            return HttpResponse('{"code":-1,"msg":"%s"}' % err_msg)
    else:
        try:
            def list_data_handle(list_data):
                new_list_data = []
                for row in list_data:
                    player_id = row[1]
                    if player_id in player_ids:
                        new_list_data.append(list(row) + shutup_player_list.get(player_id) )
                    else:
                        new_list_data.append(list(row))
                return new_list_data
            return query_view(request,query_name=query_name,list_data_handle=list_data_handle)
        except:
            err_msg = trace_msg()
            return HttpResponse('{"code":-1,"msg":"%s"}' % err_msg)

    return query_view(request,query_name)

# @Route()
# def player_single(request):
#     server_id = int(request.REQUEST.get('server_id','') or 0)
#     player_id = int(request.REQUEST.get("player_id",'') or 0)
#     query_name='玩家角色管理'
#     if server_id and player_id:
#         conn = Server.get_conn(server_id)
#         cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
#         sql = """select '',p.player_id,p.player_name,CONVERT(IFNULL(pp.log_level,'1'),SIGNED) level,p.channel_id,p.other,p.user_type,p.link_key,p.login_num,p.mobile_key,p.last_time,p.last_ip,p.create_time,p.status ,
#         '' as action
#         from player_%s p
#         LEFT JOIN ( select log_user,MAX(log_level) as log_level from log_player_level group by log_user ) pp
#         ON p.player_id=pp.log_user where player_id = %s"""%(server_id,player_id)
#         cur.execute(sql)
#         player_list = cur.fetchall()
#         conn.close()
#         request.data = player_list
#         def list_data_handle(list_data):
#             return request.data
#         print player_list
#         return render_to_response('player/player_single.html',locals())
#         # return query_view(request,query_name=query_name,is_query_do=True,list_data_handle=list_data_handle)
#     # return query_view(request,query_name)

def get_player_info(server_id, player_ids):
    """获取玩家信息(单个)"""
    conn = Server.get_conn(server_id)
    cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    sql = '''select player_id,player_name,channel_id,user_type,link_key,login_num,mobile_key,last_time,create_time,status,other
    from player_%s p WHERE player_id in (%s)''' % (server_id, ','.join(player_ids))
    cur.execute(sql)
    data_list = cur.fetchall()
    conn.close()
    return data_list


@Route()
@json_response
def inside_player_register(request):
    '''内部号注册
    '''
    _r = {"code": -1, "msg": "", "content": []}
    player_ids = request.REQUEST.get('player_id')
    remark = request.REQUEST.get('remark', '')
    player_ids = player_ids.split(',')
    error_player_id = []
    right_player_id = []
    print player_ids
    try:
        if player_ids:
            for player_id in player_ids:  ###############
                if player_id:
                    server_id = int(player_id) >> 20
                    InsidePlayer = Player.get_inside_player_model_class()
                    try:
                        players = get_player_info(server_id, [str(player_id)])
                    except Exception as e:
                        error_player_id.append(player_id)
                    if players:
                        for p in players:
                            p_model, created = InsidePlayer.objects.get_or_create(log_user=p['player_id'])
                            if created:
                                p_model.player_id = int(p['player_id'])
                                p_model.log_name = p['player_name']
                                p_model.log_server = server_id
                                p_model.log_time = p['create_time']
                                p_model.log_channel = int(p['channel_id']) if p['channel_id'] else 0
                                p_model.log_type = p['user_type']
                                p_model.log_relate = p['link_key']
                                p_model.mobile_key = p['mobile_key']
                                p_model.log_tag = request.admin.id
                                p_model.log_previous = p['create_time']
                                p_model.f1 = remark
                                p_model.f3 = p['other']
                                p_model.f5 = request.admin.alias
                                p_model.f6 = datetime_to_str(datetime.datetime.now())
                                p_model.save()

                                right_player_id.append(player_id)

                        _r['code'] = 0
                        _r['msg'] = '%s\n内部号标记成功!' % str(','.join(right_player_id))
                    else:
                        error_player_id.append(player_id)
                        _r['msg'] = '%s\n内部号请确认是否正确!' % str(','.join(error_player_id))
                    if error_player_id and right_player_id:
                        _r['msg'] = '%s\n内部号标记成功!' % str(','.join(right_player_id)) + '\n%s内部号请确认是否正确!' % str(
                            ','.join(error_player_id))

    except:
        err_msg = trace_msg()
        _r['msg'] = err_msg

    return _r


@Route()
def inside_player_remove(request):
    '''内部号删除
    '''
    try:
        player_ids = request.REQUEST.getlist('player_id')
        InsidePlayer = Player.get_inside_player_model_class()
        InsidePlayer.objects.filter(log_user__in=player_ids).delete()
    except:
        err_msg = trace_msg()
    return render_to_response('feedback.html',locals())


def _player_list(request,server_id=0):
    '''玩家列表
    '''
    page_size=30
    page_num=int(request.GET.get("page_num","1"))
    is_block = int(request.GET.get("block", 0))
    group_id = int(request.GET.get("group_id", 0))
    post_back = int(request.GET.get('post_back', '0'))
    
    list_group = center_cache.get_group_list()
        
    if(page_num<1):
        page_num=1

    the_user = request.admin
    
    list_channel= center_cache.get_channel_list()
    
    itemChannelList={}
    for item in list_channel:
        itemChannelList[item.id]=item.name
    
    list_group_server = [] 
    if group_id != 0: 
        list_group_server = center_cache.get_group_server_list(group_id)
    
    if request.admin.is_root:
        list_server = center_cache.get_server_list()
    else:
        list_server = center_cache.get_user_server_list(the_user)
    
    tmp_list_server = [] 
    if 0 != list_group_server.__len__():
        for item in list_group_server:
            if list_server.__contains__(item):
                tmp_list_server.append(item)
        list_server = tmp_list_server
        
    itemServerList = {}
    for item in list_server:
        itemServerList[item.id]=item.name
   
    player_key = request.GET.get('key','')
    key_type = request.GET.get('key_type','0')
    user_type = int(request.GET.get('user_type','-1'))
    channel_id = int(request.session.get('channelId','0'))
    
    server_id= int(request.GET.get("server_id","0"))
    
    if server_id<=0:
        server_id= int(request.session.get("serverId","0"))
#    if server_id<=0 and len(list_server)>0:
#        server_id=list_server[0].id
    player_keys = [player_key]
    
    if key_type == '0' and player_key:
        if ',' in player_key:
            player_keys = [ x.strip() for x  in player_key.split(',') if x ]
        if server_id<=0:
            server_id = int(player_keys[0])>>20

    #账号状态
    status_condition = 0
    if is_block == 1:
        status_condition = -1
    
    total_record=0
    player_list=[]
    player_list1=[]
    
    if 0 != post_back and  server_id>0: 
        conn = getConn(server_id)
        cursor = conn.cursor()
    
        query=[]
        query.append("status=%d" % status_condition)
        if channel_id>0:
            query.append('channel_id=%d'%channel_id)
      
        if player_key!="":
            if key_type=='0':
                query.append('player_id in (%s)'% ','.join(player_keys))
            elif key_type=='1':
                query.append('player_name like \'%s%%\''%player_key.encode('utf-8'))
            elif key_type=='2':
                query.append('link_key=\'%s\''%player_key)
            elif key_type=='3':
                query.append('mobile_key=\'%s\''%player_key)
        if user_type>-1:
            query.append('user_type=%d'%player_key)
        
        if not request.admin.is_root:
            channel_count = request.admin.get_resource('channel').count()
            if request>0:
                channel_list = request.admin.get_resource('channel')
                channel_id_list_query = ' channel_id in (%s) ' % ','.join([str(item.id) for item in channel_list])
                query.append(channel_id_list_query)
            
        if len(query)>0:
            sql1='select count(1) from player_%d where %s'%(server_id,' and '.join(query))
            sql2='select player_id,player_name,channel_id,user_type,link_key,login_num,mobile_key,last_time,create_time,status from player_%d where %s order by id desc limit %d,%d'%(server_id,' and '.join(query),(page_num-1)*page_size,page_size)
        else:
            sql1='select count(1) from player_%d'%server_id
            sql2='select player_id,player_name,channel_id,user_type,link_key,login_num,mobile_key,last_time,create_time,status from player_%d order by id desc limit %d,%d'%(server_id,(page_num-1)*page_size,page_size)
        
        print(sql1,sql2)
        cursor.execute(sql1)
        count_list=cursor.fetchone()
        total_record=int(count_list[0])
        if total_record>0:
            cursor.execute(sql2)
            player_list1=cursor.fetchall()
        user_type_name = {0:'游爱',1:'当乐',2:'UC',3:'91',4:'云游',5:'飞流',6:'乐逗',8:'小虎',9:'4399',10:'facebook',11:'qq'}
        for item in player_list1:
            item = list(item)
            item[2]=itemChannelList.get(int(item[2]),item[2])
                
            item[3]=user_type_name.get(int(item[3]),item[3])
                 
            player_list.append(item)
        cursor.close()
    parg = {}
    parg["server_id"] = server_id
    parg["list_group"] = list_group
    parg["list_server"] = list_server
    parg["player_key"] = player_key
    parg["player_list"] = player_list
    parg["is_block"] = is_block
    parg['key_type'] = key_type
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    group_servers_dict = get_group_servers_dict(request)
    agent_channels_dict = get_agent_channels_dict(request)
    return render_to_response('player/player_list.html',locals())

# def player_info(request,playerId):
#    return render_to_response('player/player_info.html')
#
#
#def user_login(request):
#    from django.http import HttpResponse
#    import time
#    response = HttpResponse()
#    response['Content-Type']='application/json'
#    timestamp = int(time.time())
#    return render_to_response('player/user_login.html',locals())

@Route()
def role_transfer(request):
    '''角色转移
    '''
    _r = 'fail'
    oid = int(request.POST.get('oid', '0') or 0)
    nid = int(request.POST.get('nid', '0') or 0)

    if oid and nid:
        o_sid = int(oid)>>20
        n_sid = int(nid)>>20
        if o_sid == n_sid:
            try:
                conn = getConn(o_sid)
                query_sql = "select link_key,user_type from player_{0} where player_id in ({1},{2})".format(o_sid,oid,nid)
                print '=====>:',query_sql
                cur = conn.cursor()
                cur.execute(query_sql)
                user_list = cur.fetchall()
                if len(user_list) > 1:
                    n_key = user_list[0][0]
                    n_user_type = int(user_list[0][1])
                    o_key = user_list[1][0]
                    o_user_type = int(user_list[1][1])

                    sql1 = "update player_%s set link_key='%s',user_type=%d where player_id=%d" % (o_sid,n_key,n_user_type,oid)
                    sql2 = "update player_%s set link_key='%s',user_type=%d where player_id=%d" % (o_sid,o_key,o_user_type,nid)
                    cur.execute(sql1)
                    cur.execute(sql2)
                    #print sql1,sql2
                    _r = 'OK!'

            except Exception,e:
                err_msg = trace_msg()
                _r = err_msg


    return HttpResponse(json.dumps(_r))






