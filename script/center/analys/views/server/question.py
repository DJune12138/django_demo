#! /usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from models.admin import Admin
from models.channel import Agent,Channel 
from models.server import Server ,Group
from models.log import DictDefine
from django.db.models import Q
from django.db import connections
from models.center import  Question,QuestionOther,VipList
from django.http import HttpResponse
from cache import center_cache, memcached_util 
from views.base import md5
import json, MySQLdb, datetime,time
import os,json
from views.base import notauth

from django.core.serializers import serialize,deserialize
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from views.widgets import get_group_servers_dict,get_agent_channels_dict

from urls.AutoUrl import  Route
import traceback
from util.threadpoll import async
import settings
from settings import STATIC_ROOT

def get_category_list():
    _category_dict = {}
    try:
        category_dict = DictDefine.objects.using('read').get(key="question_category").get_dict()
        category_list = []
        #键为分类 值为父分类:
    
        for k,v in category_dict.iteritems():
            _category_dict.setdefault(v,[])
            if k!=v:
                _category_dict[v].append(k)
    except:
        pass
    return _category_dict

def convert_dict_datetime(_dict):
    _d = {}
    for k,v in _dict.iteritems():
        _v = v
        if isinstance(v,datetime.datetime):
            _v = v.strftime('%Y-%m-%d %H:%M:%S')
        _d[k] = _v 
    return _d

def manage_question_order(request):
    '''设置客服接单时间
    '''
    question_id = request.REQUEST.get('qid','')
    _r = {"code":1,"msg":"error","data":[]}
    try:
        if question_id:
            question = Question.objects.get(id=question_id)
            if not question.order_time:
                question.order_time=datetime.datetime.now()
            the_user_id = int(request.admin.id)
            if not question.order_user and the_user_id > 0:
                order_user = Admin.objects.get(id=the_user_id)
                question.order_user = order_user.username
                question.save()
                question_dict = convert_dict_datetime(model_to_dict(question))
                _r["data"].append(question_dict)
            _r["code"] = 0
            _r["msg"] = ""
    except Exception,e:
        _r["msg"] =  str(e)
    return HttpResponse(json.dumps(_r))

def manage_question_allocation(request):
    '''指派问题
    '''
    question_ids = request.REQUEST.getlist('question_id')
    order_user = request.REQUEST.get('order_user','')
    _r = {"code":1,"msg":"error","data":[]}
    try:
        if question_ids and order_user:
            now = datetime.datetime.now()
            Question.objects.filter(id__in=question_ids).update(order_user=order_user,order_time=now)
            _r["code"] = 0
            _r["msg"] = ""
    except Exception,e:
        _r["msg"] =  str(e)
    return HttpResponse(json.dumps(_r))

def get_kefu_question_info(kefu_list):
    '''获取客服状态信息
    '''
    conn = connections['read']
    sql = '''SELECT order_user,count(0),min(order_time)
    FROM question
    WHERE status=0 AND order_user in (%s)  AND post_time>='2014-09-25 00:00:00' 
    GROUP BY order_user
    ''' % ','.join([ "'%s'" % x.username.replace('%','%%') for x in kefu_list])
    cur = conn.cursor()
    cur.execute(sql)
    _r = {}
    for row in cur.fetchall():
        _r[row[0]] = [row[1],row[2]] #最早的接单时间
    return  _r

def get_kefu_list():
    return Admin.get_kefu_list()

def query_parent_question(request,template='server/child_question_list.html'):
    '''查询服问题
    '''
    sid = int( request.REQUEST.get('sid','') or 0 )
    if sid:
        list_record = Question.objects.using('read').filter(Q(session_id=sid)|Q(id=sid)).order_by('id')
    return render_to_response(template, locals())

