#:coding:utf-8
from django.http import HttpResponse
from models.server import Server
from services.views import getConn
from services.models.log import DictDefine
from services.models.player import Player_operation
from services.models.game import Activity

import hashlib
import time
import json
import MySQLdb
import logging
import logging.handlers
from settings import APP_LABEL
import os
from services.models.player import Player_convert


BASE_LOG_PATH = os.path.join(APP_LABEL,'logs/api/').replace('\\','/')

def Log(Type,msg):
    now = time.strftime("%Y%m%d")

    path =  BASE_LOG_PATH + 'api_%s.log'%(now)

    #没有文件夹就创建
    check_dir = os.path.dirname(path)
    isExists = os.path.exists(check_dir)
    if not isExists:
        os.makedirs(check_dir)

    now_time = time.strftime("%Y-%m-%d %H:%M:%S")
    msg =  now_time + ' [%s] '%(Type) + '%s'%msg
    msg += '\n'
    with open(path,'a') as L:
        L.write(msg)

def to_md5(sign_str):
    return hashlib.md5(sign_str).hexdigest()

def get_server_list(request):
    #参数
    dicts = request.POST
    ts = dicts.get("ts", "")
    sign = dicts.get("sign","")
    print ts
    result = {"flag":"false","msg":"","serverList":[]}
    if not all([ts, sign]):
        result["msg"] = "params imcomplete"
        return HttpResponse(json.dumps(result))

    #时间校验
    time_out=60
    if not ts:
        result["msg"]="not time_stamp"
        return HttpResponse(json.dumps(result))
    now = time.time()
    if now-float(ts)>time_out:
        result["msg"]="stale date"
        return HttpResponse(json.dumps(result))

    #sign校验
    game_key = "b27d9389deb25d48"

    # tss= ts.encode("utf-8").decode("gbk")

    if sign != to_md5(ts+game_key):
        result["msg"]="sign error"
        return HttpResponse(json.dumps(result))

    # 服务器列表
    try:
        models = Server.objects.all()
    except Exception as e:
        Log("error", "%get_server_list-%s-error" % (e))
        result["msg"] = "connection error"
        return HttpResponse(json.dumps(result))
    else:
        server_list = []
        for model in models:
            server_dic = {}
            server_dic["serverName"]=model.name
            server_dic["serverId"] = model.id
            server_list.append(server_dic)
        result["flag"]="true"
        result["serverList"]=server_list
    return HttpResponse(json.dumps(result))

def get_player(request):
    ###获取个人
    #请求参数
    dict = request.POST
    ts = dict.get("ts", "")
    sign = dict.get("sign", "")
    server_id =dict.get("serverId","")
    game_account= dict.get("gameUniId","")

    result = {"flag": "false", "msg": "", "roleList": []}

    if not all([ts, sign, server_id, game_account]):
        result["msg"] = "params imcomplete"
        return HttpResponse(json.dumps(result))

    # 时间校验
    time_out = 60
    if not ts:
        result["msg"] = "not time_stamp"
        return HttpResponse(json.dumps(result))
    now = time.time()
    # if now - float(ts) > time_out:
    #     result["msg"] = "stale date"
    #     return HttpResponse(json.dumps(result))

    # sign校验
    game_key = "b27d9389deb25d48"
    if sign != to_md5(server_id+game_account+ts+game_key):
        result["msg"] = "sign error"
        return HttpResponse(json.dumps(result))

    #获取角色列表
    try:
        conn = getConn(int(server_id))

        # sql ="select player_id,player_name from player_{0} where link_key='{1}'".format(server_id,game_account)
        sql = "select pp.player_id as player_id,pp.player_name as player_name,cc.log_level as log_level from player_{0} as pp left JOIN  log_player_level as cc on pp.player_id=cc.log_user WHERE pp.link_key='{1}'".format(server_id, game_account)
        Log("info","%s-get_player-%s=======>sql"%(game_account,sql))
        cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cur.execute(sql)

        users = cur.fetchall()
        role_list=[]
        print users
        if not users:
            result["msg"] = "content empty"
            return HttpResponse(json.dumps(result))
        for user in users:
            role_dic={}
            role_dic["roleUniId"]=user.get("player_id","")
            role_dic["roleName"]=user.get("player_name","")
            role_dic["roleLevel"] = user.get("log_level","")     ############
            role_list.append(role_dic)
        result["flag"]="true"
        result["roleList"]=role_list
        cur.close()
    except Exception as e:
        print e
        Log("error","%s-get_player-%s-error"%(game_account,e))
        result["msg"]="connection error"
        return HttpResponse(json.dumps(result))
    return HttpResponse(json.dumps(result))

