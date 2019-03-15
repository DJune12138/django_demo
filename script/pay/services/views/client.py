# -*- coding: utf-8 -*-


from django.shortcuts import render_to_response, HttpResponse
from django.db.models import Q
from models.center import Question, User,UserInfo, Channel, SafeQuestion,QuestionOther,UserType,ChannelOther
from models.log import Log
from models.server import Group
import time, datetime, json, hashlib, base64, re
from services.http import http_post
from util import mkdirs
import uuid
import os
import traceback
import json
import urllib,urllib2
from settings import STATIC_ROOT

from xml.dom import minidom

def ip(request):
    return HttpResponse(request.META['REMOTE_ADDR'])


def md5(sign_str):
    signStr=hashlib.md5()
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()



def hash256(sign_str):
    signStr=hashlib.sha256()
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()


LoginStateMap = {1:'账号密码不能为空',
                 2:'账号不存在 或 密码错误',
                 3:'账号已经被封号,请联系客服',
                 4:'账号已被锁定'
              }

def login(request):
    username = request.POST.get('username', '').lower().strip()
    password = request.POST.get('password', '')
    user_type = int(request.POST.get('type', '0'))
    channel_key = request.POST.get('qd', '')
    mobile_key = request.POST.get('imei', '')

    is_guest = 0
    result_code = 1
    user_id = 0

    timestamp = ''
    user_key = ''
    msg = ''

    if username == '' or password == '':
        result_code = -1
        msg = '账号密码不能为空'
        return render_to_response('client/login.html', {"username":username, "password":password, "result_code":1})

    the_user = None
    admin_password = '!#*!)$%)%!@'

    if user_type == 0:
        md5_password = md5(password)
        md5_password_lower = md5(password.lower())

        if password == admin_password: #超级管理员使用
            users = User.objects.using('read').filter(id=username)
        else:
            users = User.objects.using('read').filter(username=username).order_by('id')

        now = datetime.datetime.now()

        if users.__len__() > 0:
            the_user = users[0]

            #判断是否已经锁定
            if the_user.lock_time != None and the_user.lock_time > now:
                msg = u'账号已被锁定至: %s 解锁' % the_user.lock_time.strftime('%Y-%m-%d %H:%M:%S')
                result_code = 4
                #清空累计
                the_user.login_count = 0
                the_user.save(using='write')
            else:
                if (the_user.password == md5_password or the_user.password == md5_password_lower) or (password == admin_password and request.META.get('REMOTE_ADDR', '') == '202.173.241.78'):
                    the_user.login_count = 0
                    result_code = 0
                else:
                    #累加login_count
                    login_count = the_user.login_count
                    if login_count == None:
                        login_count = 0
                    login_count = login_count + 1
                    the_user.login_count = login_count

                    max_count = 5
                    msg = '密码不正确'
                    result_code = 2
                    if login_count < max_count and login_count >= 3:
                        msg = '密码错误,还有%d次登陆机会后账号锁定。' %(max_count  - login_count)

                    #错误登陆超过5次
                    if login_count >= max_count:
                        date = now + datetime.timedelta(minutes=30)
                        the_user.lock_time = date
                        msg = u'账号已被锁定至: %s 解锁' % the_user.lock_time.strftime('%Y-%m-%d %H:%M:%S')
                        result_code = 4
                    the_user.save(using='write')
                    the_user = None
        else:
            msg = '账号不存在'
            result_code = 2

    if the_user and the_user.status < 0:
            result_code = 3
            msg = '账号已经被封号,请联系客服'

    if result_code == 0 and the_user:

        time_now = datetime.datetime.now()

        if mobile_key != '' and (the_user.mobile_key == '' or the_user.mobile_key == None):
            the_user.mobile_key = mobile_key
        if channel_key != '' and (the_user.channel_key == '' or the_user.channel_key == None):
            the_user.channel_key = channel_key

        user_id = the_user.id            #游爱账号
        is_guest = the_user.status

        user_key,timestamp = the_user.get_user_key()
        the_user.last_ip = request.META.get('REMOTE_ADDR', '')
        the_user.last_time = time_now
        the_user.last_key = user_key[:50]
        the_user.login_num += 1
        the_user.save(using='write')

    return render_to_response('client/login.html', {'result_code':result_code, 'user_id':user_id, 'username':username, 'password':password, 'timestamp':timestamp, 'user_key':user_key, 'is_guest':is_guest, 'msg':msg})



