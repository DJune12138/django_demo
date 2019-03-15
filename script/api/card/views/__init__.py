# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import datetime
import re
import traceback

import MySQLdb

from django.shortcuts import render_to_response
from django.http import HttpResponse
from settings import DATABASES

from models.card import Card, CardBatch, CardLog
from models.server import Group, Server
from models.channel import Channel
from views.game.base import GMProtocol


def index(request, group_key=0, key=''):
    '''领取主页
    '''
    user_agent = request.META['HTTP_USER_AGENT'].lower()
    is_mobile = 0
    if user_agent.find('mobile') != -1 or user_agent.find('wap') != -1:
        is_mobile = 1
    the_card_batch = []
    server_ids = request.session.get('server_ids', [])

    list_server = []
    print key
    if key and group_key != 0:  # in group_key_map.keys():
        try:
            the_card_batch = CardBatch.objects.using('card').filter(key=key)[0]
            if the_card_batch.status > 0:
                current_unixtime = int(time.time())
                start_time = int(time.mktime(the_card_batch.start_time.timetuple()))
                end_time = int(time.mktime(the_card_batch.end_time.timetuple()))

                if current_unixtime < start_time or current_unixtime > end_time:
                    list_server = []
                else:
                    list_server = the_card_batch.server
                    if group_key == 'a':
                        list_server = [int(i) for i in list_server.split(',') if i]
                        list_server = Server.objects.using('read').filter(id__in=list_server)
                    else:
                        group_server = Group.objects.using('read').filter(key=group_key)[0].server.exclude(
                            status__in=[-1, 0, 1])
                        if list_server != '' and list_server != 'None' and list_server != None:
                            list_server = [int(i) for i in list_server.split(',')]
                            list_server = group_server.filter(id__in=list_server)
                        else:
                            list_server = group_server
            else:
                the_card_batch = []
        except Exception, e:
            traceback.print_exc()
            print 'get card batch error', e
            list_server = []
    else:
        list_server = []
    if len(list_server) == 0:
        the_card_batch = []
    if len(server_ids) == 0:
        server_ids = request.COOKIES.get('server_ids', [])

    if type(server_ids) == str:
        server_ids.replace('[', '')
        server_ids.replace(']', '')
        server_ids = server_ids.split(',')

    show_num = 0
    for item in list_server:
        try:
            if False:  # server_ids.__contains__(item.id):
                item.is_show = False
            else:
                item.is_show = True
                show_num += 1
        except Exception, ex:
            print 'server_ids.__contains___ error:', ex
            item.is_show = False

    pargs = {}
    pargs["list_server"] = list_server
    pargs["show_num"] = show_num
    pargs["key"] = key
    pargs["the_card_batch"] = the_card_batch
    pargs["is_mobile"] = is_mobile
    return render_to_response('index.html', pargs)


class CardShowError(Exception): pass


