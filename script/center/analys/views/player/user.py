#! /usr/bin/python
# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Q
from models.center import User, SafeQuestion,RebateUser
from models.center import Channel
from views.base import md5, getConn
from cache import center_cache
from django.db import connection
import json
import datetime
from urls.AutoUrl import Route
from views.log.query import query_view
from views.widgets import get_group_servers_dict,get_agent_channels_dict
from models.channel import Channel,Agent,ChannelOther
from views.game.base import GMProtocol



#设备白名单
mobile_white = ["ea376ee490575bc035125a51af5b39d6"]

def user_list(request):
    channel_id = int(request.session.get('channelId', '0'))
    if channel_id > 0:
        channel = center_cache.get_channel_list()
    
    page_size = 30
    page_num = int(request.GET.get('page_num', '1'))
    if page_num < 1:
        page_num = 1
    
    user_type = int(request.GET.get('type', '-1'))
    user_key = request.GET.get('key', '')
    user_status = request.GET.get('select_status','')
    model = User()
    query = Q()
     
    query = Q(user_type=0)
        
    if user_key != '':
        key_type = int(request.GET.get('key_type', '0'))
        if key_type == 0:
            try:
                query = query & Q(username=user_key)
            except:
                print('key_value has error')
        elif key_type == 2:
            query = query & Q(mobile_key=user_key)
        else:
            query = query & Q(username__icontains=user_key)
            
    if channel_id > 0:
        query = query & Q(channel_key=channel.key)

    if user_status:
        query = query & Q(status = user_status)

    list_record = []
    if query:
        total_record = User.objects.using('read').filter(query).count()
        if total_record > 0:
            list_record = User.objects.using('read').filter(query)[(page_num - 1) * page_size:page_num * page_size]
    else:
        total_record = User.objects.using('read').count()
        if total_record > 0:
            list_record = User.objects.using('read').all()[(page_num - 1) * page_size:page_num * page_size]

    parg = {}
    parg["user_key"] = user_key
    parg["list_record"] = list_record
    parg["status_choices"] = User.STATUS_CHOICES
    parg["user_status"] = int(user_status) if user_status else 0

    parg["request"] = request
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    
    return render_to_response('player/user_list.html', parg)

from util import trace_msg
def user_unlock(request):
    uid = int(request.REQUEST.get('uid','') or 0)
    
    try:
        if uid:
            # User.objects.filter(id=uid).update(lock_time=None)
            user = User.objects.filter(id=uid)
            user.update(lock_time=datetime.datetime.now())
            user.update(last_time=datetime.datetime.now())
            err_msg = '%s  解锁成功!' % uid
    except:
        err_msg = trace_msg()   
    return HttpResponse(err_msg)

    
def user_lock(request, user_id=0, is_lock=0):
    
    model_id = int(user_id)
    is_lock = int(is_lock)

    if model_id == 0:
        model_id = int(request.GET.get('user_id', '0'))
    if is_lock == 0:
        is_lock = int(request.GET.get('is_lock', '0'))
    
    if model_id > 0 :
        try:
            model = User.objects.get(id=model_id)
            if model.mobile_key in mobile_white:
                print '设备白名单'
                return
            if is_lock == 1:
                if not model.is_lock():
                    # model.status -= 5
                    model.status = -1
            else:
                if model.is_lock():
                    # model.status += 5
                    model.status = model.user_type

            model.lock_time = datetime.datetime.now()
            model.last_time = datetime.datetime.now()
            model.save(using='write')
        except Exception, e:
            print('lock user error:', e)
    
    return render_to_response('feedback.html')

def user_password(request, user_id=0):
    user_id = int(user_id)
    
    if user_id == 0:
        user_id = int(request.GET.get('user_id', '0'))
    
    msg = ''
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if user_id > 0 and password != '':
            try:
                the_user = User.objects.get(id=user_id, user_type=0)
                the_user.password = md5(password.lower())
                the_user.lock_time = None
                the_user.save(using='write')
                
                msg = '操作成功!'        
            except Exception, e:
                print('set password error:', e)
                msg = e
    
    parg = {}
    parg["user_id"] = user_id
    parg["msg"] = msg

    return render_to_response('player/user_password.html', parg)

def modify_mibao(request,user_id=0):
    user_id = user_id or int(request.GET.get('user_id', request.POST.get('user_id', '0')))
    
    code = 1
    err_msg = ''
    if user_id != 0:
        try:
            the_user = User.objects.get(id=user_id, user_type=0)
            if  the_user:
                safequestion_list = the_user.safequestion_set.all()
                if len(safequestion_list) >0 :
                    safequestion = safequestion_list[0]
                    question = request.POST.get('question', '')
                    answer = request.POST.get('answer', '')
                    if question and answer:
                        safequestion.question = question.strip()
                        safequestion.answer = answer.strip()
                        safequestion.save(using='write')
                        return render_to_response('feedback.html')
            else:
                err_msg = '没有此账户'
        except Exception,e:
            err_msg = str(e) 
    return render_to_response('player/user_mibao.html', locals())