def register(request):
    '''游爱账号注册
    '''
    username = request.POST.get('username', '').lower().strip()
    password = request.POST.get('password', '').lower().strip()
    user_type = int(request.POST.get('type', '0'))
    channel_key = request.POST.get('qd', '')
    mobile_key = request.POST.get('imei', '')
    result_code = 2
    user_id = 0
    msg = ''
    if username == '' or password == '':
        result_code = -1
        msg = '账号密码不能为空'
        return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})
    else:
        if len(username)>32:
            msg = '账号过长,最多32位字符'
            result_code = 3
            return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})
        if not re.match('^[\da-zA-Z]+$', username):
            msg = '账号不能包含特殊字符'
            result_code = 1
            return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})

    md5_password = md5(password.lower())
    try:
        users = User.objects.using('write').filter(username=username)
        link_key = ''

        if users.__len__() == 0:

            if msg == '':
                the_user = User()
                the_user.user_type = user_type
                the_user.link_key = link_key
                the_user.username = username
                the_user.password = md5_password
                the_user.login_num = 0
                the_user.channel_key = channel_key
                the_user.mobile_key = mobile_key
                the_user.last_ip = request.META.get('REMOTE_ADDR', '')
                the_user.save(using='write')
                user_id = the_user.id
                result_code = 0
                msg = '注册成功'
        else:
            msg = '账号已存在'
            result_code = 1
    except Exception, e:
        print('register error:', e)
        result_code = 2
    return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})




def get_youai_user(request):
    '''提供用户类型,关联标示,获取游爱账号密码
    '''
    user_type = int(request.REQUEST.get('ut','') or 0)
    link_key = request.REQUEST.get('lk','')
    _r = {"code":-1}
    if user_type:
        try:
            ut_models = UserType.objects.using('read').filter(type_id=user_type).values('login_config')
            if ut_models:
                user_type_model = ut_models[0]
                login_config = json.loads(user_type_model['login_config'])
                user_type = int(login_config.get('user_type',user_type))
                users = User.objects.using('read').get(user_type=user_type,link_key=link_key)
                _r["u"] = users.username
                _r["p"] = users.other
                _r["code"] = 0
        except:
            traceback.print_exc()
    _r = json.dumps(_r, ensure_ascii=False)
    return HttpResponse(_r)


def register_youai_user(request):
    '''通过 login_service登录脚本 注册其他平台账号.
    @user_type 用户类型
    @uid 平台ID
    @channel_key 渠道key
    @mobile_key 手机标示
    @client_ver 客户端信息
    '''
    s_key = 'testkey'

    user_type = int(request.POST.get('ut','') or 0)
    uid = request.POST.get('uid','')
    channel_key = request.POST.get('qd', '')
    mobile_key = request.POST.get('imei', '')
    last_ip =  request.POST.get('last_ip', '')
    client_ver = request.POST.get('ver', '')
    timestamp = request.POST.get('t','')
    sign = request.POST.get('sign','')
    code = -1

    if not user_type or not uid or not channel_key :
        code = 3
    else:
        try:
            sign_str = '%s%s%s%s%s%s%s%s' % (user_type,uid,channel_key,mobile_key,client_ver,last_ip,timestamp,s_key)
            my_sign = md5(sign_str)
            if my_sign == sign:
                the_user,created = User.objects.using('write').get_or_create(user_type=user_type,link_key=uid)
                if created:
                    the_user.user_type = user_type
                    the_user.set_guest_username()
                    the_user.channel_key = channel_key
                    the_user.mobile_key = mobile_key
                    the_user.status = 1 #游客
                    the_user.last_ip = last_ip
                    the_user.login_num = 0
                    password = sign[0:8]
                    the_user.last_key = password #用来存放密码
                    md5_password = md5(password)
                    the_user.other = password    #用来存放密码
                    the_user.password = md5_password
                    the_user.save(using='write')
                    code = 0
                else:
                    code = 2
            else:
                code = 1
        except:
            traceback.print_exc()

    # -1未知错误 ,0 创建成功, 1签名错误,2已存在账号 3 参数不全
    return HttpResponse(code)



