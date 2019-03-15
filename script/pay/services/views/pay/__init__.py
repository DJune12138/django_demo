# -*- coding: utf-8 -*-
'''
充值相关
'''

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from models.pay import PayAction,PayChannel
from models.channel import Channel,ChannelOther
from views import md5,getConn
from util.http import http_post,HttpTimeOut
import datetime,json,os
import traceback
import time

from views.game.pay import async_game_pay
from util import trace_msg
import socket
from settings import APP_LABEL
import os,math
from views.upload_douzhen import upload_douzhen_post
from views.upload_reyun import upload_reyun_post
from views.upload_trackingio import upload_trackingio_post
from views.upload_track import upload_track_post
from models.server import Server
from models.player import Player
from models.channel import Channel
from models.center import User
from views.game.game_def import Occupation_Map,HEAD_TITLE,TRIBE_TITLE, PLAYER_INFO_MAP
from views.game.base import GMProtocol

from settings import PAY_FUNC_URL

upload_tracking_channels = ["ylstyaxd_appstore_appstore"]
upload_track_channels = ["mhtxxw_appstore_appstore"]
BASE_LOG_PATH = os.path.join(APP_LABEL,'logs/pay/').replace('\\','/')

def Log(Type,msg):
    now = time.strftime("%Y%m%d")
    # 本机测试
    # pwd = os.path.join(os.getcwd(),"/").replace('\\','/')
    # pwd = os.getcwd() + "/"
    # path = pwd + BASE_LOG_PATH + '%s.log'%(now)
    # 上传
    path =  BASE_LOG_PATH + '%s.log'%(now)

    now_time = time.strftime("%Y-%m-%d %H:%M:%S")
    msg =  now_time + ' [%s] '%(Type) + '%s'%msg
    msg += '\n'
    with open(path,'a') as L:
        L.write(msg)

def strQ2B(ustring):
#把全角字符串转半角
    ustring=ustring.decode("utf-8")
    rstring=""
    for uchar in ustring:
        inside_code=ord(uchar)
        #print inside_code
        if inside_code==0x3000:
            inside_code=0x0020
        else:
            inside_code-=0xfee0
        if inside_code<0x0020 or inside_code>0x7e:
            rstring+=uchar.encode('utf-8')
        else:
            rstring+=(unichr(inside_code)).encode('utf-8')

    return rstring


func_list = {}
def getFunc(func_name,func_ver=0,_func_list=[]):

    if len(_func_list)==0:
        _func_list = ['confirm_%s'%func_name,'confirm_%s_get_link_id'%func_name]

    the_func = func_list.get(str(_func_list),None)

    if the_func == None:
        try:
            loadFunc(func_name,func_ver)
            the_module = __import__('services.views.pay.%s'%func_name,fromlist=_func_list)
            the_func = []
            for item in _func_list:
                the_func.append(getattr(the_module,item))
            func_list[str(_func_list)] = the_func
        except Exception,e:
            traceback.print_exc()
            print('load func has error',e,func_name)
    return the_func

def loadFunc(func_name,func_ver=0):
    #判断本地是否有文件,如果没有,从远程获取,如果有,检查版本
    is_reload = True
    func_path = '%s/%s.py'%(os.path.dirname(__file__),func_name)
    if os.path.exists(func_path):
        if func_ver>0:
            f = open(func_path,'r')
            func_str = f.read()
            f.close()
            if func_str.find('FUNC_VER=%d'%func_ver)!=-1:
                is_reload = False
        else:
            is_reload = False
    if is_reload:
        func_url = '%s%s.py'%(PAY_FUNC_URL,func_name)
        func_str = http_post(func_url)

        func_str = func_str.decode('utf-8')

        if func_str.find(func_name)!=-1:
            f = open(func_path,'wb')
            f.write(func_str.encode('utf-8'))
            f.close()

def getPlayer(server_id,user_type,open_id):
    conn = getConn(server_id)
    pay_user = 0
    channel_id = 0
    try:
        query_sql = "select player_id,channel_id from player_%d where user_type=%d and link_key='%s'"%(server_id,user_type,open_id)
        cursor = conn.cursor()
        cursor.execute(query_sql)
        pay_user_record = cursor.fetchone()

        if pay_user_record!=None:
            pay_user = int(pay_user_record[0])
            channel_id = int(pay_user_record[1])
        else:
            print 'get player not find...'
    except Exception,e:
        print('get player has error',e)