def clear_mibao(request, user_id=0):
    user_id = int(user_id)
    
    code = 1
    msg = ''
    
    if user_id == 0:
        user_id = int(request.GET.get('user_id', request.POST.get('user_id', '0')))
        the_user = User.objects.get(id=user_id, user_type=0)
        if None != the_user:
            safeQuestion_list = SafeQuestion.objects.filter(user = the_user)
            for item in safeQuestion_list:
                item.delete(using='write')
            code = 0
            msg = '操作成功!'
        else:
            msg = '账号不存在'
    if request.is_ajax() or request.REQUEST.get('ajax',''):
        return HttpResponse('{"code":%s, "msg":"%s"}' % (code, msg))
    else:
        return HttpResponse(msg)

def user_convert(request, server_id=0):
    server_id = int(server_id)
    err_msg = ''
    if server_id > 0:
        try:
            conn = getConn(server_id)
        except:
            err_msg = '数据库链接出错!'
    else:
        conn = connection
    if err_msg != '':
        parg = {}
        parg["err_msg"] = err_msg
        return render_to_response('feedback.html', parg)
    cursor = conn.cursor()
    
    start_pos = int(request.GET.get('pos', 0))
    if start_pos == 0:
        query_sql = 'select id from log_create_role where log_user=(select max(player_id) from player_%d)' % (server_id,)
        cursor.execute(query_sql)
        last_player_id = cursor.fetchone()
        if last_player_id != None:
            start_pos = int(last_player_id[0])
    

    sql = 'select log_user,log_result,f1,log_time,id from log_create_role where id>%d order by id limit 100' % start_pos
    cursor.execute(sql)
    list_record = cursor.fetchall()
    for item in list_record:
        try:
            #先判断存在与否
            sql = 'select count(0) from player_%d where player_id=%d' % (server_id, item[0])
            cursor.execute(sql)
            count_list = cursor.fetchone()
            total_record = int(count_list[0])
            
            if total_record == 0:
                the_user = User.objects.using('read').get(id=item[1])
                if the_user.user_type == 0:
                    link_key = the_user.id
                else:
                    link_key = the_user.link_key
                channel_id = 0
                try:
                    the_channel = Channel.objects.using('read').get(channel_key=the_user.channel_key)
                    channel_id = the_channel.id
                except:
                    pass
                try:
                    sql = '''insert into player_%d(player_id,player_name,user_type,link_key,channel_id,create_time,last_ip,last_time,login_num,status,mobile_key)
                            values(%s,"%s",%s,"%s",%s,"%s","%s","%s",0,0,"%s")''' % (server_id, item[0], item[2].replace('\\', '\\\\'), the_user.user_type, link_key, channel_id, item[3], the_user.last_ip, the_user.last_time, the_user.mobile_key)
                    cursor.execute(sql)
                except Exception, e:
                    print('convert user has error', e, item[0])
        except Exception, e:
            print('convert user has error', e, item[0])
        start_pos = item[4]
    is_reload = True
    if len(list_record) < 100:
        err_msg = '同步完成!'
        is_reload = False
    cursor.close()
    
    parg = {}
    parg["server_id"] = server_id
    parg["start_pos"] = start_pos
    parg["is_reload"] = is_reload
    parg["err_msg"] = err_msg
    
    return render_to_response('player/user_convert.html', parg)

def user_status_edit(request):
    '''修改帐号状态
    '''
    _r = {"code":1}
    user_list = request.POST.getlist('uid')
    if not user_list:
        return HttpResponse('没有选择帐号!')
    try:
        datas = User.objects.filter(id__in=user_list)
        status = int(request.POST.get('user_status','') or 0)
        if status == 4:
            datas.lock_time = datetime.datetime.now()
        datas.using('write').update(status=status)
        datas.using('write').update(lock_time = datetime.datetime.now())
        datas.using('write').update(last_time = datetime.datetime.now())
        _r["code"] = 0
        _r["msg"] = '修改成功!'
    except:
        _r["msg"] = trace_msg()

    return HttpResponse(json.dumps(_r))


@Route()
def white_user(request):
    channels = Channel.objects.all()
    _channels = []
    for channel in channels:
        _channels.append({'channel_key':channel.channel_key,'name':channel.name})
    request.channel_agent = _channels
    request.POST.setlist('agent',[_channels])

    return query_view(request,query_name='白名单列表')