def manage_question_list(request, user_id=0, status= -1,is_myqustion=False,other_param={}):
    '''问题列表
    '''
    if request.REQUEST.get('route','') == 'order_question':
        return manage_question_order(request)
    if request.REQUEST.get('route','') == 'allocation_question':
        return manage_question_allocation(request)
    if request.REQUEST.get('route','') == 'query_parent_question':
        return query_parent_question(request)
    
    ajax = request.REQUEST.get('ajax', False)
    if status == -1 :
        status = int(request.REQUEST.get('status', '-1'))
    
    search_type = int(request.REQUEST.get('search_type', '-1'))
    question_type = int(request.REQUEST.get('question_type', '-1'))
    question_category = request.REQUEST.get('question_category', '')
    page_size = request.REQUEST.get('page_size', 20)
    group_id = int(request.REQUEST.get('group_id', -1))
    kefu_name = request.REQUEST.get('kefu_name', '')
    sdate = request.REQUEST.get('sdate','')
    edate = request.REQUEST.get('edate','')
    template = request.REQUEST.get('template', request.POST.get('template', 'question_list'))
    
    vip = -1
    try:
        vip = int(request.REQUEST.get('vip', -1))
    except:
        vip = -1

    
    usm = request.admin
    
    server_id = int(request.REQUEST.get('server_id', '0'))
    
    if user_id == 0 or user_id == '0':
        user_id = request.REQUEST.get('user_id', '')
    
    status = int(status)
    page_num = int(request.REQUEST.get('page_num', '1'))
    page_size = int(page_size)
    if page_size > 1000:
        page_size = 20
    total_page = 1
    if page_num < 1:
        page_num = 1
    

    query = Q()
    
    if user_id != '':
        if search_type == 1:
            query = query & Q(post_user=user_id)
        elif search_type == 2:
            query = query & Q(question__contains = user_id)
        elif search_type == 3:
            query = query & Q(score=user_id)
          
    
    if -1 != vip:
        query = query & Q(post_user_id = vip)
    
    if -1 != question_type:
        query = query & Q(question_type=question_type)
        
    if '' != question_category:
        query = query & Q(category=question_category)
    
    if '' != kefu_name:
        query = query & Q(reply_user = kefu_name)
        
    if sdate and edate:
        query = query & Q(post_time__range=(sdate,edate)) 
            
    if status != -1:
        query = query & Q(status=status)        

    
    group_servers_dict,server_list = get_group_servers_dict(request,get_server_list=True)
    agent_channels_dict,channel_list = get_agent_channels_dict(request,get_channel_list=True)
    
    server_map = {}
    for server in server_list:
        server_map[server.id] = server
    channel_map = {}
    for channel in channel_list:
        channel_map[channel.id] = channel
        
    server_ids = request.REQUEST.getlist('server_id')
    channel_ids = request.REQUEST.getlist('channel_id')
    
    #限制渠道及服务器
    server_ids = server_ids or [item.id for item in server_list]
    channel_ids = channel_ids or [item.id for item in channel_list]
    query = query & Q(server_id__in = server_ids)
    if request.admin.is_manager:
        channel_ids.append(0)
        
    query = query & Q(channel_id__in = channel_ids)
        

    total_record = Question.objects.using('read').filter(query).count()
    list_record = Question.objects.using('read').filter(query)[(page_num - 1) * page_size:page_num * page_size]
    
    for item in list_record:
        item.question = item.question.replace('\n', '')
        if item.server_id > 0:
            item.serverName = server_map.get(item.server_id, '--')
        else:
            item.serverName = "--"
        channel = channel_map.get(item.channel_id, None)
        if None != channel:
            item.channel = channel.name
        else:
            item.channel = '未知渠道'
        if item.question_type == 4:#战报
            other_models = QuestionOther.objects.using('read').filter(qid=item.id).values('data')
            print other_models 
            if other_models:
                item.br_url =  '%s%s' % (settings.SERVICE_URL,other_models[0]['data'])
    if total_record > page_size:
        total_page = total_record / page_size
        if total_record % page_size > 0:
            total_page += 1
    
    kefu_list = get_kefu_list()
    parg = {}
    server_ids = [ int(s) for s in server_ids]
    channel_ids = [ int(c) for c in channel_ids]
    question_category_list = get_category_list()
    TYPE_MAP = Question.TYPE_MAP
    if ajax:  
        return render_to_response('server/question_list_block.html', locals())
    

    return render_to_response('server/%s.html' % template, locals())

from views.game.base import GMProtocol

@async
def tell_question_status_to_game_server(qm):
    '''回复后异步通知服务端
    '''
    try:
            server_id = qm.server_id
            player_id = qm.post_user
            gmp = GMProtocol(server_id)
            result = gmp.post_question_status(player_id)
    except:
        traceback.print_exc()
        