#    finally:
#        conn.close()
    return (pay_user,channel_id)

def get_again(player_id):
    channel_id = 0
    conn = getConn()
    try:
        query_sql = "select channel_id from player_all where player_id=%d" % (player_id)
        print(query_sql)
        cursor = conn.cursor()
        cursor.execute(query_sql)
        pay_user_record = cursor.fetchone()
        if pay_user_record != None:
            # pay_user = int(pay_user_record[0])
            channel_id = int(pay_user_record[0])
    except Exception, e:
        print('get player_channel_id has error', e)
    return channel_id

def getPlayerChannelId(server_id,player_id):
    channel_id = 0
    conn = getConn(server_id)
    try:
        query_sql = "select channel_id from player_%d where player_id=%d"%(server_id,player_id)
        print(query_sql)
        cursor = conn.cursor()
        cursor.execute(query_sql)
        pay_user_record = cursor.fetchone()
        if pay_user_record!=None:
            #pay_user = int(pay_user_record[0])
            channel_id = int(pay_user_record[0])
    except Exception,e:
        print('get player_channel_id has error',e)
#    finally:
#        conn.close()
    return channel_id

def getChannelId(channel_key):
    channel_id = 0
    try:
        if channel_key.find(',')!=-1:
            channel_key = channel_key.split(',')[0]

        channel_list = Channel.objects.using('read').filter(key=channel_key)
        if 0 != channel_list.__len__():
            channel = channel_list[0]
            channel_id = channel.id
    except Exception,e:
        print('get channel_id has error',e)
    return channel_id

def getChannelIds(channel_keys):
    channel_ids = []
    try:
        channels = Channel.objects.using('read').filter(channel_key__in=channel_keys)
        for item in channels:
            channel_ids.append(item.id)
    except Exception,e:
        print 'get channel_ids has error',e
    return channel_ids

def getAdKey(mobile_key):
    try:
        users = User.objects.using('read').filter(mobile_key=mobile_key)
        if len(users) > 0:
            user = users[0]
            print 'idfa:',user.ad_key
            return user.ad_key
    except Exception,e:
        print 'get AD key has Error',e
    return ""

def pay(request,pay_type=0):
    #验证相同的卡号是否已经提交
    print(request.POST)
    the_action = PayAction()
    the_action.card_no = request.POST.get('cardid','')
    the_action.card_pwd = request.POST.get('cardpass','')
    the_action.pay_user = int(request.POST.get('userid','0'))
    the_action.server_id = int(request.POST.get('serverid','1'))
    the_action.post_amount = float(request.POST.get('amount','0.00'))
    the_action.channel_key = request.POST.get('from','')
    pay_type = int(pay_type)
    if pay_type==0:
        pay_type = int(request.POST.get('type',0))
    the_action.pay_type = pay_type
    the_action.pay_ip = request.META.get('REMOTE_ADDR','')
    the_action.post_time = datetime.datetime.now()
    pay_status = 0

    if the_action.card_no!='' and the_action.card_pwd!='' and the_action.post_amount > 0:
        try:
            the_action.card_no = strQ2B(the_action.card_no)
        except:
            print('strq2b has error')

        the_action.query_id = the_action.get_query_id()

        result_code = 0
#        if True:
        try:
            pay_channel = PayChannel.objects.using('read').get(id=the_action.pay_type)
            the_action.channel_id = getChannelId(the_action.channel_key)
            the_action.safe_save()

            pay_status = the_action.query_id
            #向支付接口提交数据,返回值1为成功
            func_path = pay_channel.get_config_value('func_path',pay_channel.func_name)
            pay_func = getFunc(func_path,0,['pay_%s'%func_path])[0]
            result_code,msg = pay_func(the_action,pay_channel,request.get_host())

            if result_code == 1:
                the_action.pay_status = 1
            else:
                the_action.pay_status = -2
                the_action.remark = msg


                the_action.save(using='write')
                if the_action.is_sure_pay():
                    async_game_pay(the_action,pay_channel)
#            通知成功,去失败对列里找一个发送
        except Exception,e:
            #不成功
            print('pay has error',e)
            pay_status = 0
    else:
        pay_status = 0

    return render_to_response('pay/pay_post.html',locals())