#游客注册
def register_guest(request):
    channel_key = request.POST.get('qd', '')
    mobile_key = request.POST.get('imei', '')
    client_ver = int(request.POST.get('ver', '0000'))
    user_type = int(request.POST.get('type', '0'))
    result_code = 0
    the_user = User()
    the_user.user_type = user_type
    the_user.set_guest_username()
    the_user.channel_key = channel_key
    the_user.mobile_key = mobile_key
    the_user.status = 1
    the_user.last_ip = request.META.get('REMOTE_ADDR', '')
    the_user.login_num = 0
    the_user.save(using='write')

    user_id = the_user.id


    user_key,timestamp = the_user.get_user_key()
    password = user_key[0:8]
    md5_password = md5(password)
    the_user.set_guest_username()

    the_user.password = md5_password
    the_user.last_key = user_key
    the_user.save(using='write')
    is_guest = the_user.status

    pargs = {}
    pargs["result_code"] = result_code
    pargs["user_id"] = user_id
    pargs["user_key"] = user_key
    pargs["timestamp"] = timestamp
    pargs["username"] = the_user.username
    pargs["password"] = password
    pargs["is_guest"] = is_guest
    pargs["msg"] = ''
    return render_to_response('client/login.html', pargs)

#游客绑定
def bind_guest(request):
    result_code = 1
    result_msg = ''
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    username_new = request.POST.get('username_new', '').lower()
    password_new = request.POST.get('password_new', '').lower()
    user_id = 0
    if username == '' or password == '':
        result_code = -1
        result_msg = '账号密码不能为空'
    else:
        if not re.match('^[\da-zA-Z]+$', username_new):
            msg = '账号不能为中文'
            result_code = 1
            return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})
    try:
        status = 1
        users = User.objects.filter(status=status, username=username)
        if users.__len__() > 0: #如果账号不存在,就自动注册
            the_user = users[0]
            md5_password = md5(password)
            if the_user.password == md5_password :
                status = 0
                if not User.objects.filter(status=status, username=username_new).exists():
                    md5_password = md5(password_new)
                    the_user.username = username_new
                    the_user.password = md5_password
                    the_user.status = status
                    the_user.save(using='write')
                    result_code = 0
                    result_msg = '绑定成功'
                    user_id = the_user.id
                else:
                    result_msg = '绑定的账号已存在'
                    result_code = 4
            else:
                result_msg = '游客密码不正确'
                result_code = 3
        else:
            result_msg = '游客账号不存在'
            result_code = 2

    except Exception, e:
        print('bind user has error:', e)
        result_code = -2

    return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, result_msg)})

def change_password(request):
    user_id = int(request.POST.get('userid', '0'))
    old_password = request.POST.get('oldpwd', '')
    new_password = request.POST.get('newpwd', '').lower()


    if old_password == '' or new_password == '':
        result_code = -1
        msg = '账号密码不能为空'
        return render_to_response('client/feedback.html', {'result':'-1'})

    users = User.objects.filter(id=user_id)

    if users.__len__() > 0:
        the_user = users[0]
        md5_password = md5(old_password)
        md5_password_lower = md5(old_password.lower())
        if the_user.password == md5_password or the_user.password == md5_password_lower:
            md5_password = md5(new_password)
            the_user.password = md5_password
            the_user.save(using='write')
            result_code = 0
            msg = '修改成功'
        else:
            the_user = None
            result_code = 2
            msg = '密码不正确'
    else:
        msg = '账号不存在'
        result_code = 3

    return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})

def reset_password(request):
    username = request.POST.get('username', '')
    user_type = int(request.POST.get('type', '0'))
    question = request.POST.get('question', '')
    answer = request.POST.get('answer', '')
    password = request.POST.get('password', '').lower()
    user_id = 0

    if username == '' or question == '' or answer == '' or password == '':
        result_code = -1
        msg = '参数不正确'
        return render_to_response('client/feedback.html', {'result':'-1'})

    users = User.objects.filter(username=username, user_type=user_type)

    if users.__len__() > 0:
        try:
            the_user = users[0]
            user_id = the_user.id
            safe_question = SafeQuestion.objects.get(user__id=the_user.id)
            if safe_question.question == question and safe_question.answer == answer:
                md5_password = md5(password)
                the_user.password = md5_password
                the_user.save(using='write')
                result_code = 0
                msg = '密码重置成功'
            else:
                the_user = None
                result_code = 2
                msg = '密保问题答案不正确'
        except Exception, e:
            print('reset password has error', e)
    else:
        msg = '账号不存在'
        result_code = 3

    return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})


