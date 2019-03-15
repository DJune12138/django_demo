#coding=utf-8
# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse
from models import Card,CardBatch,CardPrize
import json
import random
import datetime
from settings import DATABASES
import MySQLdb
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

def prize_view(request, model_id, code):
    msg = ''
    model = None
    try:
        model_id = int(model_id)
        model_id = model_id
    except Exception, e:
        print 'model_id error', e
    try:
        if msg == '':
            model = CardPrize.objects.using('card').filter(id = model_id, code = code)[0]
            if model:
                if model.status == 1:
                    now = datetime.datetime.now()
                    if model.start_time < now and model.end_time > now:
                        pass
                    else:
                        model = None
                else:
                    model = None
            else:
                msg = 'model unknow'
    except Exception, e:
        print 'error', e
        msg = 'error'
    parg = {}
    parg['model'] = model
    parg['code'] = code
    parg['key'] = model_id
    return render_to_response('prize_view.html', parg)

def get_rand(proArr):
    result = '' 
 
    #概率数组的总概率精度 
    proSum = 0 
    for k, v in proArr.items():
        proSum += v
    #概率数组循环 
    for k, v in proArr.items():
        randNum = random.randint(1, proSum)
        if randNum <= v:
            result = k
            break
        else:
            proSum -= v 
    proArr = None
    return result
        
def prize_get(request, model_id, code):
    is_ajax = request.GET.get('is_ajax', False)
    msg = ''
    result_code = 1
    model = None
    referer = request.META.get('HTTP_REFERER','')
    host_name = request.META['HTTP_HOST']
    if str(referer).find(host_name) == -1:
        msg = '非法请求,已被记录！'
        print 'prize_get illegal request'
    if msg == '':
        try:
            model_id = int(model_id)
        except:
            msg = '请不要重复领卡！'
        try:
            if msg == '':
                model = CardPrize.objects.using('card').filter(id = model_id, code = code)[0]
                if model:
                    if model.status == 1:
                        now = datetime.datetime.now()
                        if model.start_time < now and model.end_time > now:
                            config = json.loads(model.config)
                            data = {}
                            for k, v in config.items():
                                data[int(k)] = int(v['v'])
                             
                            rid = get_rand(data) #根据概率获取礼包卡key
                            #prize = config[str(rid)]['prize']#中奖内容
                            key = int(rid)
                            the_card_batch = CardBatch.objects.using('card').filter(key = key)[0]
                            if the_card_batch:
                                current_unixtime = datetime.datetime.now()
                                if the_card_batch.status == 1 and current_unixtime > the_card_batch.start_time and current_unixtime < the_card_batch.end_time:
                                    the_conn_str = DATABASES['card']
                                    the_conn = MySQLdb.connect(host=the_conn_str['HOST'],user=the_conn_str['USER'],passwd=the_conn_str['PASSWORD'], port=int(the_conn_str['PORT']), db=the_conn_str['NAME'],charset='utf8')
                                    the_conn.autocommit(1)
                                    cursor = None
                                    try:
                                        sql = "LOCK TABLE card_%s WRITE" % key
                                        cursor = the_conn.cursor()
                                        sql = "SELECT `number`,`id` FROM card_%s WHERE `status` = 0 AND `batch_id` = %d " % (key, the_card_batch.id)
                                        cursor.execute(sql)
                                        data = cursor.fetchone()
                                        msg = u'卡号：%s'%data[0]
                                        sql = "UPDATE card_%s SET `status` = 1 WHERE `id` = %d " % (key, int(data[1]))
                                        cursor.execute(sql)
                                    except Exception, e:
                                        print e
                                        pass
                                    finally:
                                        if None != cursor:
                                            try:
                                                cursor.execute('UNLOCK TABLES')
                                                result_code = 0
                                            except Exception, e:
                                                print e
                                                pass   
                                else:
                                    '领卡人数较多，请稍候再试！'      
                            else:
                                '领卡人数较多，请稍候再试！'                             
                        else:
                            msg = '卡号已经全部领取完毕，谢谢！'                                    
                    else:
                        msg = '卡号已经全部领取完毕，谢谢！'
                else:
                    msg = '卡号已经全部领取完毕，谢谢！'
        except Exception, e:
            print 'error',e
            msg = '领卡人数较多，请重新领取！'
    parg = {}
    parg['model'] = model
    parg['result_code'] = result_code
    parg['msg'] = msg
    if is_ajax:
        response = HttpResponse(json.dumps({'msg':msg, 'result_code': result_code}))
    else:
        response = render_to_response('prize_show.html',{"result_code": result_code, "msg":msg})
    return response    