#客服回复问题（如果是渠道后台,则需要判断被回复的玩家所在渠道是否在本渠道）
def manage_question_answer(request):
    question_id = int(request.POST.get('question_id', 0))
    cover = request.POST.get('cover', request.POST.get('cover', ''))
    answer = request.POST.get('answer', '')

    reply_name = request.POST.get('reply_user', 'admin')
    _d = {"code":1}
    
    question = None
    
    if question_id > 0:
        question = Question.objects.get(id=question_id)
    
    if answer != '' and question != None:        
        question.answer = answer
        reply_name = request.admin.username
        question.reply_user = reply_name
        question.status = 1
        if not question.reply_time:
            question.reply_time = datetime.datetime.now()
        category = request.REQUEST.get('answer_category', '')
#        if not category or category=="未分类": #强制选择类型
#            return HttpResponse('请选择问题类型')
        question.category = category
        question.save(using='write')
        
        tell_question_status_to_game_server(question)
        
        _d["code"] = 0
        _d["reply_user"] = reply_name
        _d["reply_time"] = question.reply_time_str()


    return HttpResponse(json.dumps(_d))
    
def edit_category(request):
    code = 0
    msg = ''
    g = lambda x,y:request.GET.get(x,request.POST.get(x,y))
    gl = lambda x,y:request.GET.getlist(x, request.POST.getlist(x,y))
    ajax = g('ajax', '')
    
    usm = request.admin
    if not usm.is_manager:
        code = 1
        msg = '非法操作'
    
    question_id_array = gl('id', '')
    if question_id_array.__len__() == 0:
        tmp = g('id', '')
        if tmp != '':
            question_id_array = [tmp]
    category = g('category', '')
    if category == '':
        code = 1
        msg = '请输入类别名称'
    
    question_id_array = [int(item) for item in question_id_array]
    
    error_count = 0
    if code == 0:
        question_list = Question.objects.filter(id__in=question_id_array)
        for item in question_list:
            item.category = category
            try:
                item.save()
            except Exception, ex:
                error_count += 1
                continue
        
        if error_count != 0:
            code = -1
            msg = '保存中发送错误，保存出错%s个' % error_count
        
    if ajax != '':
        return HttpResponse('{"code":%d,"msg":"%s"}' % (code, msg))
    
    if code == 0:
        msg = "操作成功"
    
    return HttpResponse(msg)
    

def manage_question_remove(request, question_id=0):
    question_id = int(question_id)
    ajax = request.GET.get('ajax', False)

    #新增忽略，更改状态+3,取消忽略-3恢复到原状态
    ignore = request.POST.get('type',None)
    if ignore:
        question_ids = request.POST.getlist('question_ids',None)
        if not question_ids:
            _r = {"code":1,"msg":"无问题ID"}
            return HttpResponse()
        for qid in question_ids:
            question = Question.objects.get(id=int(qid))
            if question:
                if question.status-3 < 0 and ignore == "removeIgnore":
                    continue
                if question.status +3 > 5 and ignore == "ignore":
                    continue
                question.status += 3 if ignore=='ignore' else -3
                question.save(using='write')
        _r = {"code":0,"msg":"忽略成功"}
        return HttpResponse(json.dumps(_r, ensure_ascii=True))

    question = None 
    if question_id < 1:
        question_id = int(request.GET.get('question_id', '0'))
    
    if question_id > 0:
        question = Question.objects.get(id=question_id)
    
    if question != None:
        question.delete(using='write')
        
    if ajax : 
        return HttpResponse("删除成功！")

    return render_to_response('feedback.html')