def goods_permission(request):
    # 请求参数
    dict = request.POST
    ts = dict.get("ts","")
    sign = dict.get("sign","")
    server_id = dict.get("serverId","")
    game_account = dict.get("gameUniId","")
    roleUniId = dict.get("roleUniId","")
    productId = dict.get("productId","")

    result = {"flag": "false", "msg": ""}
    if not all([ts, sign, server_id, game_account,roleUniId,productId]):
        result["msg"] = "params imcomplete"
        return HttpResponse(json.dumps(result))

    # 时间校验
    time_out = 60
    if not ts:
        result["msg"] = "not time_stamp"
        return HttpResponse(json.dumps(result))
    now = time.time()
    if now - float(ts) > time_out:
        result["msg"] = "stale date"
        return HttpResponse(json.dumps(result))

    # sign校验
    game_key = "b27d9389deb25d48"
    if sign != to_md5(server_id + game_account + roleUniId + productId + ts + game_key):
        result["msg"] = "sign error"
        return HttpResponse(json.dumps(result))

    #查询角色是否存在
    conn = getConn(int(server_id))
    sql = "select player_name from player_{0} where player_id='{1}'".format(server_id, roleUniId)
    cur = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cur.execute(sql)
    users = cur.fetchone()
    if not users:
        result["msg"] = "Without the role"
        return HttpResponse(json.dumps(result))

    # 查询产品
    product_dict = DictDefine.get_dict_for_key("tw_online_charge")
    product_name = product_dict.get(productId, "")
    print unicode(product_name)
    if not product_name:
        result["msg"] = "product is not exit"
        return HttpResponse(json.dumps(result))
    if unicode(product_name) != u"周卡" and  unicode(product_name) != u"月卡":
        result["flag"] = "true"
        return HttpResponse(json.dumps(result))

    # 获取周卡，月卡状态
    if unicode(product_name) == u"周卡":
        product_name = "weekCard"
    elif unicode(product_name) == u"月卡":
        product_name = "monthCard"
    try:
        conn = getConn(int(server_id),logic_db=True)
        sql = "select `data` from operationalplayer where playerId=%s AND actType=2 "%(roleUniId)
        print "===>",sql
        cur = conn.cursor()
        cur.execute(sql)
        data = cur.fetchone()
        print data
        if not data:
            result["flag"] = "true"
            return HttpResponse(json.dumps(result))

        # data:{"weekCard":{"status":1,"time":1506283200},"monthCard":{"status":2,"time":1508443200}}
        data = json.loads(data[0])
        card_dict = data.get(product_name,"")
        if not card_dict:
            result["flag"] = "true"
            return HttpResponse(json.dumps(result))
        card_time = card_dict.get("time","")
        if now-card_time>0:
            result["flag"] = "true"
            return HttpResponse(json.dumps(result))
        else:
            result["msg"] = "The card is not expired"
            return HttpResponse(json.dumps(result))
    except Exception as e:
        print e
        Log("error", "%s-goods_permission-%s-error" % (roleUniId, e))
        result["msg"] = "connection error"
        return HttpResponse(json.dumps(result))