# charge_type
# 0 普通充值
# 1 月卡
# 2 周卡
# 3 神秘礼包
# 4 1元每日礼包
# 5 3元每日礼包
# 6 6元每日礼包
# 7 全部每日礼包
# 8   30-50级成长基金
# 9   54-70级成长基金
# 10  73-85级成长基金
# 11  每月特卖

def return_charge_type(Type):
    # charge_type_map = {}
    charge_type = ["60灵玉","300灵玉","980灵玉","1980灵玉","3280灵玉","6480灵玉","月卡","周卡","神秘礼包","1元每日礼包",
                    "3元每日礼包","6元每日礼包","30-50级成长基金",
                    "54-70级成长基金","73-85级成长基金","月特卖18元","月特卖30元","月特卖98元","月特卖198元","月特卖328元","月特卖648元","月特卖108元"]

    # for i in range(charge_type.__len__()):
    #     charge_type_map[i] = charge_type[i]

    # return charge_type_map[]
    if type(Type) == int and Type <= charge_type.__len__():
        return charge_type[Type-1]
    try:
        Type = int(Type)
        if Type <= charge_type.__len__():
            return charge_type[Type-1]
        return Type
    except:
        return Type
    return Type

def get_mobile_key(server_id,player_id):
    conn = getConn(server_id)
    try:
        sql = """select p.mobile_key,p.other from player_%s p where player_id=%s"""%(server_id,player_id)
        cursor = conn.cursor()
        cursor.execute(sql)
        player_info = cursor.fetchone()
        if player_info and player_info[0]:
            print 'mobile_key:',player_info[0]
            if player_info[1]:
                print 'channel_sub_key:',player_info[1]
            conn.close()
            return player_info[0],player_info[1] if player_info[1] else ""
    except BaseException as e:
        print 'get_mobile_key Error:%s'%e
        return "",""
    return "",""

def getOpen_id(server_id,player_id):
    conn = getConn(server_id)
    sql = """select p.link_key from player_%s p where player_id=%s"""%(server_id,player_id)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        open_id = cursor.fetchone()
        print "link_key :",open_id[0]
        conn.close()
        if open_id:
            return open_id[0] if open_id[0] else ""
    except Exception as e:
        print 'get open_id error:',e
        return ""

def getVipLevel(server_id,player_id):
    conn = getConn(server_id)
    sql = """select max(f2+0) from log_player_vip where log_user=%s"""%(player_id)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        data = cursor.fetchone()
        print "vip level:",data[0]
        conn.close()
        if data:
            return int(data[0]) if data[0] else 0
    except BaseException as e:
        print 'get vip level error:',e
        return 0

def check_client_info(request):
    '''（韩国服）校验客户端发过来的数据，然后调用请求韩国PGP，根据结果调用confirm'''
    import requests
    result={'code':0,'msg':''}
    try:
        if request.method == "POST":
            Log('info', "func_name=%s;  POST%s" % ('pangsky', request.POST))
        if request.method == "GET":
            Log('info', "func_name=%s;  GET%s" % ('pangsky', request.GET))

        # print json.loads(request.POST['auth_data'])
        auth_data = json.loads(request.POST.get('auth_data', ''))
        order_type = request.POST.get('order_type','')        
        if not auth_data or not order_type:
            result['msg']  ='not authData or order_type'
            return HttpResponse(json.dumps(result))
        post_url=''
        paycha = PayChannel.objects.filter(func_name='pangsky').first()    #################
        if order_type =='0':
            post_url=(eval(paycha.post_url))['Google']
            print post_url
        elif order_type =='1':
            post_url=(eval(paycha.post_url))['OneStore']
            print post_url
        elif order_type == '2':
            post_url = (eval(paycha.post_url))['apple']
            print post_url
        else:
            result['msg'] = 'fail order_type'
            return HttpResponse(json.dumps(result))
        res = requests.post(url=post_url,data=json.dumps(auth_data),headers={'Content-type':'application/json; charset=UTF-8'})
        ##请求韩国PGP验证成功：
        if json.loads(res.text)['api_result'] == 1:
            if order_type == '2':
                request.POST._mutable = True
                request.POST['order_id'] = json.loads(res.text).get("order_id","")
            return confirm(request,func_name='pangsky')
        else:
            Log('ERROR', res.text)
            result['msg'] = 'cannot connect korean PGP'

        return HttpResponse(json.dumps(result))
    except Exception,e:
        result['msg']=e
        Log('ERROR', e)
    return HttpResponse(json.loads(result))



