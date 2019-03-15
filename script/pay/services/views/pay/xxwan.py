# -*- coding: utf-8 -*-
# xxwan

import urllib,hashlib
import traceback

def confirm_xxwan_get_link_id(request):
    return urllib.unquote_plus(request.REQUEST.get('h',''))

def urldecode(rq,key):
    return urllib.unquote_plus(rq.get(key,'').encode('utf-8'))

def md5(sign_str):
    return  hashlib.new('md5',sign_str).hexdigest()

def confirm_xxwan(request,pay_channel):
    
    print request.REQUEST
    rq = request.REQUEST
    userId = urldecode(rq,'a')          #userId
    userAccount = urldecode(rq,'b')     #userAccount
    serverId = urldecode(rq,'c')        #serverId
    roleId = urldecode(rq,'d')          #roleId
    roleName = urldecode(rq,'e')        #roleName
    order_id = urldecode(rq,'f')        #orderId
    order_status = urldecode(rq,'g')    #orderStatus
    pay_type = urldecode(rq,'h')        # platformId 平台类型定义(platformId) 
    amount = urldecode(rq,'i')          #amount
    remark = urldecode(rq,'j')          #remark
    callbackInfo = urldecode(rq,'k')    #callBackInfo
    payTime = urldecode(rq,'l')         #payTime
    paySUTime = urldecode(rq,'m')       #paySUTime
    callBackUrl = urldecode(rq,'n')     #paySUTime
    
    sign = urldecode(rq,'o')            #sign  不参与签名
    clientType  = urldecode(rq,'p')     #客户端类型 0-android 1-ios(clientType)  不参与签名
    
    result_msg = 'error'
    the_server_id = pay_amount = 0
    open_id = player_id = ''
    try:
        app_key = pay_channel.get_config_value('app_key','5845686f4d27f836487ae04a1e14d15e').encode('utf-8')
        user_type = pay_channel.get_config_value('user_type',1)

        sign_str = 'a=%s&b=%s&c=%s&d=%s&e=%s&f=%s&g=%s&h=%s&i=%s&j=%s&k=%s&l=%s&m=%s&n=%s&appkey=%s' %\
        (userId,userAccount,serverId,roleId,roleName,order_id,order_status,pay_type,amount,remark,callbackInfo,payTime,paySUTime,callBackUrl,app_key)
        my_sign = md5(sign_str)
        
        print (sign_str,my_sign,app_key)
        if sign==my_sign:
            if int(order_status) == 1:
                the_server_id = int(serverId)
                player_id = int(roleId)
                pay_amount = float(amount) / 100
                result_msg =  'success'
                remark = '%s_%s' % (remark,platform_map.get(str(pay_type),''))
        else:
            result_msg = 'errorSign'
    except Exception,e:
        traceback.print_exc()
        print('confirm xxwan has error',e)
        
    return {'server_id':the_server_id,'player_id':player_id,'order_id':order_id,'amount':pay_amount,'remark':remark,'result_msg':result_msg}        

        
        
platform_map =\
{
    "1": "360",
    "2": "91",
    "3": "指点",
    "4": "百度多酷",
    "5": "UC",
    "6": "小米",
    "7": "豌豆荚",
    "8": "OPPO",
    "9": "当乐",
    "10": "安智",
    "11": "3K",
    "12": "49",
    "13": "步步高",
    "14": "应用汇",
    "15": "联想",
    "16": "有信",
    "17": "点点乐",
    "18": "C1",
    "19": "37wan",
    "20": "华为",
    "21": "拇指玩",
    "22": "3g",
    "23": "阿里",
    "24": "迅雷",
    "25": "搜狗",
    "26": "电信爱游戏",
    "27": "微讯",
    "28": "立火",
    "29": "酷派",
    "30": "碰碰(",
    "31": "PPS",
    "32": "多玩",
    "33": "联通",
    "34": "小鬼",
    "35": "金立",
    "36": "益玩",
    "37": "有米",
    "38": "泡椒",
    "39": "机锋",
    "40": "琵琶",
    "41": "手游吧",
    "42": "HTC",
    "43": "酷我",
    "44": "朗宇",
    "45": "畅梦",
    "46": "欧朋",
    "47": "水煮科技",
    "48": "悠悠村",
    "49": "平安",
    "50": "新浪",
    "51": "海马",
    "52": "移动",
    "53": "酷狗",
    "54": "卓然",
    "55": "蜗牛",
    "56": "万普",
    "57": "应用宝",
    "58": "Pp",
    "59": "同步推",
    "60": "快用",
    "61": "爱思助手",
    "62": "itools",
    "63": "Xy",
    "101": "梦想手游"
}
        
        