def show(request, batch_name=''):
    '''礼包卡号显示
    '''
    batch_name = batch_name.strip()
    card_result = ''
    server_id = int(request.REQUEST.get('server_id', '') or 0)
    is_ajax = request.REQUEST.get('is_ajax', False)
    key_name = request.REQUEST.get('key_name', '')
    password_key = request.REQUEST.get(key_name, '')
    cb = request.REQUEST.get('cb', '') or request.REQUEST.get('callback', '') or request.REQUEST.get('jsonpcallback',
                                                                                                     '')
    server_ids = []
    is_error = True

    _r = {"code": -1, "msg": ""}

    try:

        if not batch_name:
            raise CardShowError('礼包名名为空!')

        the_card_batch = CardBatch.objects.using('card').filter(name=batch_name)[:1]

        if len(the_card_batch) == 0:
            raise CardShowError('没有 %s 礼包!' % batch_name)

        import pdb;
        pdb.set_trace()
        the_card_batch = the_card_batch[0]
        if the_card_batch.show == 0:
            raise CardShowError('%s 礼包被禁用 !' % batch_name)

        if int(time.time()) - request.session.get('card_time', 0) > 1800:
            request.session['card_code'] = 0

        card_code = request.session.get('card_code', 0)
        if card_code:
            _r['code'] = 0
            raise CardShowError(card_code)

        card_limit_count = the_card_batch.card_limit_count
        current_unixtime = int(time.time())
        start_time = int(time.mktime(the_card_batch.start_time.timetuple()))
        end_time = int(time.mktime(the_card_batch.end_time.timetuple()))

        if not (current_unixtime > start_time and current_unixtime < end_time):
            raise CardShowError('%s 礼包不在可用时间内 !' % batch_name)

        list_server = the_card_batch.server
        if list_server:
            list_server = [int(i) for i in list_server.split(',')]
            if server_id not in list_server:
                raise CardShowError('%s 礼包不在可用服务器内!' % batch_name)
        try:
            key = the_card_batch.key
            the_conn_str = DATABASES['card']
            the_conn = MySQLdb.connect(host=the_conn_str['HOST'], user=the_conn_str['USER'],
                                       passwd=the_conn_str['PASSWORD'], port=int(the_conn_str['PORT']),
                                       db=the_conn_str['NAME'], charset='utf8')
            the_conn.autocommit(1)
            cursor = None
            card_table_name = Card.get_card_table_name(key)
            cursor = the_conn.cursor()
            sql = "LOCK TABLE %s WRITE" % card_table_name
            cursor.execute(sql)
            sql = "SELECT `number`,`id` FROM %s WHERE  `status`=0  AND `batch_id` = %d LIMIT 1" % (
                card_table_name, the_card_batch.id)
            cursor.execute(sql)
            print sql
            data = cursor.fetchone()

            if not data:
                raise CardShowError('卡号已经全部领取完毕')
            card_code = data[0]
            sql = "UPDATE %s SET  `status`=1 WHERE `id` = %d " % (card_table_name, int(data[1]))
            cursor.execute(sql)
            request.session['card_code'] = card_code
            request.session['card_time'] = int(time.time())
            _r['msg'] = data[0]
            _r['code'] = 0
        except CardShowError, e:
            raise CardShowError(str(e))
        except Exception, e:
            traceback.print_exc()
            raise CardShowError(str(e))
        finally:
            if None != cursor:
                try:
                    cursor.execute('UNLOCK TABLES')
                except Exception, e:
                    traceback.print_exc()
                    raise CardShowError('卡号已经全部领取完毕')

    except CardShowError, err_info:
        _r['msg'] = err_info[0]
    except Exception, e:
        traceback.print_exc()
        _r['msg'] = '未知错误!'

    json_rsp = json.dumps(_r, ensure_ascii=False)
    if cb == 'json':  # 返回json
        response = json_rsp
    elif cb:  # jsonp函数
        response = '%s(%s)' % (cb, json_rsp)
    else:  # 什么都不是 返回text
        response = _r['msg']
    return HttpResponse(response)


def getConn(server_id=0):
    the_conn = None
    try:
        if server_id != 0:
            the_server = Server.objects.using('read').get(id=server_id)
            the_conn_str = json.loads(the_server.log_db_config)
            the_conn = MySQLdb.connect(host=the_conn_str['host'], user=the_conn_str['user'],
                                       passwd=the_conn_str['password'], port=the_conn_str.get('port', 3306),
                                       db=the_conn_str['db'], charset='utf8')
        the_conn.autocommit(1)
    except Exception, e:
        traceback.print_exc()
        print('mysql has error0:%d,%s' % (server_id, e))
        raise Exception, e

    return the_conn


class GamePlayerInfo(object):
    '''游戏角色信息
    '''

    def __init__(self, player_id):
        self.player_id = int(player_id)

        self.server_id = self.player_id >> 20

    def get_level(self):
        conn = getConn(self.server_id)
        cursor = conn.cursor()
        query_sql = 'SELECT MAX(`log_level`) FROM `log_player_level` WHERE `log_server` = %s AND `log_user` = %s ' % (
            self.server_id, self.player_id)
        print 'query_sql', query_sql
        cursor.execute(query_sql)
        player_level = cursor.fetchone()[0]
        if str(player_level).isdigit():
            return int(player_level)
        conn.close()


'''
0    卡号验证成功
-2    卡号不存在
-1    未知错误
1    卡号验证失败
2    卡已超过使用次数
3    卡已超过有效期
4    该卡不能在此运营商使用
5    该卡不能在这个服务器使用
6    该类卡你已经不能再用 禁用
7    该类卡你已经不能再用 次数
8    该礼品卡需要主城等级不够
new:
0   奖励已到背包，请注意查收
-2  该礼包码不存在
-1  未知错误，请联系客服
1   未知错误，请联系客服
2   该礼包码已被领取
3   该礼包码已失效
4   无法领取该礼包码
5   无法领取该礼包码
6   该礼包码已失效
7   已领取过该礼包

'''


# class CardReCode:

#     unknow_err = -1       #未知错误
#     not_exist =  -2       #该类礼品卡不存在此卡号
#     success = 0           #卡号验证成功
#     validation_fails = 1  #卡号验证失败
#     over_card_limit = 2   #超过卡每张卡的限制次数 ,已被使用过
#     expired = 3           #卡已超过有效期
#     channel_err = 4       #该卡不能在此运营商使用
#     server_err = 5        #该卡不能在这个服务器使用
#     illegal = 6           #该类卡你已经不能再用 禁用
#     over_role_limit = 7   #卡已超过角色限制次数
#     level_not_enough = 8  #该礼品卡需要主城等级不够

class CardReCode:
    unknow_err = -1  # 未知错误
    not_exist = -2  # 该礼包码不存在
    success = 0  # 奖励已到背包，请注意查收
    validation_fails = 1  # 未知错误，请联系客服   礼品卡号格式不正确
    over_card_limit = 2  # 该礼包码已被领取
    expired = 3  # 该礼包码已失效
    channel_err = 4  # 无法领取该礼包码     该卡不能在此运营商使用
    server_err = 5  # 无法领取该礼包码     该卡不能在这个服务器使用
    illegal = 6  # 该礼包码已失效
    over_role_limit = 7  # 已领取过该礼包


class CardValidateErr(Exception): pass


def send_gift(card_no, player_id, server_id):
    """发送礼包卡奖励"""

    # 获取礼包卡标识（前三位）
    card_key = card_no[:3]

    # 根据礼包卡标识查出奖励
    card_batch = CardBatch.objects.using('card').get(key=card_key)
    gifts = json.loads(card_batch.prize)

    # 拼接GM命令
    GM_str = '#gmMail ' + str(player_id) + u' 礼包卡奖励 礼包卡奖励 '
    for gift in gifts:
        GM_str += str(gift['aID']) + ',' + str(gift['id']) + ',' + str(gift['v']) + ';'
    GM_str = GM_str.rstrip(';')

    # 发送GM命令
    gmp = GMProtocol(int(server_id))
    gmp.send_mail(GM_str)