def confirm(request,func_name=''):

    if func_name=='':
        func_name = 'youai'

    #取得方法名
    pay_channel = None
    func_path = func_name
    #lowB写法
    if func_name =='pangsky':
        pass
    else:
        if request.method=="POST":
            Log('info', "func_name=%s;  POST%s" % (func_name,request.POST))
        if request.method == "GET":
            Log('info', "func_name=%s;  GET%s" % (func_name,request.GET))
    try:
        pay_channels = PayChannel.objects.using('read').filter(func_name=func_name)
        if len(pay_channels) > 0:
            pay_channel = pay_channels[0]
            func_path = pay_channel.get_config_value('func_path',func_name)
            print func_path
    except Exception,e:
        Log('ERROR',e)
        print('get func_path has error',e)

    last_msg = {'msg':'unknow pay_channel',"code":0}
    if not getFunc(func_path):
        # return render_to_response('pay/pay_post.html',last_msg=json.dumps(last_msg))
        return HttpResponse(json.dumps(last_msg))

    confirm_func,get_link_id_func = getFunc(func_path)[:2]

    if confirm_func==None:
        print request.POST,request.GET
        Log('ERROR',last_msg)
        return HttpResponse(json.dumps(last_msg))

    link_id = ''
    try:
        link_id = get_link_id_func(request)

    except Exception,e:
        print('%s get link_id has error'%func_name,e)
        Log('ERROR','%s get link_id has error:'%func_name+'%s'%e)
        traceback.print_exc()
    result = {}
    params = {}

