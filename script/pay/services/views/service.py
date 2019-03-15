# -*- coding: utf-8 -*-

import datetime
import json
import base64

import MySQLdb
from django.shortcuts import render_to_response
from django.http import HttpResponse

from util import trace_msg
from services.views.game.base import GMProtocol
from services.views.game.base import write_gm_log
from services.views import getConn, md5
from services.http import http_post
from models.center import Server, Channel, User
from models.log import Log
from models.pay import PayAction
from models.player import Player


def get_argument(request,keys,default):
    if isinstance(keys,basestring):keys = [keys]
    for k in keys:
        _value =  request.GET.get(k,request.POST.get(k,default))
        if _value:return _value
    return default

def server_list(request, agent_name=''):
    g = lambda x,y:request.GET.get(x, request.POST.get(x, y))
    code = 1
    try:
        if agent_name == 'all':
            list_server = Server.objects.all()
        else:
            list_server = Server.objects.filter(agent__name=agent_name)

        code = 0
    except:
        code = -1
        list_server = []
    template = g('template', '')
    if '' != template:
        template = 'client/%s/server_list.html' % template
    else:
        template = 'client/server_list.html'
    return render_to_response(template, locals())

def query(request, func_name=''):
    from services.views.pay import getFunc
    if func_name == '':
        func_name = request.GET.get('type', request.POST.get('type', ''))

    if func_name == '':
        return HttpResponse('')

    try:
        query = getFunc(func_name, _func_list = ['query_%s' % func_name])[0]
        return query(request)
    except Exception, ex:
        print ex
        return HttpResponse('')

def player_info(request):
    player = {'user_id':0, 'player_id':0, 'player_name':'', 'level':0, 'server_id':0}

    try:
        user_type = int(request.GET.get('type', '0'))
        template_name = request.GET.get('template', '')
        if template_name.find('/')>0:
            template = 'client/%s.html' % template_name
        else:
            template = 'client/%s/player_info.html' % template_name if template_name else 'client/player_info.html'

        openid = get_argument(request,['uid','openid','loginName'],0)
        server_id = int(get_argument(request,['serverid','server_id','sid','s_id'],0))
        player['server_id'] = server_id
        if server_id > 0 and openid != '':
            openid = filter_sql(str(openid))

            user_type = user_type
            server = Server.objects.get(id=server_id)
            conn = server.mysql_conn()
            cursor = conn.cursor()
            query_sql = 'select player_id,player_name from player_%d where user_type=%d and link_key="%s"' % (server_id, user_type, openid)

            cursor.execute(query_sql)
            player_list = cursor.fetchall()
            if len(player_list) > 0:
                player['user_id'] = openid
                player['player_id'] = player_list[0][0]
                player['player_name'] = player_list[0][1]
                try:
                    master_server = server.master_server
                    db_name,mongo_conn = master_server.get_mongo_conn()
                    record = mongo_conn[db_name].gl.player.find_one({'pi':player['player_id']},{'lv':1})
                    player['level'] = record['lv']
                    mongo_conn.close()
                except Exception, ex:
                    print trace_msg()

    except Exception, ex:
        print trace_msg()
    return render_to_response(template, {'player':player})