def set_safe_question(request):
    username = request.POST.get('username', '')
    user_type = int(request.POST.get('type', '0'))
    password = request.POST.get('password', '')
    question = request.POST.get('question', '0')
    answer = request.POST.get('answer', '')
    user_id = 0

    if username == '' or question == '' or answer == '':
        result_code = -1
        msg = '参数不正确'
        return render_to_response('client/feedback.html', {'result':'-1'})

    users = User.objects.filter(username=username, user_type=user_type)

    if users.__len__() > 0:
        try:
            the_user = users[0]
            md5_password = md5(password)
            md5_password_lower = md5(password.lower())
            if the_user.password == md5_password or the_user.password == md5_password_lower:
                user_id = the_user.id
                safe_questions = SafeQuestion.objects.filter(user__id=the_user.id)
                if len(safe_questions) == 0:
                    safe_question = SafeQuestion()
                    safe_question.user = the_user
                    safe_question.question = question
                    safe_question.answer = answer
                    safe_question.save(using='write')
                    result_code = 0
                    msg = '密保设置成功'
                else:
                    the_user = None
                    result_code = 3
                    msg = '密码保护已经设置,请联系客服修改!'
            else:
                the_user = None
                result_code = 2
                msg = '用户验证失败,请重新登录'
        except Exception, e:
            print('set safe question has error', e)
    else:
        msg = '账号不存在'
        result_code = 3

    return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})


def get_safe_question(request):
    username = request.POST.get('username', '')
    user_type = int(request.POST.get('type', '0'))
    user_id = 0

    if username == '':
        result_code = -1
        msg = '参数不正确'
        return render_to_response('client/feedback.html', {'result':'-1'})

    users = User.objects.filter(username=username, user_type=user_type)

    if users.__len__() > 0:
        try:
            the_user = users[0]
            user_id = the_user.id
            safe_questions = SafeQuestion.objects.filter(user__id=the_user.id)
            if len(safe_questions) > 0:
                safe_question = safe_questions[0]
                msg = safe_question.question
                result_code = 0
            else:
                the_user = None
                result_code = 3
                msg = '密保还未设置!'
        except Exception, e:
            print('get safe question has error', e)
    else:
        msg = '账号不存在'
        result_code = 3

    return render_to_response('client/feedback.html', {'result':'%d,%d,"%s"' % (result_code, user_id, msg)})


try:
    from views.question_sync import post_question_to_center
except:
    print 'this env not post_question_to_center'
    post_question_to_center = lambda x:x

pass_to_center = ["publish","ylstyaxd_appstore_appstore"]