#    if True:
    try:
        if link_id != None and link_id:
            pay_channels = PayChannel.objects.using('read').filter(func_name=func_name,link_id=link_id)
            if len(pay_channels) > 0:
                pay_channel = pay_channels[0]
            if pay_channel == None:
                pay_channel = PayChannel()

        result_list = confirm_func(request,pay_channel)
        # params["appid"] = pay_channel.get_config_value('reyun_id','')
        if type(result_list) != list:
            result_list = [result_list]
        if len(result_list) > 0:
            #数据表锁定
            #PayAction.lock()
            pass
        Log('ERROR', '1111111111111111111')
        for result in result_list:
            try:
                if result["result_msg"] != "SUCCESS":
                    continue
                pay_action_id = result.get('pay_action_id', '')
                query_id = params["query_id"] = result.get('query_id','')
                order_id = result.get('order_id','')
                amount = params["pay_amount"] = result.get('amount',0)
                remark = result.get('remark','')
                charge_id = int(result.get('charge_id'))
                charge_type = int(result.get('charge_type'))
                # params["charge_type"] = return_charge_type(charge_id) if charge_id != 999 else ""
                payType = params["payType"] = result.get('payType')

                pay_type = result.get('pay_type',0)
                _link_id = result.get('link_id',None)

                duplicate_order = PayAction.objects.using("write").filter(query_id=query_id,pay_status=4)
                if duplicate_order:
                    #PayAction.unlock()
                    last_msg={"message":"SUCCESS","code":1}
                    if func_name == "douzhen" or func_name=="douzhenb":
                        last_msg = last_msg["message"]
                    Log('WARNING', 'confirm %s  query_id=%s duplicate order' % (func_name, query_id))
                    return HttpResponse(json.dumps(last_msg))

                if pay_type > 0 :
                    pay_channel = PayChannel.objects.using('read').get(id=pay_type)
                elif _link_id!=None:
                    pay_channels = PayChannel.objects.using('read').filter(func_name=func_name,link_id=_link_id)
                    if len(pay_channels) > 0:
                        pay_channel = pay_channels[0]

                pay_channel_str = result.get('pay_channel_str','') or link_id

                server_id = params["server_id"] = int(result.get('server_id',0))
                player_id = params["player_id"] = int(result.get('player_id',0))
                params["mobile_key"],params["channel_sub_key"] = get_mobile_key(server_id,player_id)
                # params["idfa"] = getAdKey(params["mobile_key"]) if params["mobile_key"] else ""
                user_channel_id = 0
                params["currency"] = result.get("currency")
                the_actions = []

                if pay_action_id != '':
                    tmp_the_action = PayAction.objects.using('write').get(id=pay_action_id)
                    the_actions.append(tmp_the_action)

                if query_id != '' and the_actions.__len__() == 0:
                    the_actions = PayAction.objects.using('write').filter(query_id=query_id)
                elif order_id != '' and the_actions.__len__() == 0:
                    if pay_channel!=None and pay_channel.id != None:
                        the_actions = PayAction.objects.using('write').filter(pay_type=pay_channel.id,order_id=order_id)
                if len(the_actions) > 0:
                    the_action = the_actions[0]
                else:
                    the_action = PayAction()

                channel_id_list_str = ''
                channel_id = 0
                if pay_channel!=None:
                    channel_id_list_str = pay_channel.channel_key# ,1,2,3,
                    if channel_id_list_str != '':
                        #去掉 首尾  , 号 客户端get_pay_channel 中因为用了  container 所以必须要有临界区分符号。
                        channel_id_list_str = channel_id_list_str[1:-1]
                        #第一优先
                if the_action.id==0 or the_action.id==None:
                    print('new record')
                    if pay_channel!=None:
                        the_action.pay_type = pay_channel.id
                    if query_id!='':
                        the_action.query_id = query_id
                    else:
                        the_action.set_query_id()
                    #新建订单号时,初始化状态
                    the_action.pay_status = the_action.pay_status or 0
                    the_action.server_id = server_id
                    the_action.pay_user = player_id
                    the_action.order_id = order_id
                    the_action.charge_id = charge_id
                    the_action.charge_type = charge_type
                    the_action.payType = payType
                    the_action.channel_sub_key = params["channel_sub_key"]
                else:

                    if pay_channel!=None and pay_channel.id!=None and the_action.pay_type!=None and the_action.pay_type>0 and pay_channel.id!=the_action.pay_type:
                        pay_type = the_action.pay_type
                        pay_channel = PayChannel.objects.using('read').get(id=pay_type)
                        channel_id_list_str = pay_channel.channel_key# ,1,2,3,
                        if channel_id_list_str != '':
                            channel_id_list_str = channel_id_list_str[1:-1]#

                    if channel_id_list_str=='' and the_action.channel_id!=0:
                        channel_id_list_str = str(the_action.channel_id)
                        #客户端渠道KEY

                open_id = result.get('open_id','')

                #取不到关联账号时，用player_id取
                if server_id and player_id and not open_id:
                    open_id = getOpen_id(server_id,player_id)
                the_action.open_id = open_id

                # 取玩家vip等级
                vip_level = getVipLevel(server_id,player_id)
                the_action.vip_level = vip_level
                #当玩家编号为0时,通过open_id和user_type取得玩家ID
                if the_action.pay_user == 0:
                    user_type = result.get('user_type',0)
                    if open_id!='' and server_id>0:
                        player_id,user_channel_id = getPlayer(server_id,user_type,open_id)

                        the_action.pay_user = player_id

                if the_action.server_id == 0:
                    the_action.server_id = server_id

                #当订单号为空时,赋值
                if the_action.order_id==None and order_id!='':
                    the_action.order_id = order_id

                #当支付类型为0是,赋值
                if the_action.pay_type == 0:
                    the_action.pay_type = pay_channel.id

                #当支付状态为非成功状态时,可以将状态通知为成功
                if the_action.pay_status==None:
                    the_action.pay_status = 0
                #print ('the_action.pay_status, amount',the_action.pay_status, amount)
                if amount > 0:
                    if the_action.pay_status < 2:
                        #当订单渠道为空时:
                        if the_action.channel_id==None or the_action.channel_id==0:
                            #取USER_channel_id
                            if user_channel_id == 0 and the_action.pay_user > 0 and the_action.server_id>0:
                                user_channel_id = getPlayerChannelId(the_action.server_id,the_action.pay_user)

                                if user_channel_id==0:
                                    server_db= Server.objects.filter(id=server_id)[0]
                                    db_config = json.loads(server_db.log_db_config)
                                    db_id = db_config.get("db","").replace("ss_log","")
                                    user_channel_id = getPlayerChannelId(int(db_id), the_action.pay_user)

                                    if user_channel_id == 0:
                                        user_channel_id = get_again(the_action.pay_user)
                            #当玩家ID大于0并且支付通道的渠道为0时,取玩家的渠道号
                            if channel_id_list_str!='':
                                if channel_id_list_str.find(',')>-1:
                                    f_channel_ids = [int(item) for item in channel_id_list_str.split(',')]
                                    if user_channel_id in f_channel_ids:
                                        channel_id = user_channel_id
                                    else:
                                        channel_id = 0
                                # else:
                                #     f_channel_id = int(channel_id_list_str)
                                #     if f_channel_id>0:
                                #         channel_id = f_channel_id

                            # if channel_id == 0 and user_channel_id > 0:
                            #     channel_id = user_channel_id
                            if user_channel_id > 0:
                                channel_id = user_channel_id

                            the_action.channel_id = channel_id
                            # appid_list = params["appid"]
                            params["device_type"] = ""
                            if channel_id != None and channel_id!=0:
                                the_action.channel_key = params["channel_key"] = channel_key =  Channel.objects.get(id=channel_id).channel_key
                                channel_key = channel_key.split("_")
                                if channel_key.__len__() >= 3:
                                    params["device_type"] = channel_key[1]

                            # if type(appid_list) == dict and len(appid_list) >= 2:
                            #     params["appid"] = appid_list["ios"] if params["device_type"] == "appstore"  else appid_list["andorid"]
                            # elif type(appid_list) == dict and len(appid_list) == 1:
                            #     params["appid"] = appid_list["appid"]

                        the_action.pay_status = 2

                        if the_action.post_amount==0 or the_action.post_amount==None:
                            the_action.post_amount = result.get('post_amount',0) or amount
                        the_action.pay_amount = params["pay_amount"] = amount

                        the_action.pay_gold = params["pay_gold"] = math.ceil(pay_channel.get_gold(the_action.pay_amount))  #根据充值通道里面写的比例计算
                        the_action.extra = pay_channel.get_extra(the_action,pay_channel_str)
                    else:
                        if func_path=='apple':
                            #苹果重复订单
                            result['result_msg'] = '-3'
                        else:
                            pass
                else:
                    if the_action.pay_status > -2 and the_action.pay_status < 2:
                        the_action.pay_status = -2

                if remark == '':
                    remark = str(result.get('result_msg',''))
                if remark.find('<script')!=-1:
                    import re
                    remark = re.sub('<script[\s\S]+script>', '',remark)
                the_action.pay_ip = request.META.get('REMOTE_ADDR','')
                the_action.remark = remark

                if the_action.pay_type!=None and the_action.server_id>0 and the_action.pay_user>0:
                    #处理需要返回订单号的情况
                    if str(result.get('result_msg','')).find('{query_id}')!=-1:
                        result['result_msg'] = result.get('result_msg','').replace('{query_id}',the_action.query_id)

                    if charge_id == 999:
                        result['result_msg'] = 'charge error'
                        Log("ERROR","query_id=%s,charge error"%query_id)
                        the_action.pay_status = 5

                    the_action.post_time=datetime.datetime.now()
                    #the_action.id = int(PayAction.objects.all().latest('id').id) +1    #####针对港澳不能用锁添加的
                    the_action.save(using='write')

                    #客户端要附带充值参数
                    extra = result.get("extra","")
                    if the_action.is_sure_pay():

                        async_game_pay(the_action,pay_channel,extra)

                    channel_other_model,_ = ChannelOther.objects.get_or_create(cid=the_action.channel_id)
                    post_reyun = channel_other_model.get_data_detail(key_name="upload_reyun").get("value","")
                    post_track = channel_other_model.get_data_detail(key_name="upload_track").get("value","")
                    post_tracking = channel_other_model.get_data_detail(key_name="upload_tracking").get("value","")

                                                                                                #  安卓 1526350854348-9036052968314198189#3d43d186-7a23-3b2f-8adf-9efd5536d8e8
                                                                                                # ios   1526064346000-3113850#3D5F501B-D3B5-435C-84DB-6F86F64EB031
                    #上传斗阵支付数据
                    if func_name=="douzhen":
                        check_str =  result.get("advertising_id")
                        if check_str.isupper():
                            params["identify"] = "ios"
                            params["douzhen_appid"] = "id1362484819"

                        elif check_str.islower() :
                            params["identify"] = "android"
                            params["douzhen_appid"] = "tw.play9453.mwts"

                        params["appsflyer_id"] = result.get("appsflyer_id")
                        params["advertising_idfa"] = result.get("advertising_id")
                        upload_result=upload_douzhen_post(params)
                        Log("upload douzhen info", upload_result)
                    #上传到热云
                    if len(post_reyun) > 2:
                        params["appid"] = post_reyun
                        upload_result = upload_reyun_post(params)
                        Log("upload reyun info",upload_result)

                    # 上传到trackingIO
                    if len(post_tracking) > 2:
                        params["appid"] = post_tracking
                        upload_result = upload_trackingio_post(params)
                        Log("upload tracking info",upload_result)

                    # 上传到track
                    if len(post_track) > 2:
                        if the_action.channel_key:
                            deviceType = the_action.channel_key.split("_")
                            if deviceType.__len__() >= 3:
                                deviceType = deviceType[1]
                                if deviceType == "appstore" or deviceType == "ios":
                                    params["deviceType"] = "ios"
                                elif deviceType == "andriod":
                                    params["deviceType"] = "andriod"
                        params["appid"] = post_track
                        upload_result = upload_track_post(params)
                        Log("upload track info",upload_result)

                else:
                    tmp_err_msg = result.get('result_msg',None)
                    if tmp_err_msg!=None:
                        tmp_err_msg = str(tmp_err_msg)
                        if -1 == tmp_err_msg.upper().find('ERROR'):
                            result['result_msg'] = 'error order'
                    print('confirm %s pay_type or  server_id or pay_user has error'% func_name,result)
                    Log('ERROR','confirm %s pay_type or  server_id or pay_user has error'% func_name+'%s'%result)
            except Exception,e:
                traceback.print_exc()
                result['result_msg'] = 'unknow error'

                print('confirm %s has Exception error' % func_name,e)
                Log('WARNING','confirm %s  order_id=%s has Exception error=%s'%(func_name,order_id,e))


    except Exception,e:
        print(request.GET,request.POST)
        traceback.print_exc()
        result['result_msg'] = 'unknow error'
        print('confirm %s has Exception error'% func_name ,e)
        Log('ERROR','confirm %s has Exception error'% func_name+'%s'%e)
    finally:
        #PayAction.unlock()
        pass
    headers = result.get('headers',{})
    result_msg = result.get('result_msg','unknow error')
    content_type = "text/html"
    if str(result_msg).find("<?xml")!=-1:
        content_type="text/xml"
    last_msg = {}
    last_msg["code"] = 1 if result_msg == 'SUCCESS' else 0
    last_msg["message"] = result_msg
    if last_msg["code"] == 0:
        Log('ERROR',last_msg)
    # response = render_to_response('pay/pay_post.html',{'pay_status':result_msg})
    # response = render_to_response('pay/pay_post.html',{'msg':result_msg,'code': 1 if result_msg == 'SUCCESS' else 0})
    # if isinstance(headers,dict):
    #     for k,v in headers.iteritems():#add headers
    #         response[k] = v
    # response['Content-Type'] = content_type
    # response['Content-Length'] = len(response.content)
    if func_name=="pangsky":
        if request.POST.get('order_type','') =='2':
            last_msg['order_id']=order_id
    if func_name=="douzhen":
        last_msg = last_msg["message"]
    if func_name=="jingqiocean" or func_name=="jingqioceanandr":
        last_msg={}
        last_msg["msg"] = "" if result_msg == 'SUCCESS' else "error"
        last_msg["status"] = "success" if result_msg == 'SUCCESS' else ""

    return HttpResponse(json.dumps(last_msg))