def pay_top_list(request):
    access_ip = ['202.55.12.242', '202.55.12.246', '202.55.12.244']
    ip = ''
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        ip =  request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']

    gl = lambda x: request.GET.getlist(x, [])
    g = lambda x,y: request.GET.get(x, request.POST.get(x, y))

    group_id_list = g('groups', '')
    group_id_list = filter_sql(group_id_list)
    group_id_list = group_id_list.split(',')
    sdate = g('sdate', '')
    edate = g('edate', '')
    code = 0

    if ip not in access_ip:
        return HttpResponse('')

    if sdate == '' or edate == '':
        code = 1
    if group_id_list.__len__() == 0:
        code = 1

    if code != 0:
        return HttpResponse('')
    try:
        sdate = filter_sql(sdate)
        edate = filter_sql(edate)

        sql = '''SELECT pay_user, server_name, pay_amount, pay_gold, pay_time, server_id, open_id
        FROM (
            SELECT pay_user, servers.name AS server_name, SUM(pay_amount) AS `pay_amount`, SUM(pay_gold) AS `pay_gold`,MAX(last_time) AS `pay_time`, pay_action.server_id AS server_id, open_id
                FROM pay_action , servers
                WHERE pay_action.server_id = servers.id AND  pay_status=4 AND pay_amount != 0 AND last_time BETWEEN '%s' AND  '%s' AND pay_action.server_id IN (SELECT server_id FROM groups_server WHERE group_id IN (%s))
                GROUP BY pay_user
            ) AS result
        ORDER BY pay_gold DESC, pay_time ASC LIMIT 50''' % (sdate, edate,','.join(group_id_list))
        center_conn = getConn()
        center_cursor = center_conn.cursor()
        center_cursor.execute(sql)
        data_list = center_cursor.fetchall()
        server_player_dict = {}
        #result_data_list = {}
        for item in data_list:
            pay_user = item[0]
            server_id = int(item[5])
            player_id_list = server_player_dict.get(server_id, [])
            player_id_list.append(str(pay_user))
            server_player_dict[server_id] = player_id_list

            #result_data_list['%s_%s' % (server_id, pay_user)] = {"pay_user":pay_user, "server_name":server_name, "pay_amount": pay_amount, "pay_gold":pay_gold, "pay_time":pay_time, "server_id":server_id, "open_id":open_id, "player_name":'None', "link_key":'None' }

        player_dict = {}
        sql = 'SELECT link_key, player_name, player_id FROM player_%d WHERE player_id IN (%s)'
        for server_id in server_player_dict:
            conn = getConn(server_id)
            cursor = conn.cursor()
            player_id_list = server_player_dict.get(server_id)
            query_sql = sql % (server_id, ','.join(player_id_list))
            cursor.execute(query_sql)
            player_data_list = cursor.fetchall()
            for player in player_data_list:
                link_key = player[0]
                player_name = player[1]
                player_id = player[2]
                player_dict[player_id] = [link_key, player_name]

        result_data_list = []
        for item in data_list:
            pay_user = item[0]
            player_info = player_dict.get(pay_user, [])
            player_name = 'None'
            link_key = 'None'
            if player_info.__len__() != 0:
                link_key = player_info[0]
                player_name = player_info[1]

            data_item = {}
            data_item['pay_user'] = pay_user
            data_item['server_name'] = item[1]
            data_item['pay_amount'] = item[2]
            data_item['pay_gold'] = item[3]
            data_item['pay_time'] = item[4].strftime('%Y-%m-%d %H:%M:%S')
            data_item['server_id'] = item[5]
            data_item['open_id'] = item[6]
            data_item['player_name'] = player_name
            data_item['link_key'] = link_key
            result_data_list.append(data_item)

    except Exception, ex:
        code = 1
        print 'get pay_top_list error:', ex

    if code == 1:
        return HttpResponse('')

    return render_to_response('service/pay_top_list.html', {"result_data_list" : result_data_list})