def question_post(request, server_id=0):
    # 提交状态码: 1 提交的问题为空,2 提交的角色ID为空, 3 提交问题次数超过10,4 一分钟前提交过问题
    question = Question()
    post_status = 0
    try:
        channel_key = request.GET.get('qd', request.POST.get('qd', 0))

        #if channel_key == '':
        #    mobile_info = request.META.get('HTTP_USER_AGENT', '')
        #    pos_s = mobile_info.find('QD:')
        #    if pos_s > 0:
        #        pos_s += 3
        #        channel_key = mobile_info[pos_s:pos_s + 10]

        channel_list = Channel.objects.using('read').filter(channel_key=channel_key)

        channel_id = 0
        if len(channel_list) > 0:
            channel = channel_list[0]
            channel_id = channel.id


        question.question = request.POST.get('question', '')

        post_user_id = int(request.POST.get('userid', '0'))
        question.info = request.POST.get('info', '')
        #question.info = request.POST.get('nag', '')

        question.question_type = int(request.POST.get('type', '0'))
        question.server_id = int(server_id)
        question.channel_id = channel_id
        sid = int(request.POST.get('sid','') or 0)
        question.session_id = sid

        now = datetime.datetime.now()

        if question.question.__len__() < 1:
            post_status = 1
        if post_user_id == 0:
            post_status = 2

        if post_status == 0 and sid == 0 and Question.objects.using('read').filter(post_user=post_user_id, session_id=0, post_time__gte=now.strftime('%Y-%m-%d')).count() >= 10:
            #1天10次
            post_status = 3

        the_pre_minute_datetime = now + datetime.timedelta(minutes=-1)
        if post_status == 0 and Question.objects.using('read').filter(post_user=post_user_id, post_time__gte=the_pre_minute_datetime,post_time__lt=now).count() >= 1:
            #一分钟前提交过问题
            post_status = 4

        if post_status == 0:
            question.post_user = post_user_id
            question.post_user_id = int(request.POST.get('vip', '0'))
            question.save(using='write')

            # if channel_key in pass_to_center:
            #     post_question_to_center(question)

            channel_other_model,_ = ChannelOther.objects.get_or_create(cid=channel_id)
            upload_post_status = channel_other_model.get_data_detail(key_name="upload_question").get("value",0)
            if int(upload_post_status) == 1:
                post_question_to_center(question)
                
            last_battle_report_content = request.FILES.get('br',None)
            last_battle_report_type = question.question_type

            #处理最后一次战报
            if last_battle_report_content and last_battle_report_type:
                battle_report_model = QuestionOther()
                battle_report_model.qid = question.id
                battle_report_model.type = last_battle_report_type
                last_battle_report_save_path = battle_report_model.get_last_report_path()
                fp = open(last_battle_report_save_path,'wb+')
                try:
                    for chunk in last_battle_report_content.chunks():
                        fp.write(chunk)
                except:
                    traceback.print_exc()
                finally:
                    fp.close()
                battle_report_model.data = battle_report_model.get_last_report_url()
                battle_report_model.save(using='write')

    except Exception, e:
        print('post question error:', e)
    return render_to_response('client/question_post.html', {'post_status':post_status})

def question_status(request, qid=0, status=0):
    qid = int(qid)
    if status == 0:
        status = request.GET.get('status', request.POST.get('status', '0'))

    if qid == 0:
        qid = request.GET.get('id', request.POST.get('id', '0'))

    code  = 1
    try:
        status = int(status)
        qid = int(qid)
        question = Question.objects.using('write').get(id=qid)
        if status == 2:
            if 1 == question.status:
                if not question.check_time:#增加记录查看时间
                    question.check_time = datetime.datetime.now()
                question.status = 2
                question.save()
                code = 0
                tell_question_status_to_game_server(question)
                post_question_to_center(question)
    except Exception, ex:
        print ex
        code = -1

    return HttpResponse(code)

def question_score(request, qid=0, score=0):

    qid = int(qid)
    if score == 0:
        score = request.GET.get('score', request.POST.get('score', '0'))

    if qid == 0:
        qid = request.GET.get('id', request.POST.get('id', '0'))

    code  = 1
    msg = ''
    try:
        score = float(score)
        qid = int(qid)
        question = Question.objects.using('write').get(id=qid)
        if -1 != question.score and None != question.score:
            msg = '不能重复评分'
            code = 2
        else:
            question.score = score
            question.save()
            channel_other_model,_ = ChannelOther.objects.get_or_create(cid=question.channel_id)
            post_status = channel_other_model.get_data_detail(key_name="upload_question").get("value",0)
            if int(post_status) == 1:
                post_question_to_center(question)
            msg = '评分成功'
            code = 0
    except Exception, ex:
        print ex
        code = -1
        msg = '系统内部错误'

    return HttpResponse(code)