def pay_channel(request,server_id=0):
    '''客户端充值渠道获取
    '''
    server_id = int(server_id)
    mobile_info = request.META.get('HTTP_USER_AGENT','')
    channel_key = request.GET.get('qd','')
    player_id = int(request.REQUEST.get('player_id','') or 0 )

    if channel_key=='':
        pos_s = mobile_info.find('QD:')
        if pos_s>0:
            pos_s += 3
            channel_key = mobile_info[pos_s:pos_s+10]
    print(channel_key)

    channel_id = getChannelId(channel_key)
    list_record = []
    if channel_id !=0:
        #数据库中的 channel_key  是这样子 ：,1,2, 带有临界区分符号
        list_record = PayChannel.objects.using('read').filter(server_id__in=(0,server_id),status__gt=-1,channel_key__contains= (',%s,' % channel_id))
    if len(list_record)==0:
        list_record = PayChannel.objects.using('read').filter(server_id__in=(0,server_id),status__gt=-1,channel_key='')


    if player_id:
        pay_channel_list = []
        for pc in list_record:
            pay_channel_list.append(str(pc.id))

        first_pay_channel_map = {}
        if pay_channel_list:
            the_first_pay_list = PayAction.objects.raw('select id,pay_type,COUNT(0) pay_count from pay_action where pay_user=%d and server_id=%d and pay_type in (%s) group by pay_type' % (player_id,server_id,','.join(pay_channel_list)))
            for pa in the_first_pay_list:
                first_pay_channel_map[pa.pay_type] = pa.pay_count

            for pc in list_record:
                if first_pay_channel_map.get(pc.id,None) == None:
                    pc.first_rebate = pc.get_config_value('first_rebate',0)

    result = []
    #除去u'',"extra":[{u'amount': 10, u'conditions': [100, 1000]}]
    if list_record:
        for i in list_record:
            if i.pay_config:
                _extra = json.loads(i.pay_config).get('extra',[])
                _l = []
                if _extra:
                    for j in _extra:
                        _d = {"amount":0,"conditions":[0]}
                        _d["amount"] = j["amount"]
                        _d["conditions"] = j["conditions"]
                        _l.append(_d)
                    i.extra = _l
                    i.sdate = i.get_config_value('sdate',0)
                    i.edate = i.get_config_value('edate',0)

    for i in list_record:
        try:
            d = {}
            d['id'] = i.id
            d['status'] = i.status
            d['image'] = i.icon
            d['type'] = i.pay_type
            d['linkid'] = i.link_id
            d['amount'] = i.amount
            d['gold'] = i.gold
            d['exchange'] = i.exchange_rate
            d['name'] = i.name
            d['about'] = i.remark
            d['order'] = i.order
            if hasattr(i,'extra'): d['extra'] = i.extra
            if hasattr(i,'sdate'): d['sdate'] = i.sdate
            if hasattr(i,'edate'): d['edate'] = i.edate
            if hasattr(i,'first_rebate'): d['first_rebate'] = i.first_rebate
            result.append(d)
        except Exception,e:
            traceback.print_exc()

    return HttpResponse(json.dumps(result))