def get_product_list(request):
    #####'''请求商品信息'''
    #参数
    dicts = request.POST
    ts = dicts.get("ts", "")
    sign = dicts.get("sign","")

    result = {"flag":"false","msg":"","productList":[]}
    if not all([ts, sign]):
        result["msg"] = "params imcomplete"
        return HttpResponse(json.dumps(result))

    #时间校验
    time_out=60
    if not ts:
        result["msg"]="not time_stamp"
        return HttpResponse(json.dumps(result))
    now = time.time()
    if now-float(ts)>time_out:
        result["msg"]="stale date"
        return HttpResponse(json.dumps(result))

    #sign校验
    game_key = "b27d9389deb25d48"

    if sign != to_md5(ts+game_key):
        result["msg"]="sign error"
        return HttpResponse(json.dumps(result))

    # 商品列表
    try:
        name_dict = DictDefine.get_dict_for_key("tw_online_charge")

        money_dict = DictDefine.get_dict_for_key("charge_id_money")
        pay_type_dict = DictDefine.get_dict_for_key("online_pay_type")
    except Exception as e:
        Log("error", "get_product_list-%s-error" %(e))
        result["msg"] = "connection error"
        return HttpResponse(json.dumps(result))
    else:
        productList = []
        for key,value in name_dict.items():
            product_dic = {}
            product_dic["productName"]= value
            product_dic["productId"] = key
            product_dic["productAmount"] = money_dict.get(key,"")
            product_dic["productPayType"] = pay_type_dict.get(key,"")
            productList.append(product_dic)
        result["flag"]="true"
        result["productList"]= productList
    return HttpResponse(json.dumps(result))

def operation(request):
    dict = request.REQUEST
    Log("info",dict)
    player_id = dict.get("player_id","0")
    type= dict.get("type","")
    scene_id = dict.get("scene_id","")
    account = dict.get("account","")
    content=dict.get("content","")
    app_name = dict.get("app_name","")
    bundle_id = dict.get("bundle_id","")
    decive_id = dict.get("device_id","")
    channel_key = dict.get("channel_key","")
    extra = dict.get("extra","")
    result={}

    try:
        model = Player_operation()
        model.player_id=int(player_id)
        model.type = type
        model.scene_id=scene_id
        model.account= account
        model.content = content
        model.app_name = app_name
        model.bundle_id=bundle_id
        model.device_id = decive_id
        model.channel_key = channel_key
        model.extra = extra
        model.save()
    except Exception as e:
        print e
        Log("error",e)
        result["msg"]="connect error"
        return HttpResponse(json.dumps(result))
    result["msg"]="ok"
    return HttpResponse(json.dumps(result))



CONVERT_TYPE={'Activation':1,'Zip':2,'ShowSdk':3,'LoginSdk':4,'LoginServer':5,
'LoginPanel':6,'SelectServer':7,'EnterLgoin':8,'CreatePlayer':9,'SelectProf':10,
'SelectName':11,'EnterCreatePlayer':12,'CreateSuccess':13,'EnterScene':14,'SubmitTask':15}

def convert(request):
    '''记录客户端发送的打点数据'''

    dict = request.REQUEST
    print 'hihihihihihihihi',dict
    Log("info", "convert=%s"%dict)
    type = dict.get("login_type","")
    player_id = dict.get("player_id",0)
    account = dict.get("account","")
    ieme = dict.get("ieme","")

    if type.isalpha():
        type = CONVERT_TYPE.get(type)

    result = {}
    if not type:
        result["msg"] = "no type error"
        return HttpResponse(json.dumps(result))

    try:
        model = Player_convert()
        model.type = type
        model.player_id = int(player_id)
        model.account=account
        model.ieme = ieme
        model.save()
    except Exception as e:
        print e
        Log("error", e)
        result["msg"] = "connect error"
        return HttpResponse(json.dumps(result))
    result["msg"] = "ok"
    return HttpResponse(json.dumps(result))