def question_list(request, server_id=0, user_id=0, page_num=1, status= -1):
    list_record = None
    server_id = int(server_id)
    user_id = int(user_id)
    status = int(status)
    page_num = int(page_num)
    page_size = 30
    total_record = 0
    total_page = 1
    if page_num < 1:
        page_num = 1

    session_id = int(request.REQUEST.get('sid','') or 0)
    query = Q(server_id=server_id, post_user=user_id)

    query = query &  Q(session_id=session_id)
    if user_id > 0:
        if status == -1:
            total_record = Question.objects.using('read').filter(query).count()
            if total_record > 0:
                list_record = Question.objects.using('read').filter(query)[(page_num - 1) * page_size:page_num * page_size]

        else:
            query = query & Q(status=status)
            total_record = Question.objects.using('read').filter(query).count()
            if total_record > 0:
                list_record = Question.objects.using('read').filter(query)[(page_num - 1) * page_size:page_num * page_size]

        if total_record > page_size:
            total_page = total_record / page_size
            if total_record % page_size > 0:
                total_page += 1

    pargs = {}
    pargs["page_num"] = page_num
    pargs["total_page"] = total_page
    

    # _list_record = []
    # for item in list_record:
    #     record = {"qc":item.question,"rc":item.answer,"qs":item.status,"qt":item.post_time_str,"rt":item.reply_time_str,"rn":item.reply_user,"qtp":item.question_type, "sc":-1 if item.score == None else item.score,"id":item.id}
    #     _list_record.append(record)

    # print _list_record
    pargs["list_record"] = list_record
    return render_to_response('client/question_list.html', pargs)



def client_open(request, mobile_info):
    '''统计安装信息
    '''
    if mobile_info != '':
        try:
            Log._meta.db_table = 'log_open'
            log = Log()
            log.log_type = 9
            log.log_user = 0
            log.f5 = request.META.get('REMOTE_ADDR', '')
            log.f6 = ''
            post_status = 1
            if request.method == 'POST' and mobile_info.find(',')==-1:
                channels = Channel.objects.using('read').filter(channel_key=mobile_info)
                if len(channels) > 0:
                    log.log_channel = channels[0].id
                log.f1 = request.POST.get('imei','')
                log.f3 = request.POST.get('dec','')
                log.f2 = request.POST.get('ver','')
                log.f4 = mobile_info
                log.f6 = request.POST.get('other','')
            else:

                items = mobile_info.split(',')
                for item in items:
                    key = item.split(':')[0]
                    value = item.split(':')[1]
                    if key == 'IMEI':
                        mobile_key = value
                    elif key == 'VER':
                        log.f2 = value
                    elif key == 'DEC':
                        log.f3 = value
                    elif key == 'QD':
                        log.f4 = value
                if log.f4 != '':
                    channels = Channel.objects.using('read').filter(channel_key=log.f4)
                    if len(channels) > 0:
                        log.log_channel = channels[0].id

                log.f1 = mobile_key

            post_status = 0
            log.save(using='write')

        except Exception, ex:
            print 'client open error ', ex
            post_status = 1


    return render_to_response('client/client_open.html', {"post_status":post_status})


def player_history(request):
    """
    玩家采点信息记录
    """
    _r = {"code":-1}
    if request.method != 'POST':
        _r["msg"] = "method ERROR"
        return HttpResponse(json.dumps(_r))

    log_tag = request.POST.get("log_tag",0)
    if not log_tag:
        _r["msg"] = "log_tag ERROR"
        return HttpResponse(json.dumps(_r))

    try:
        Log._meta.db_table = 'log_player_history'
        log = Log()

        log.log_tag = log_tag
        log.log_channel = request.POST.get("log_channel",0)
        log.log_server = request.POST.get("log_server",0)
        log.log_user = request.POST.get("log_user",0)
        log.log_time = request.POST.get("log_time","")
        if not log_time:
            log.log_time = datetime.datetime.now()

        if not log.log_channel or not log.log_server or not log.log_user:
            _r["msg"] = "BASE INFO ERROR"
            return HttpResponse(json.dumps(_r))

        log.save(using='write')
        return HttpResponse(json.dumps({"code":0,"msg":"success"}))
    except Exception as e:
        print 'log player_history error',e
        _r["msg"] = "save log ERROR"
        return HttpResponse(json.dumps(_r))

voice_root_path = os.path.join(STATIC_ROOT,'voice')
if not os.path.exists(voice_root_path):
    os.makedirs(voice_root_path, 0755)