# http://service.fytxonline.com/card_service/?player_id=29363211&card_no=102442987degyqy&server_id=28
def card(request):
    '''客户端礼包卡接口
    '''
    # import pdb;pdb.set_trace()
    post_data = request.REQUEST
    card_no = post_data.get('card_no', '').lower()
    server_id = post_data.get('server_id', '')
    channel_id = post_data.get('channel_id', '')
    player_id = post_data.get('player_id', '')
    level = post_data.get('player_level', '')

    # _r = {"code":CardReCode.unknow_err,"msg":"未知错误!","name":"","prize":{}}
    _r = {"code": CardReCode.unknow_err}
    if channel_id:
        try:
            channel_id = str(Channel.objects.get(channel_key=channel_id).id)
        except Exception, e:
            print 'get_channel_id error(%s) : %s ' % (channel_id, str(e))

    validate_card = ''
    print 'card_no', card_no
    print 'server_id', server_id
    print 'player_id', player_id
    print 'channel_id', channel_id
    print 'level', level
    try:
        if server_id != '' and card_no != '' and player_id != '' and re.match('^\d+$', server_id):
            key = card_no[0:3]
            validate_card = Card.check_card(card_no)
            print 'validate_card', validate_card
            if validate_card and CardBatch.check_card_key(key):
                player_id = int(player_id)

                Card._meta.db_table = Card.get_card_table_name(key)
                the_card = Card.objects.using('card').extra(
                    where=["number = '%s' and (status <> -1 ) or status IS NULL " % card_no])

                if the_card:
                    the_card = the_card[0]
                    the_card.use_count = the_card.get_use_count()
                    batch_id = the_card.batch.id
                    card_batch = CardBatch.objects.using('card').get(id=batch_id)

                    card_limit_count = card_batch.card_limit_count
                    # _r['name'] = card_batch.name
                    if the_card.use_count >= card_limit_count:
                        # raise CardValidateErr(CardReCode.over_card_limit,'该礼品卡号已被使用过!')
                        raise CardValidateErr(CardReCode.over_card_limit, '')

                    if card_batch.status == 0:
                        # raise  CardValidateErr( CardReCode.illegal,'该类礼品卡不存在此卡号!'  )    #禁用了
                        raise CardValidateErr(CardReCode.illegal, '')
                    else:
                        if card_batch.server != '':
                            server_list = card_batch.server.split(',')
                        else:
                            server_list = []

                        if card_batch.channels != '':
                            channels = card_batch.channels.split(',')
                        else:
                            channels = []
                        current_unixtime = int(time.time())
                        start_time = int(time.mktime(card_batch.start_time.timetuple()))
                        end_time = int(time.mktime(card_batch.end_time.timetuple()))
                        role_limit_count = card_batch.limit_count

                        if current_unixtime < start_time or current_unixtime > end_time:
                            # raise  CardValidateErr( CardReCode.expired,'该礼品卡不在有效期内!'  )
                            raise CardValidateErr(CardReCode.expired, '')
                        elif server_list.__len__() > 0 and server_id not in server_list:
                            # raise CardValidateErr( CardReCode.server_err,'该礼品卡不能应用于您所在服务器!' )
                            raise CardValidateErr(CardReCode.server_err, '')
                        elif channels.__len__() > 0 and channel_id not in channels:
                            # raise CardValidateErr( CardReCode.channel_err,'该礼品卡不能应用于您所在运营商!')
                            raise CardValidateErr(CardReCode.channel_err, '')
                        elif role_limit_count > 0:
                            validate_limit_count = CardLog.objects.using('card').filter(player_id=player_id,
                                                                                        server_id=server_id,
                                                                                        card_key=key).count()
                            if role_limit_count <= validate_limit_count:
                                # raise CardValidateErr(CardReCode.over_role_limit,'您已达到领取该礼包的次数上限!')
                                raise CardValidateErr(CardReCode.over_role_limit, '')

                        player_obj = GamePlayerInfo(player_id)
                        limit_level = card_batch.get_condition_for_key('level')
                        if int(limit_level):
                            player_level = player_obj.get_level()
                            if player_level < limit_level:
                                _r['level'] = limit_level
                                raise CardValidateErr(CardReCode.level_not_enough, '该礼品卡需要%s级才可使用!' % limit_level)

                        the_card.use_count = the_card.use_count + 1
                        the_card.status = 2  # 已使用
                        #                        the_card.use_time = datetime.datetime.now()
                        #                        the_card.server_id = server_id
                        #                        the_card.channel_key = channel_id
                        #                        the_card.player_id = player_id
                        the_card.save(using='card')

                        card_batch.used_count = card_batch.used_count + 1
                        card_batch.save(using='card')

                        card_log = CardLog()
                        card_log.card_key = key
                        card_log.channel_key = channel_id
                        card_log.server_id = server_id
                        card_log.player_id = player_id
                        card_log.card_name = card_batch.name
                        card_log.number = card_no
                        card_log.prize = card_batch.prize
                        card_log.save(using='card')
                        # if card_log.prize:
                        #     _r['prize'] = json.loads(card_log.prize)

                        # _r['msg'] = "成功！"
                        _r['code'] = CardReCode.success

                else:
                    # raise CardValidateErr(CardReCode.not_exist,'该类礼品卡不存在此卡号!')
                    raise CardValidateErr(CardReCode.not_exist, '')
            else:
                raise CardValidateErr(CardReCode.not_exist, '')
                # raise CardValidateErr(CardReCode.validation_fails,'礼品卡号格式不正确!')

    except CardValidateErr, err_info:
        _r['code'] = err_info[0]
        # _r['msg'] = err_info[1]
    except Exception, e:
        traceback.print_exc()
        _r['msg'] = '未知错误!'
        _r['code'] = CardReCode.unknow_err

    # 发送奖励
    if _r['code'] == CardReCode.success:
        send_gift(card_no, player_id, server_id)

    return HttpResponse(json.dumps(_r, ensure_ascii=False))

# =======
# #! /usr/bin/python
# # -*- coding: utf-8 -*-
# #
# #主页,登录相关
# #
# #django 常用导入
# #=========================================
# from django.core.urlresolvers import reverse  
# from django.db import connection,connections
# from django.utils.html import conditional_escape 
# from django.http import HttpResponse
# from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
# from django.views.generic import ListView,View
# #==========================================


# import sys
# import datetime, time
# from views.base import notauth
# from django.core.serializers import serialize,deserialize
# from models.admin import Admin, Role 
# from models.channel import Agent,Channel
# from util import trace_msg
# from util import TIMEFORMAT,DATETIMEFORMAT
# import traceback
# from urls.AutoUrl import Route
# from settings import TITLE as Title
# @Route()
# def doc(request):
#     return render_to_response('doc.html', locals()) 

# @Route()
# def index(request):
#     '''主页
#     '''
#     list_menu = request.admin.get_resource('menu').filter(is_show=1).order_by('order')
#     now_timestamp = int(time.time())
#     TITLE = Title
#     return render_to_response('index.html', locals())