@Route()
def myquestion(request):
    request.POST._mutable = True
    request.GET._mutable = True  
    try:
        now = datetime.datetime.now()
        other_param = {}
        limit_question_num = 10
        order_num = int(request.REQUEST.get('order_num','') or -1)
        groups = Group.objects.filter(key='kefuserver').prefetch_related('server')
        is_query_user_question = request.REQUEST.get('is_query','')
        group_id = int(request.REQUEST.get('group_id','') or 0 )
        sdate = request.REQUEST.get('sdate','')
        edate = request.REQUEST.get('edate','')
        usm = UserStateManager(request)
        the_user = usm.get_the_user()

        if not is_query_user_question:
            group = groups[0]
            the_user_id = int(request.session.get('userid', '0'))
            servers = group.server.all().values('id')
            server_ids = [ s['id'] for s in servers]
            request.POST.setlist('group_id',[group_id or group.id])
            kefu_name = the_user.username
            
            base_query = Q(status__lt=1) & Q(server_id__in=server_ids) & (Q(reply_user__isnull=True)|(Q(reply_user=''))) #属于游爱的没被接的单
            base_query = base_query & Q(post_time__gte=datetime.date(2014, 9, 25))    #限定从今天开始接单
            base_query = base_query & ~Q(channel_id__in=[97,1288]+range(904,944)+[948,952])
            if not usm.is_kefu_manager() :                   
                request.POST.setlist('kefu_name',[kefu_name])
                request.POST.setlist('group_id',[ group.id]) #限定服务器
                request.POST.setlist('server_id',server_ids)
                
            else:
                not_order_query = Q(Q(order_user__isnull=True)|(Q(order_user=''))) & base_query
                other_param['not_order_num'] = Question.objects.using('read').filter(not_order_query).count()

            if order_num > 0 :                              
                request.POST.setlist('group_id',[ group.id])  #接单限定
                request.POST.setlist('kefu_name',[kefu_name])
                
                query = Q(order_user=kefu_name) & base_query                                      #已接单没回复的数量
                kefu_not_reply_num = Question.objects.using('read').filter(query).count()         #客服没回复的数量
                epos = 0
                if kefu_not_reply_num < limit_question_num:                                         
                    query = base_query  & (Q(order_user__isnull=True)|(Q(order_user='')))         #没有回复及接单的问题
                    epos = order_num
                    if (kefu_not_reply_num + epos) > limit_question_num:
                        epos = limit_question_num - kefu_not_reply_num
                    max_question_num = 100
                    not_order_question_ids = []
                    not_order_question = list(Question.objects.filter(query)\
                                                  .values_list('id','post_time')\
                                                  .order_by('status','-post_user_id','id')[:max_question_num]
                                                  )
                    
                    for id,post_time in reversed(not_order_question):
                        if ( now - post_time ).seconds > 60 * 10 : #大于10分钟的优先
                            not_order_question_ids.append(id)

                        if len( not_order_question_ids ) >= epos:
                            break
                    
                    if not_order_question_ids:
                        kefu_not_reply_num += epos
                        not_order_question_ids = not_order_question_ids[:epos]
                        
                    query = query & Q(id__in=not_order_question_ids)
                    update_questions =  Question.objects.filter(query)
                    update_questions.update(order_user=kefu_name,order_time=now)
                other_param['kefu_not_reply_num'] = kefu_not_reply_num 
                print kefu_not_reply_num,epos
        other_param['is_myqustion'] = True
        other_param['is_query'] = is_query_user_question
        return manage_question_list(request,is_myqustion=True,other_param=other_param)
    except Exception,e:
        traceback.print_exc()
        return HttpResponse(str(e))
        
    
    
@Route()
def edit_kefu_server(request):
    '''客服服务器
    '''
    try:
        group_id = Group.objects.filter(key='kefuserver')[0].id
    except:
        return HttpResponse('没有建立客服服务器分区!')
    return group_edit(request,group_id)

def viplist(request,template='server/viplist.html'):
    '''viplist
    '''
    path = os.path.join(STATIC_ROOT, 'vip')
    filename = os.path.join(path,'pick.json')
    if not os.path.exists(path):
        os.makedirs(path)
        os.mknod(filename)
    #读取本地VIP礼包配置json文件
    try:
        if os.path.isfile(filename):
            fp = open(filename,'r')
            msg = json.loads(fp.read())
            fp.close()
    except Exception,e:
        pass

    list_record = VipList.objects.all()
    for i in list_record:
        i.privilege_type = '%s(%s)' %(VipList.TYPE_CHOICES[i.privilege_type][1],i.privilege_type)
        i.everyday_type = '%s(%s)' %(VipList.TYPE_CHOICES[i.everyday_type][1],i.everyday_type)

    return render_to_response(template, locals())