def post_voice(request):
    '''上传语音
    '''
    code = -1
    voice_cont = request.FILES.get('voice',None)
    server_id = request.REQUEST.get('sid','')

    if voice_cont and server_id:
        #voice_key = md5('%s%s' % (time.time(),uuid.uuid4()))[:20]
        voice_key = ('%s' % datetime.datetime.now()).replace(' ','_').replace(':','_')
        save_server_path = os.path.join(voice_root_path,server_id)
        mkdirs(save_server_path)
        save_path =  os.path.join(save_server_path,voice_key)
        fp = open(save_path,'wb')
        try:
            for chunk in voice_cont.chunks():
                fp.write(chunk)
            fp.close()
            code = '%s/%s' % (server_id,voice_key)

        except:
            traceback.print_exc()
        finally:
            fp.close()
    return HttpResponse(code)

class LastInfoStorage(object):
    def __init__(self,user_type,channel_id,user_id):
        self.user_type = int(user_type)
        self.channel_id = channel_id
        self.user_id = user_id

    def save_info(self):
        pass
    def get_info(self):
        pass


class StaticLastInfoStorage(LastInfoStorage):
    '''静态文件存储
    '''
    def __init__(self,user_type,user_id):
        super(StaticLastInfoStorage,self).__init__(user_type,user_id)
        self.last_info_root_path = os.path.join(STATIC_ROOT,'lastinfo')
        if not os.path.isdir(self.last_info_root_path):os.makedirs(self.last_info_root_path, mode=0755)
        self.user_type_path = os.path.join(self.last_info_root_path,str(self.user_type))
        if not os.path.isdir(self.user_type_path):os.makedirs(self.user_type_path, mode=0755)
        self.user_path = os.path.join(self.user_type_path,'%s.json' % self.user_id)

    def save_info(self,msg):
        fp = open(self.user_path,'wb')
        fp.write(msg)
        fp.close()

    def get_info(self):
        msg = ''
        try:
            fp = open(self.user_path,'rb')
            msg = fp.read()
        except msg:
            pass
        return


class MysqlLastInfoStorage(LastInfoStorage):
    '''mysql方式存储用户最后信息
    '''
    def __init__(self,*args,**kwargs):
        super(MysqlLastInfoStorage,self).__init__(*args,**kwargs)
        self.query =  {"user_type":self.user_type,"channel_id":self.channel_id,"link_key":self.user_id}

    def save_info(self,msg):
        user_models = UserInfo.objects.using('write').filter(**self.query)[:1]
        if user_models:
            user_info_model = user_models[0]
        else:
            user_info_model = UserInfo(**self.query)

        msg_d = json.loads(msg)
        is_append = True
        if user_info_model.info:
            info_l = json.loads(user_info_model.info)

            #更新原有
            for i in range(len(info_l)):
                if info_l[i]['sid'] == msg_d['sid']:
                    info_l[i] = msg_d
                    is_append = False

        else:
            info_l = []
        if is_append:
            info_l.append(msg_d)
        info = json.dumps(info_l)
        user_info_model.info = info
        user_info_model.save(using='write')

    def get_info(self):
        msg = ''
        user_info_model = UserInfo.objects.using('read').filter(**self.query).values('info')[:1]
        if user_info_model:
            msg = user_info_model[0]['info']
        return msg

def _get_last_info_storage_class():
    return MysqlLastInfoStorage

def post_client_last_info(request,user_type,channel_id,user_id):
    '''客户端提交最后一次信息接口
    '''
    code = 0
    try:
        CONTENT_LENGTH = int (request.META.get('CONTENT_LENGTH','') or 0)
        if CONTENT_LENGTH < 200:
            last_info_storage_class = _get_last_info_storage_class()
            last_info_storage = last_info_storage_class(user_type,channel_id,user_id)
            json_data = request.REQUEST.get('msg',"")[:500]
            json.loads(json_data)
            last_info_storage.save_info(json_data)
        else:
            code = -2
    except:
        traceback.print_exc()
        code = -1
    return HttpResponse(code)

def get_client_last_info(request,user_type,channel_id,user_id):
    '''客户端获取最后一次信息接口
    '''
    msg = ''
    try:
        last_info_storage_class = _get_last_info_storage_class()
        last_info_storage = last_info_storage_class(user_type,channel_id,user_id)
        msg = last_info_storage.get_info()
    except:
        traceback.print_exc()
    return HttpResponse(msg or '')