# @Route()
# def home(request):
#     from models.platform import PlatForm
#     platform_list = request.admin.get_resource('platform')
#     return render_to_response('home.html',locals())

# class LoginError(Exception):pass


# def check_login_status(request):
#     '''登录状态检测
#     '''
#     now = datetime.datetime.now()
#     err_msg = ''
#     err_count = request.session.setdefault('err_count', 0)
#     max_count = 10

#     if err_count >= max_count:
#         lock_time = request.session.setdefault('lock_time',now + datetime.timedelta(minutes=max_count))
#         if now < lock_time:
#             request.session.clear()
#             return '错误登录次数过多,请在  %s 后再登录！' % lock_time.strftime(TIMEFORMAT)
#         else:
#             del request.session['err_count']
#             del request.session['lock_time']

#     if request.POST.get('verify', '') != request.session.get('verify',''):#验证码
#             return '验证码错误 !'   


# @Route('^login$')
# @notauth
# def login(request):
#     '''登录
#     '''
#     now = datetime.datetime.now()
#     if request.method == 'POST':
#         username = request.POST.get('username', '').strip()
#         password = request.POST.get('passowrd', '').strip()
#         request.COOKIES["username"] = username

#         try:
#             login_status_err_msg = check_login_status(request)
#             if login_status_err_msg:
#                 raise LoginError(login_status_err_msg)

#             if username == password :
#                 raise  LoginError( '请联系管理员修改密码!')
#             if not username or not password :
#                 raise  LoginError( '账号或密码为空!')
#             the_admins = Admin.objects.filter(username=username)
#             if the_admins:
#                 the_admin = the_admins[0]
#             else:
#                 raise  LoginError( '%s 账户不存在!' % username)
#             if the_admin.status != Admin.Status.NORMAL:
#                 raise  LoginError( '账户已  %s' % the_admin.get_status_display())
#             if the_admin.md5_password() == the_admin.md5_password(password):
#                 request.session.clear()
#                 request.session['admin_id'] = the_admin.id
#                 the_admin.login_count += 1
#                 the_admin.last_time = now
#                 the_admin.last_ip = request.real_ip
#                 the_admin.session_key = request.session.session_key
#                 the_admin.save()
#                 redirect_url = request.REQUEST.get('from_url','/index')
#                 return HttpResponseRedirect(redirect_url)
#             else:
#                 raise  LoginError( '密码错误!')
#         except LoginError,err_msg:   
#             err_msg = err_msg
#             request.session['err_count'] = request.session.get('err_count',0) +1

#     return render_to_response('login.html', locals())


# @Route('^logout$')
# @notauth
# def logout(request):
#     '''登出
#     '''
#     agent_id = request.session.get('agent_id', None)    #渠道登录的
#     request.session.clear()
#     if agent_id:
#         return HttpResponseRedirect("/channel/login")
#     return HttpResponseRedirect("/login")


# @Route('^channel/login')
# @notauth
# def channel_login(request):
#     anget_name = '渠道'

#     if request.method == 'POST':
#         username = request.POST.get('username', '').strip()
#         password = request.POST.get('passowrd', '').strip()
#         request.COOKIES["username"] = username

#         try:
#             login_status_err_msg = check_login_status(request)
#             if login_status_err_msg:
#                 raise LoginError(login_status_err_msg)
#             if username == password :
#                 raise  LoginError( '请联系管理员修改渠道密码!')
#             if not username or not password :
#                 raise  LoginError( '账号或密码为空!')
#             the_admins = Agent.objects.filter(username=username)
#             if the_admins:
#                 the_admin = the_admins[0]
#             else:
#                 raise  LoginError( '%s 账户不存在!' % username)

#             if the_admin.password == password:
#                 request.session.clear()
#                 request.session['agent_id'] = the_admin.id
#                 the_admin.login_count += 1
#                 the_admin.last_time = datetime.datetime.now()
#                 the_admin.last_ip = request.real_ip
#                 the_admin.session_key = request.session.session_key
#                 the_admin.save()
#                 redirect_url = request.REQUEST.get('from_url','/index')
#                 return HttpResponseRedirect(redirect_url)
#             else:
#                 raise  LoginError( '密码错误!')
#         except LoginError,err_msg:   
#             err_msg = err_msg
#             request.session['err_count'] = request.session.get('err_count',0) +1
#     return render_to_response('login.html', locals())