def pay_count(request):
    access_ip = ['202.55.12.242', '202.55.12.246', '202.55.12.244']
    ip = ''
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        ip =  request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']

    player_id = request.GET.get('playerid', request.POST.get('playerid', '0'))
    open_id = request.GET.get('uid', request.POST.get('uid', '0'))
    server_id = request.GET.get('serverid', request.POST.get('serverid', '0'))
    sdate = request.GET.get('startTime', request.POST.get('startTime', '0'))
    edate = request.GET.get('EndTime', request.POST.get('EndTime', '0'))

    code = 0
    if '0' == server_id or '0' == sdate or '0' == edate  or not ip in access_ip or (open_id == '0' and player_id == '0'):#or ip not in access_ip
        code = 1

    gold = 0
    count = 0
    if 0 == code:
        try:
            player_id = int(player_id)
            server_id = int(server_id)
            open_id = filter_sql(str(open_id))
            sdate = datetime.datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            edate = datetime.datetime.strptime(edate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')

            if player_id == 0:
                query_player_sql = 'SELECT player_id FROM player_%s WHERE link_key = \'%s\' ' % (server_id, open_id)
                conn = getConn(server_id)
                cursor = conn.cursor()
                cursor.execute(query_player_sql)
                player_list = cursor.fetchall()
                if player_list.__len__() > 0:
                    player_id = int(player_list[0][0])

            if player_id != 0:
                query_sql = 'SELECT SUM(pay_gold), COUNT(0) FROM pay_action WHERE pay_user = %s AND pay_status = 4 AND pay_amount != 0 AND last_time BETWEEN \'%s\' AND \'%s\' ' % (player_id, sdate, edate)
                from services.settings import DATABASES
                cfg = DATABASES.get('read')
                cen_conn = MySQLdb.connect(host=cfg.get('HOST'),user=cfg.get('USER'),passwd=cfg.get('PASSWORD'), port=int(cfg.get('PORT', 3306)), db=cfg.get('NAME'),charset='utf8')
                cen_cursor = cen_conn.cursor()
                cen_cursor.execute(query_sql)
                result_list = cen_cursor.fetchall()
                if result_list.__len__() > 0:
                    tmp_value = result_list[0][0]
                    count = result_list[0][1]
                    if None != tmp_value:
                        try:
                            gold = int(tmp_value)
                        except Exception, ex:
                            print 'pay_count error'
                            print ex
                            gold = 0

        except Exception, ex:
            print ex
            pass

    return render_to_response('client/pay_count.html', {"gold":gold, "count":count})

def filter_sql(sql):
    sql = str(sql)
    sql = sql.lower()
    sql = sql.replace('update', '')
    sql = sql.replace('delete', '')
    sql = sql.replace('modify', '')
    sql = sql.replace('column', '')
    sql = sql.replace('lock', '')
    sql = sql.replace('drop', '')
    sql = sql.replace('table', '')
    sql = sql.replace('contains', '')
    sql = sql.replace('\'', '')
    sql = sql.replace('*', '')
    sql = sql.replace('%%', '')

    return sql



def login_query(request,server_id=0):
    channel_username = request.GET.get('username','')
    channel_password = request.GET.get('password','')
    server_id = int(server_id)
    result_code = 0
    if channel_username!='' and channel_password!='' and server_id > 0:
        channel_id = 0

        try:
            channels = Channel.objects.using('read').filter(username=channel_username)
            if len(channels)>0:
                the_channel = channels[0]
                if the_channel.password == channel_password:
                    channel_id = the_channel.id
        except:
            pass

        if channel_id > 0:
            the_date = '%s 00:00:00'%(datetime.datetime.now().strftime('%Y-%m-%d'))
            the_server = Server.objects.using('read').get(id=server_id)
            the_db_config = json.loads(the_server.log_db_config)
            conn = MySQLdb.connect(host=the_db_config['host'],user=the_db_config['user'],passwd=the_db_config['password'], port=the_db_config.get('port',3306),db=the_db_config['db'],charset='utf8')
            query_sql = "select count(0) from log_check_user where channel_id=%d and logtime>='%s'"%(channel_id,the_date)
            cursor = conn.cursor()
            cursor.execute(query_sql)
            pay_user_record = cursor.fetchone()
            if pay_user_record!=None:
                result_code = int(pay_user_record[0])
            conn.close()
        else:
            pass

    return HttpResponse(result_code)




def pay_list(request,server_id=0):
    channel_username = request.GET.get('username','')
    channel_password = request.GET.get('password','')
    server_id = int(server_id)
    pay_actions = []

    if channel_username!='' and channel_password!='' and server_id > 0:
        channel_key = ''

        try:
            channels = Channel.objects.using('read').filter(username=channel_username)
            if len(channels)>0:
                the_channel = channels[0]
                if the_channel.password == channel_password:
                    channel_key = the_channel.key
        except:
            pass

        if channel_key !='':
            the_time = '%s:00:00'%(datetime.datetime.now().strftime('%Y-%m-%d %H'))
            pay_actions = PayAction.objects.using('read').filter(pay_status=4,channel_key=channel_key,post_time__lte=the_time)
        else:
            pass

    return render_to_response('service/pay_list.html', {'pay_actions':pay_actions})


def sgz_betauser_reward(request):
    '''内测付费用户，公测金币回馈,分3次返还，

    就是第一天充值额度100%+100%vip经验  第二次天50%充值额度金票  第三天百分之50%充值额度金票
    '''

    key = "sgztestkey"

    user_type = int(request.POST.get("user_type") or  0)
    link_key = request.POST.get("link_key") or ""
    server_id = int(request.POST.get("server_id") or 0)
    sdate = request.POST.get("sdate", "2999-01-19 00:00:00")
    edate = request.POST.get("edate", "2999-01-19 01:00:00")
    sign = request.POST.get("sign", "")

    sign_con = "%s&%s&%s&%s" % (user_type, link_key, server_id, key)
    if sign != md5(sign_con):
        return HttpResponse("signError")

    link_key32 = link_key[:32] if len(link_key) > 32 else link_key
    if server_id not in [7,9,12]:
        return HttpResponse("ok") #服务器错误 直接返回，不需要循环
    if server_id:
        servdb_conn = getConn(server_id)
        serv_curs = servdb_conn.cursor()
        player_id = 0
        try:
            serv_curs.execute("SELECT player_id, player_name FROM player_%s WHERE user_type=%s AND link_key='%s'" % (server_id, user_type, link_key))
            result = serv_curs.fetchone()
            if result:
                player_id,player_name = result
        except Exception,e:
            print "mysql error: ",e
        finally:
            serv_curs.close()
            servdb_conn.close()

        if not player_name:
            return HttpResponse("player_name_fail")

        center_conn = getConn(alias='write')
        center_curs = center_conn.cursor()
        pay_golds = 0
        sent_number = 0
        today = datetime.date.today()
        sent_date = datetime.date.today() + datetime.timedelta(days = -1)  #初始昨天，统一比较类型,方便判断
        try:
            ############   判断次数  ###########
            sql = "SELECT remark FROM pay_action WHERE open_id='%s' AND pay_status=4 AND pay_amount>0 AND last_time>='%s'" \
                  " AND last_time<'%s' AND server_id in (2,3,4) " % (link_key32, sdate, edate)
            center_curs.execute(sql)
            result = center_curs.fetchone()
            if result:
                remark = result[0]

                if 'sent' in remark:
                    d_n_s = remark.split('_')
                    print '==>d_n_s',d_n_s
                    d = d_n_s[0]
                    sent_number = int(d_n_s[1])
                    sent_date = datetime.date(int(d.split('-')[0]), int(d.split('-')[1]), int(d.split('-')[2]))


            if sent_number == 0 and today > sent_date:
                ####第一天一次领取
                sql = "SELECT SUM(pay_gold) pay FROM pay_action WHERE open_id='%s' AND pay_status=4 AND pay_amount>0 AND last_time>='%s'" \
                      " AND last_time<'%s' AND remark NOT LIKE '%%_sent' AND server_id in (2,3,4)" % (link_key32, sdate, edate)
                center_curs.execute(sql)
                result = center_curs.fetchone()
                if result:
                    pay_golds = result[0]

            if sent_number in (1,2) and today > sent_date:
                ####以后的
                sql = "SELECT SUM(pay_gold) pay FROM pay_action WHERE open_id='%s' AND pay_status=4 AND pay_amount>0 AND last_time>='%s'" \
                      " AND last_time<'%s' AND remark LIKE '%%_sent' AND server_id in (2,3,4)" % (link_key32, sdate, edate)
                center_curs.execute(sql)
                result = center_curs.fetchone()
                if result:
                    pay_golds = result[0]

            if today == sent_date:
                return HttpResponse("ok")

            if sent_number > 2:
                return HttpResponse("numberFail")

        except Exception, e:
            print 'center mysql error: ', e

        update_number = sent_number + 1
        print '==>player_id', player_id
        print "==>update_number: ", update_number
        print "==>pay golds total: ", player_id,pay_golds
        if pay_golds == None:
            return HttpResponse('golds is none')
        pay_golds = int(pay_golds)
        if pay_golds > 0:
            try:

                # GM工具发邮件资源
                #[{"arg": [2097367], "m": "first", "rw": [{"gn": "tes", "gpid": 15001, "gt": 1, "act": [{"aID": 3, "v": 11}, {"aID": 19, "v": 11}]}], "ty": 0}]
                gmp = GMProtocol(server_id)
                if update_number == 1:
                    msg = {"arg": [0], "m": "", "rw": [{"gn": "内测返还礼包", "gpid": 15001, "gt": 1, "act": [{"aID": 3, "v": 0}, {"aID": 19, "v": 0}]}], "ty": 0}
                    msg['arg'][0] = player_id       #添加player_id
                    msg['rw'][0]['act'][0]['v'] = msg['rw'][0]['act'][1]['v'] = pay_golds    #添加100%金币和经验
                    msg['m'] = '内测充值返还第一天奖励'          #礼包描述
                    result = gmp.send_mail(msg)

                elif update_number in (2,3):
                    msg = {"arg": [0], "m": "", "rw": [{"gn": "内测返还礼包", "gpid": 15001, "gt": 1, "act": [{"aID": 2, "v": 0}]}], "ty": 0}
                    msg['arg'][0] = player_id       #添加player_id
                    msg['rw'][0]['act'][0]['v'] = int(pay_golds * 0.5)    #添加50%金票
                    if update_number == 2:
                        msg['m'] = '内测充值返还第二天奖励'
                    else:
                        msg['m'] = '内测充值返还第三天奖励'
                    result = gmp.send_mail(msg)
                
                print '####req_type=1134', result
                if int(result) == 0:
                    # 成功后，修改remark用于标记已使用状态
                    sql = "UPDATE pay_action SET remark='%s_%s_sent' WHERE open_id='%s' AND pay_status=4 AND pay_amount>0 " \
                          "AND last_time>='%s' AND last_time<'%s' AND server_id in (2,3,4)" % (today,update_number,link_key32, sdate, edate)
                    center_curs.execute(sql)
                    return HttpResponse("ok")
            except Exception,e:
                import traceback
                traceback.print_exc()
                return HttpResponse("GMfail")
        else:
            return HttpResponse("noOrder")

        center_curs.close()
        center_conn.close()

    return HttpResponse("fail")


def player_manage(request):
    KEY = 'hrNJKCdoV$q6BZi!'

    TREAT_MAP = {
        1: 'shutup',
        2: 'unshutup',
        3: 'kick',
        4: 'disable_login',
        5: 'enable_login'
    }

    res = {
        'state': 0,
        'data': None,
        'msg': u'失败'
    }

    try:
        atime      = int(request.REQUEST.get('atime', ''))
        uid        = request.REQUEST.get('uid','')
        gid        = int(request.REQUEST.get('gid',''))
        dsid       = int(request.REQUEST.get('dsid',''))
        treat_type = int(request.REQUEST.get('treat_type',''))
        actor_id   = request.REQUEST.get('actor_id','')
        actor_name = request.REQUEST.get('actor_name','')
        sign       = request.REQUEST.get('sign','')
    except:
        print trace_msg()
        return HttpResponse(json.dumps(res, ensure_ascii=False))

    if not atime and not uid or not gid or not dsid or not treat_type or not sign:
        res['msg'] = u'缺少参数'
        return HttpResponse(json.dumps(res, ensure_ascii=False))

    sign_str = '%s' * 6 % (KEY, uid, gid, dsid, treat_type, atime)
    if sign != md5(sign_str):
        print '==> sign: ', sign
        print '==> sign_str: ', sign_str
        res['msg'] = u'签名错误'
        return HttpResponse(json.dumps(res, ensure_ascii=False))

    server_list = []
    if dsid == 0:
        server_list = Server.objects.all()
    else:
        server_list = Server.objects.filter(id=dsid)

    treat_name = TREAT_MAP.get(treat_type)
    if server_list and treat_name:
        msg = u'失败'
        remark = ''
        # GM处理
        if treat_name != 'enable_login':
            for server in server_list:
                try:
                    server_id = int(server.id)
                    query_sql = 'select player_id, player_name from player_%s where link_key=%s' %(server_id, uid)
                    cursor = getConn(server_id).cursor()
                    cursor.execute(query_sql)
                    users = cursor.fetchall()
                    if len(users) > 0:
                        actor_id = users[0][0]
                        actor_name = users[0][1]

                    gmp = GMProtocol(server_id)
                    if treat_name == 'shutup':
                        # 默认禁言10年 0.0
                        seconds = 10*365*24*3600
                        remark = '禁言(%s)秒' % (seconds)
                        result = gmp.player_shutup(actor_id, seconds)
                        msg = u'成功'
                    elif treat_name == 'unshutup':
                        result = gmp.player_unshutup(actor_id)
                        remark = '解除禁言'
                        msg = u'成功'
                    elif treat_name  == 'kick' or treat_name  == 'disable_login':
                        result = gmp.player_kick(actor_id)
                        remark = '踢玩家下线'
                        msg = u'成功'
                    gmp.save_log('', gmp.req_type, result, role_id=actor_id, remark=remark)
                except Exception, e:
                    print '==> server: ', server_id
                    print '==> exception', e

        # 修改账号状态
        if treat_name in ['enable_login', 'disable_login']:
            try:
                user_status = 0
                if treat_name == 'disable_login':
                    user_status = -1

                user = User.objects.get(link_key=uid)
                user.status = user_status
                user.save()
                msg = u'成功'
            except User.DoesNotExist:
                msg = u'失败'
        res['msg'] = msg
        res['state'] = 1 if res['msg'] == u'成功' else 0
    return HttpResponse(json.dumps(res, ensure_ascii=False))


def send_prize(request):
    def json_dumps(data):
        return json.dumps(data, ensure_ascii=False)

    Log._meta.db_table = 'log_gm'
    log_type = 37

    CUSOTM_PRIZE = {
        (5, '冷兵器独家礼包'): [{"gn": "冷兵器独家礼包", "gpid": 15001, "gt": 1, "act": [{"aID": 2, "v": 100}, {"aID": 1, "v": 20000}]}],
        (4, '冷兵器豪华礼包'): [{"gn": "冷兵器豪华礼包", "gpid": 15001, "gt": 1, "act": [{"aID": 2, "v": 200}, {"aID": 1, "v": 100000}, {"aID": 8, "v": 40000}]}],
        (3, '冷兵器至尊礼包'): [{"gn": "冷兵器至尊礼包", "gpid": 15001, "gt": 1, "act": [{"aID": 2, "v": 300}, {"aID": 1, "v": 200000}, {"aID": 8, "v": 60000}]}],
        (6, '一元购礼包'): [{"gn": "周末1元购充值奖励", "gpid": 15001, "gt": 1, "act": [{"aID":2,"v":60},{"aID":12,"id":10001,"v":88}]}]
    }


    KEY = ';CPaRKFSmZgG9MA_rDVubdloiByj0tUW'

    msg = u'通知失败'
    res = {
        'state': 0,
        'data': None,
        'msg': msg,
    }

    try:
        # 请求时间戳
        time      = int(request.REQUEST.get('time'))
        # 中奖编号
        uuid      = request.REQUEST.get('uuid')
        # 联运商ID
        pid       = int(request.REQUEST.get('pid'))
        # 游戏ID
        gid       = int(request.REQUEST.get('gid'))
        # 服ID
        dsid      = int(request.REQUEST.get('dsid'))
        # 游戏角色名
        drname    = request.REQUEST.get('drname')
        # 游戏角色ID
        drid      = int(request.REQUEST.get('drid'))
        # 37帐号唯一标示
        uid       = request.REQUEST.get('uid')
        # 奖品描述内容
        raw_prizedesc = request.REQUEST.get('prizedesc')
        # 签名验证
        sign      = request.REQUEST.get('sign')
    except:
        print trace_msg()
        res['msg'] = u'缺少参数'
        return HttpResponse(json_dumps(res))

    sign_tuple = (KEY, pid, gid, dsid, drname, drid, uid, uuid, time, raw_prizedesc)
    sign_str = '%s' * len(sign_tuple) % sign_tuple
    if sign != md5(sign_str):
        print '==> send_prize sign: ', sign
        print '==> send_prize sign_str: ', sign_str
        res['msg'] = u'签名错误'
        return HttpResponse(json_dumps(res))

    try:
        prizedesc = json.loads(base64.b64decode(raw_prizedesc))
        prizeid = int(prizedesc.get('prizeid', -1))
        prizecontent = prizedesc.get('prizecontent', '').encode('utf-8')
        if not prizecontent or prizeid == -1:
            res['msg'] = u'缺少参数'
        elif not Log.objects.using('read').filter(log_type=log_type, log_user=drid, log_name=uuid, log_result=0).exists():
            # 检查是否已发送成功
            data = {"arg": [drid], "m": "", "rw": [], "ty": 0}
            rw = CUSOTM_PRIZE.get((prizeid, prizecontent), [])
            if prizeid in (3, 4, 5):
                # 游戏内物品奖励
                data['m'] = '恭喜您在“元旦抽奖赢好礼”活动中获得了%s，请注意查收邮件附件内的礼包奖品' % (prizecontent)
                data['rw'] = rw
            elif prizeid in (6,):
                data['m'] = '亲爱的将军：感谢您参与“周末福利，一元限时购”的活动，这是您的专属礼包。感谢您对游戏的支持和喜爱！'
                data['rw'] = rw
            elif prizeid in (0, 1, 2):
                # 实物奖励
                data['m'] = '恭喜您在“元旦抽奖赢好礼”活动中获得了%s，请在七个工作日内联系客服QQ：2880154610，提供中奖信息领取奖品，逾时不候哦' % (prizecontent)

            if data['m']:
                result = 1
                try:
                    gmp = GMProtocol(dsid)
                    result = gmp.send_mail(data)
                    result = int(result)
                    if result == 0:
                        res['msg'] = msg
                        res['state'] = 1
                except:
                    print trace_msg()

                #  log_user, log_type, protocol, server_id, role_id, role_name, log_result, params, return_params, remark1
                write_gm_log(
                    log_user=drid,
                    log_type=log_type,
                    protocol=log_type,
                    server_id=dsid,
                    role_id=drid,
                    role_name=uuid,
                    log_result=result,
                    params=raw_prizedesc,
                    return_params=prizedesc,
                    remark1='37中奖发货')
    except Exception:
        print trace_msg()
    return HttpResponse(json_dumps(res))