def confirm_test(request):
    print(request.POST)
    return render_to_response('pay/pay_post.html',{'pay_status':'error'})

def result_user(request,server_id=0,account=0):

    start_num=int(request.GET.get('start','0'))
    end_num = int(request.GET.get('end','0'))
    pay_type = int(request.GET.get('type','0'))
    date_str = request.GET.get('date','')
    account = int(account)
    server_id = int(server_id)
    list_record = []
    total_record = 0
    if account > 0 :
        date = None
        query = Q(server_id=server_id,pay_user=account)&~Q(query_id='',pay_status=0)
        if date_str!='':
            try:
                date = datetime.datetime.strptime(date_str,'%Y-%m-%d')
                sdate = date + datetime.timedelta(hours=5)
                edate = sdate + datetime.timedelta(hours=24)
                query = query & Q(post_time__gte=sdate,post_time__lt=edate)
            except:
                date_str = ''

        if pay_type>0:
            query = query & Q(pay_type=pay_type)

        #query = query & Q(pay_amount__gt = 0)
        #print(query)
        total_record = PayAction.objects.using('read').filter(query).count()
        if total_record > 0:
            if start_num>0 or end_num>0 :
                list_record = PayAction.objects.using('read').filter(query)[start_num:end_num]
            else:
                list_record = PayAction.objects.using('read').filter(query)
        list_channel = PayChannel.objects.using('read').filter(server_id__in=(0,server_id))
        channels = {}
        for item in list_channel:
            channels[item.id]=item
        for item in list_record:
            if channels.get(item.pay_type,None)!=None:
                item.pay_type_name = channels[item.pay_type].name
                item.unit = channels[item.pay_type].unit
    return render_to_response('pay/pay_result.html',{'list_record':list_record,'total_record':total_record,'start_num':start_num})

def get_player_info_param():
    return PLAYER_INFO_MAP