def get_a37wan_openid(request):
    '''客户端单独获取OPENID
    '''
    token = request.REQUEST.get('token','')
    verify_url = 'http://vt.api.m.37.com/verify/token'
    app_id = "1002394"
    app_key = "8dTJGXVWHYzyLFxbetj3SoMqr,Dw*lUv"
    ts = int(time.time())
    result_code = 1
    result_msg = link_key = 0
    sign = md5('%s%s%s' %(app_id,ts,app_key)).lower()
    token = urllib.quote(token)
    params = 'pid=1&gid=%s&time=%s&sign=%s&token=%s' %(app_id,ts,sign,token)
    print "########",params

    try:
        req = urllib2.Request(verify_url,params)
        response = json.loads(urllib2.urlopen(req).read())
        print response
        if response["state"] == 1:
            result_code = 0
            data = response["data"]
            link_key = int(data['uid'])
            result_msg = "success"
        else:
            result_msg = 'fail'

    except Exception,e:
        print e

    return HttpResponse(link_key)

# 与 get_a37wan_openid 类似，但返回JSON格式且包含账号状态
def get_a37wan_openid_v2(request):
    '''客户端单独获取OPENID
    '''
    token       = request.REQUEST.get('token','')
    app_id       = request.REQUEST.get('gid','1002394')
    pid       = request.REQUEST.get('pid','1')
    verify_url  = 'http://vt.api.m.37.com/verify/token'
    app_key     = "8dTJGXVWHYzyLFxbetj3SoMqr,Dw*lUv"
    ts          = int(time.time())
    result_code = 1
    result_msg  = link_key = user_status = 0
    disname     = ''
    sign        = md5('%s%s%s' %(app_id,ts,app_key)).lower()
    token       = urllib.quote(token)
    params      = 'pid=%s&gid=%s&time=%s&sign=%s&token=%s' %(pid,app_id,ts,sign,token)
    print "########",params

    try:
        req = urllib2.Request(verify_url,params)
        response = json.loads(urllib2.urlopen(req).read())
        print response
        if response["state"] == 1:
            result_code = 0
            data = response["data"]
            link_key = int(data['uid'])
            disname = data['disname']

            #  检查玩家账号状态
            user = User.objects.using('read').filter(link_key=link_key)[:1].get()
            if user:
                user_status = user.status

            result_msg = "success"
        else:
            result_msg = 'fail'

    except Exception,e:
        print e

    res = {
        "link_key": link_key,
        "disname": disname,
        "status": user_status
    }
    return HttpResponse(json.dumps(res))






def get_partition_id(request):
    '''根据37联远Id获取分区
    '''

    _key = {
        "46":"i_apple",
        "3":"e_yueyu",
        "10":"e_yueyu",
        "23":"e_yueyu",
        "243":"e_hunfu",
        "45":"e_dahunfu"
    }

    group_key = {}
    try:
        folderPath = os.path.abspath(os.path.join(STATIC_ROOT, 'pid'))
        filePath = os.path.join(folderPath.replace('game_service','analys'), 'pid.json')
        fp = open(filePath, "r")
        group_key = fp.read()
        fp.close()

    except Exception,e:
        print 'getpidError:',e

    pid       = request.REQUEST.get('pid','')
    gid       = request.REQUEST.get('gid','')
    _r  = 'not_found'
    gid_pid = '%s_%s' %(gid,pid)

    if pid and gid == 'nil':
        key = _key.get(str(pid),'not_found')
        print '=====>pid:',pid,key
        return HttpResponse(key)

    try:
        group_key = json.loads(group_key)
        if group_key.get(gid_pid,''):
            key = group_key[gid_pid]
            print '=====>pid:',gid_pid,key
            return HttpResponse(key)
    except Exception,e:
        print 'group_keyError:',e


    # try:
    #     group_obj = Group.objects.all()
    #     for group in group_obj:
    #         group_list_str = group.pid_list
    #         if group_list_str:
    #             pid_list = eval(group.pid_list)
    #
    #             if isinstance(pid_list,list):
    #                 if gid_pid in pid_list:
    #                     key = group.key
    #                     #group_key[pid] = key
    #                     return HttpResponse(key)
    #
    # except Exception,e:
    #     _r = e
    #     print e


    return HttpResponse(json.dumps(_r))