def viplist_save(request):
    '''保存VIP礼包json && 验证角色ID
    '''
    result = {'code':-1,'msg':""}
    req_type = request.POST.get('req_type','')
    path = os.path.join(STATIC_ROOT, 'vip')
    filename = os.path.join(path,'pick.json')
    if not os.path.exists(path):
        os.makedirs(path)
        os.mknod(filename)
    if req_type == 'pick':
        msg_json = request.POST.get('msg','')
        try:
            fp = open(filename,'w')
            fp.write(msg_json)
            fp.close()
            result['code'] = 0

        except Exception,e:
            print traceback.print_exc()

    if req_type == 'playerid':
        msg_json = request.POST.get('msg','')
        pids = json.loads(msg_json)
        fail_list = []
        try:
            for i in pids:
                viplist = VipList.objects.using('write').filter(Q(player_id=i)&Q(privilege_type=0))
                if viplist:
                    viplist[0].privilege_type = 1
                    viplist[0].save(using='write')
                else:
                    fail_list.append(i)

            if not fail_list:
                result['code'] = 0
            else:
                result['code'] = 1
                result['msg'] = json.dumps(fail_list)

        except Exception,e:
            print traceback.print_exc()

    model_id = int(request.GET.get('model_id','0'))
    if model_id > 0:
        privilege_type = int(request.POST.get('privilege_type','-1'))
        everyday_type = int(request.POST.get('everyday_type','-1'))
        if privilege_type != -1 or everyday_type != -1:
            try:
                viplist = VipList.objects.using('write').filter(id=model_id)
                if viplist:
                    viplist[0].privilege_type = privilege_type
                    viplist[0].everyday_type = everyday_type
                    viplist[0].save(using='write')
                    result['code'] = 0
                    result['msg'] = 'OK'
                else:
                    result['msg'] = 'vip_model is none'

            except Exception,e:
                print traceback.print_exc()

    return HttpResponse(json.dumps(result))

def viplist_edit(request,model_id=0,template='server/viplist_edit.html'):
    parg = {}
    model_id = int(model_id)
    if model_id == 0:
        model_id = int(request.GET.get('model_id','0'))
    model = None

    if model_id > 0:
        model = VipList.objects.using('read').get(id=model_id)
    if model == None:
        model = VipList()
        model.id = 0

    parg["model"] = model

    return render_to_response(template, parg)

@Route()
@notauth
def get_vipmsg(request):
    '''客户端获取VIP信息
    '''
    result = {'codo':-1}
    player_id = int(request.REQUEST.get("player_id",'') or 0)
    server_id = int(request.REQUEST.get("server_id",'') or 0)
    pick_id = request.REQUEST.get('pick_id','')
    if player_id and not pick_id:
        viplist = VipList.objects.using('read').filter(Q(player_id=player_id))
        if viplist:
            result['codo'] = 0
            result['pt'] = viplist[0].privilege_type
            result['et'] = viplist[0].everyday_type

    elif player_id and pick_id and server_id:
        path = os.path.join(STATIC_ROOT, 'vip')
        filename = os.path.join(path,'pick.json')
        try:
            #读取本地VIP礼包配置json文件
            if os.path.isfile(filename):
                fp = open(filename,'r')
                msg = json.loads(fp.read())
                fp.close()

            vip_models = VipList.objects.using('read').filter(Q(player_id=player_id))
            gmp = GMProtocol(server_id)
            gmp.time_out = 10
            if int(pick_id) == 0 and vip_models[0].privilege_type == 1:
                msg_info = msg[0]["info"]
                code = gmp.send_card_resouces(player_id,'VIP客服特权礼包',msg_info)
                result['codo'] = code

            elif int(pick_id) == 1 and vip_models[0].everyday_type == 1:
                msg_info = msg[1]["info"]
                code = gmp.send_card_resouces(player_id,'VIP客服每日礼包',msg_info)
                result['codo'] = code
            #print "##",code
            if int(code) == 0:
                if int(pick_id) == 0:
                    vip_models.update(privilege_type=2)
                else:
                    vip_models.update(everyday_type=2)

        except Exception,e:
            print traceback.print_exc()

    return HttpResponse(json.dumps(result))




