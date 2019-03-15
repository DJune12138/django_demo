#encoding:utf-8

import hashlib, json

def md5(my_sign):
    return  hashlib.new('md5',my_sign).hexdigest()

def confirm_a37wan_get_link_id(request):
    return ''

def confirm_a37wan(request,pay_channel={}):
    #print request.REQUEST

    pid = request.REQUEST.get('pid','')
    gid = request.REQUEST.get('gid','')
    time = request.REQUEST.get('time','')
    sign = request.REQUEST.get('sign','')
    oid = request.REQUEST.get('oid','')
    doid = request.REQUEST.get('doid','')
    dsid = request.REQUEST.get('dsid','')
    dext = request.REQUEST.get('dext','')
    drid = request.REQUEST.get('drid','')
    drname = request.REQUEST.get('drname','')
    drlevel = request.REQUEST.get('drlevel','')
    uid = request.REQUEST.get('uid','')
    money = request.REQUEST.get('money','')
    coin = request.REQUEST.get('coin','')
    remark = request.REQUEST.get('remark','')
    paid = request.REQUEST.get('paid','')
    app_key = pay_channel.get_config_value('app_key','SaM+5zP1bFIdpqCs2UO9oAVvZ;KW8DxQ')

    server_id = player_id = 0
    order_id = remark = ""
    result_msg = json.dumps({"state":0,"data":"","msg":"signerror"})
    amount = 0
    post_amount = 0
    link_id = ''
    try:
        sign_str = '%s'*8 %(time,app_key,oid,doid,dsid,uid,money,coin)
        print sign_str
        my_sign = md5(sign_str)
        print sign,my_sign
        if sign == my_sign:
            amount = money
            server_id = int(dsid)
            player_id = int(drid)
            order_id = oid
            link_id = dext
            remark = pid
            result_msg = json.dumps({"state":1,"data":"","msg":"成功"})

    except Exception, e:
        import traceback
        traceback.print_exc()

    _r = {'server_id':server_id,'player_id':player_id,'order_id':order_id,'amount':amount,'remark':remark,'result_msg':result_msg,'link_id':link_id}
    print _r
    return _r