@Route()
def white_user_edit(request):
    msg = ""

    userId = int(request.POST.get('userId',0))
    if userId:
        try:
            model = User.objects.get(id = userId)
        except:
            msg = "账号有误"

        if msg:
            _r = {"code":-1,"msg":msg}
            return HttpResponse(json.dumps(_r))

        userData = {}
        userData["userAccount"] = model.username
        userData["channel_key"] = model.channel_key
        if model.other_data:
            other = json.loads(model.other_data)
            userData["userName"] = other["userName"]
            userData["department"] = other["department"]

        return HttpResponse(json.dumps(userData))
    return HttpResponse(json.dumps(_agents))


@Route()
def white_user_save(request,model_id=0):
    model_id = int(model_id)
    model_id = int(request.POST.get('id', '0')) if not model_id else model_id
    model_id = int(request.GET.get('id', '0')) if not model_id else model_id
    print model_id
    msg = ''

    model_account = request.POST.get("account")

    print model_account

    model = None
     
    if not model_id and not model_account:
        return HttpResponse(json.dumps({"code":-1,"msg":"账号有误"}))
        
    # else:
    try:
        if model_id:
            model = User.objects.get(id = model_id)
        elif model_account:
            model = User.objects.get(username = model_account)
    except:
        msg = "账号有误"

    if not model:
        return HttpResponse(json.dumps({"code":-1,"msg":"账号有误"}))
    
    if not request.admin.is_root:
        msg = '非法操作'
    else:
        other = {}
        other["userName"] = request.POST.get("userName","")
        other["department"] = request.POST.get("department","")
        other["creatTime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        model.other_data = json.dumps(other)
        model.channel_key = request.POST.get("channel_key","")
        model.status = 4
        model.lock_time = datetime.datetime.now()
        if not msg:
            try:
                model.save(using='write')
            except Exception, ex:
                msg = '保存出错'
    
    if msg:
        _r = {"code":-1,"msg":msg}    
        return HttpResponse(json.dumps(_r))
    return HttpResponse(json.dumps({"code":0,"msg":"保存成功"}))


@Route()
def del_white_user(request):
    userId = int(request.POST.get("userId",0))
    msg = ""
    model = None
    if userId:
        try:
            model = User.objects.get(id = userId)
        except:
            msg = "账号有误"

    if model:
        model.other_data = None
        model.status = 0
        model.lock_time = datetime.datetime.now()
        try:
            model.save(using='write')
        except:
            msg = '删除出错'

    if msg:
        _r = {"code":-1,"msg":msg}
        return HttpResponse(json.dumps(_r))
    return HttpResponse(json.dumps({"code":0,"msg":"删除成功"}))


@Route()
def sign_charge_user(request):
    userlist = json.loads(request.POST.get('users')) or []
    unsignUser = [] 
    for user in userlist:
        model = None
        try:
            model = User.objects.get(username=user)
        except:
            unsignUser.append(user)
            continue

        if model:
            # (1,'充值返利未发送')
            model.recharge_status = '[1]'
            try:
                model.save(using='write')
            except:
                print '保存失败'
                continue

    if unsignUser:
        _r = {"code":-1,"msg":"%s 标记失败"%unsignUser}
        return HttpResponse(json.dumps(_r))
    return HttpResponse(json.dumps({"code":0,"msg":"标记成功"}))

@Route()
def send_rebate_user(request):
    userdict= json.loads(request.POST.get('users')) or {}
    if userdict:
        for user in userdict:
            model = None
            try:
                model = RebateUser.objects.get(username=user)
            except BaseException as e:
                print e

            if not model:
                model = RebateUser()

            if model:
                # 写入充值数返利
                model.username = user
                model.pay_reward = int(userdict[user]) if not model.pay_reward else int(userdict[user]) + int(model.pay_reward)
                model.expire_time = datetime.datetime.now() + datetime.timedelta(days=35)  
                model.last_time = datetime.datetime.now()
                model.server_id = 0
                try:
                    model.save(using='write')
                except BaseException as e:
                    print '%s 保存失败:%s'%user,e
                    continue
        return HttpResponse(json.dumps({"code":0,"msg":"保存成功"})) 
    return HttpResponse(json.dumps({"code":-1,"msg":"没有选择用户"}))


@Route()
def sign_login_user(request):
    userlist = json.loads(request.POST.get('users')) or []
    if userlist:
        for user in userlist:
            model = None
            try:
                model = RebateUser.objects.get(username=user)
            except BaseException as e:
                print e

            if not model:
                model = RebateUser()

            if model:
                # 写入充值数返利
                model.username = user
                model.login_reward = 1
                model.expire_time = datetime.datetime.now() + datetime.timedelta(days=35)  
                model.last_time = datetime.datetime.now()
                model.server_id = 0
                try:
                    model.save(using='write')
                except BaseException as e:
                    print '%s 保存失败:%s'%user,e
                    continue
        return HttpResponse(json.dumps({"code":0,"msg":"保存成功"})) 
    return HttpResponse(json.dumps({"code":-1,"msg":"没有选择用户"}))















