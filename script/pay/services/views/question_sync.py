# -*- coding: utf-8 -*-
#同步客服问题到中央服

import os,sys

if __name__=='__main__':
    import os
    _op = os.path.dirname
    _file = os.path.abspath(__file__)
    root_path = _op(_op(_op(_file)))
    sys.path.insert(0,root_path)
    print root_path
    os.chdir(root_path)
    os.environ['DJANGO_SETTINGS_MODULE'] ='services.settings'




import json
import traceback
import httplib
import urllib
import hashlib
import time,datetime
from django.http import HttpResponse
from django.core.serializers import serialize,deserialize
from django.db.models import Q
from views import getConn
from models.center import Question, User, SafeQuestion,get_time_str
from models.channel import Channel
from models.server import Server,Group
from services.views.game.base import GMProtocol


import functools
import threading

import httplib
import traceback
import socket


class HttpTimeOut(Exception):pass

def http_post(url, data=None, data_type = 'x-www-form-urlencoded',user_agent='', timeout_param=5):
    res = None
    urlInfo = httplib.urlsplit(url)
    uri = '%s?%s' % (urlInfo.path,urlInfo.query)
    
    if url.find('https://')>-1:
        conn = httplib.HTTPSConnection(urlInfo.netloc,timeout=timeout_param)
    else:
        conn = httplib.HTTPConnection(urlInfo.netloc,timeout=timeout_param)
#    if True:
    try:
        conn.connect()
        
        if data:
            if isinstance(data,unicode):
                data = data.encode('utf-8')
            conn.putrequest("POST", uri)
            conn.putheader("Content-Length", len(data))
            conn.putheader("Content-Type", "application/%s"%data_type)
            if user_agent!='':
                conn.putheader("User-Agent",user_agent)
        else:
            conn.putrequest("GET", uri)
            conn.putheader("Content-Length", 0)
            conn.putheader("Content-Type", "application/x-www-form-urlencoded")
            
        conn.putheader("Connection", "close")
        conn.endheaders()

        if data:
            conn.send(data)

        response = conn.getresponse()
        if response:
            res = response.read()
            response.close()

        print '-'*20,response.status,res
        return (response.status,res)
    
    except socket.timeout:
        raise HttpTimeOut('Connect %s time out' % url)
    except Exception, ex:
        raise ex
    
    conn.close()
    
    
    
def md5(s):
    return hashlib.new('md5',s).hexdigest()

DATETIMEFORMAT = '%Y-%m-%d %H:%M:%S'
def str_to_datetime(datetime_str):
    return datetime.datetime.strptime(datetime_str,DATETIMEFORMAT)

def datetime_to_timestamp(datetime_or_str):
    '''
    @datetime或者日期时间字符串转时间戳
    '''
    if isinstance(datetime_or_str,basestring):
        datetime_or_str = str_to_datetime(datetime_or_str)
    return int(time.mktime(datetime_or_str.timetuple()))

def get_player_name(server_id,player_id):
    player_id = int(player_id)
    server_id = player_id >> 20
    try:
        conn = getConn(server_id)
        sql = 'select player_name FROM player_%d where player_id=%d' % (server_id,player_id)
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchone()
        if result:
            return result[0]
    except:
        traceback.print_exc()
        return ''
    
def get_server_name(server_id):
    try:
        return Server.objects.get(id=server_id).name
    except:
        return server_id
    
def get_channel_name(channel_id):
    try:
        return Channel.objects.get(id=channel_id).name
    except:
        return channel_id

    
def get_question_info(qm):
    network_type = phone_type = ''
    info = qm.info
    if '|' in info:
        info_sp = info.split('|')
        if len(info_sp)>=2:
            network_type,phone_type = info_sp[0],'|'.join(info_sp[1:])
    return network_type,phone_type

class QuestionSync(dict):
    from settings import QUESTION_SYNC_ADDRESS
    from settings import QUESTION_APP_ID
    from settings import QUESTION_APP_KEY

    SYNC_ADDRESS = QUESTION_SYNC_ADDRESS
    APP_ID = QUESTION_APP_ID
    APP_KEY = QUESTION_APP_KEY
    
    def __init__(self,qm):
        self.qm = qm
        self.now = int(time.time())
        
    @classmethod
    def make_sign(cls,data,timestamp):
        sign_str = ''
        timestamp = str(timestamp)
        if not isinstance(data,(list,tuple)):
            data = [data]
        sign_str = ''
        
        for d in data:
            if not isinstance(d,dict):
                continue
            for k in sorted(d.keys()):
                v = d.get(k,'')
                if isinstance(v,unicode):
                    v = v.encode('utf-8')
                if isinstance(k,unicode):
                    k = str(k)
                if type(v) == int or type(v) == long:
                    sign_str += '&%s=%s' % (k,v)
                else:
                    sign_str += '&%s=%s'%(k,v if v else '')
        sign_str = 'app_id=%s&t=%s&%s%s' % (cls.APP_ID,timestamp,cls.APP_KEY,sign_str)
        print sign_str
        return md5(sign_str)
    
    def get_question_dict(self):
        qm = self.qm
        if qm.score < 0:
            qm.score = 0
        network_type,phone_type = get_question_info(qm)
        data = {
             "answer_name":qm.reply_user,
             "vip":qm.post_user_id,
             "create_time":qm.post_time_str(),
             "id":qm.id,
             "player_name":get_player_name(qm.server_id,qm.post_user),
             "server_name":get_server_name(qm.server_id),
             "question":qm.question,
             "channel_name":get_channel_name(qm.channel_id),
             "score":qm.score,
             "question_type":qm.question_type,
             "answer":qm.answer,
             "player_id":qm.post_user,
             }
        if network_type and phone_type:
            data["phone_type"] = phone_type
            data["network_type"] = network_type

        if qm.check_time:
            data["read_time"] = get_time_str(qm.check_time)
            
        return data
    
    def post(self,time_out=10):
        data = self.get_question_dict()

        json_data = json.dumps([data])
        post_address = '%s?app_id=%s&t=%s&sign=%s' % (self.SYNC_ADDRESS,self.APP_ID,self.now,self.make_sign(data,self.now))
        
        print post_address
        try:
            status,result = http_post(post_address,
                      data=json_data,
                      data_type='json',
                      timeout_param=time_out
            )
            print result
            result = json.loads(result)
        except:
            result = {}
        return status == 200 and result.get('result','') == 'succeed'

    def get_center_question(self):
        '''获取中央单服的问题
        '''
        try:
            #params_str = 'app_id=%s&id=%s&t=%s' % (self.APP_ID,self.qm.id,self.now) #内网测试
            params_str = 'app_id=%s&id=%s&t=%s' % (self.APP_ID,self.qm.id,datetime_to_timestamp(self.qm.post_time))
            sign = md5('%s&%s' % (params_str,self.APP_KEY))
            _get_address = '%s?%s&sign=%s' % (self.SYNC_ADDRESS,params_str,sign)
            print _get_address
            status,result = http_post(_get_address,
                                      timeout_param=10
            )
            return json.loads(result)['result']
        except:
            traceback.print_exc()
            return {}
    
    def update(self):
        data_list = self.get_center_question()
        self.__class__.sync_loacl(data_list)

    @staticmethod
    def sync_loacl(data_list):
        '''同步本地问题
        '''
        for _d in data_list:
            qid = int(_d.get('id','') or 0)
            #print _d
            if _d and qid:
                try :
                    qustion_model = Question.objects.get(id=qid)
                    qustion_model.reply_user = _d.get('answer_name','') or qustion_model.reply_user
                    if qustion_model.reply_user and not qustion_model.status:
                        qustion_model.status = 1
                    qustion_model.question_type = _d.get('question_type',qustion_model.question_type)
                    qustion_model.answer = _d.get('answer','') or qustion_model.answer
                    answer_time = _d.get('answer_time','') 
                    if answer_time:
                        qustion_model.reply_time = str_to_datetime(answer_time)
                    qustion_model.save()
                    tell_question_status_to_game_server(qustion_model)
                except:
                    traceback.print_exc()    
    
def question_sync_interface(request):
    '''同步中央服接口
    '''
    _r = {"result":"failed","msg":""}
    
    sign = request.GET.get('sign','')
    t = request.GET.get('t','')
    
    if request.method == 'POST':
        json_data = request.body
        try:
            data_list = json.loads(json_data)
            my_sign = QuestionSync.make_sign(data_list,t)
            if sign == my_sign:
                QuestionSync.sync_loacl(data_list)
                _r["result"] = 'succeed'
            else:
                _r["msg"] = "sign error"
        except Exception,e:
            traceback.print_exc()
            _r['msg'] = str(e)
    elif request.method == 'GET':# 这里是获取未接单的数据
        my_sign = QuestionSync.make_sign({},t)

        print '-' * 40
        print (my_sign,sign)
        if my_sign == sign:
            question_list = []
            server_ids = get_kefuserver_id_list()
            base_query = Q(status__lt=1) & Q(server_id__in=server_ids) & Q(Q(reply_user__isnull=True)|Q(reply_user='')) #属于游爱的没被接的单
            base_query = base_query & Q(post_time__gte=datetime.date(2014, 9, 25))    #限定从今天开始接单
            timestamp = int(t)
            now_datetime = datetime.datetime.fromtimestamp(timestamp)
            one_week_ago = now_datetime  + datetime.timedelta(days=-7)
            base_query = base_query & Q(post_time__gte=one_week_ago) #一星期前的数据
            not_order_query = base_query #接了单未回复的都能获取
            #not_order_query = Q(Q(order_user__isnull=True)|(Q(order_user=''))) & base_query
            _q_list = Question.objects.filter(not_order_query).all().order_by('post_time')
            
            for q in _q_list:
                qs = QuestionSync(q)
                q_data = qs.get_question_dict()
                question_list.append(q_data)
            _r = question_list
            print _r
    return HttpResponse(json.dumps(_r,ensure_ascii=False))

def get_kefuserver_id_list():
    server_ids = []
    groups = Group.objects.filter(group_key='kefuserver').prefetch_related('server')
    if groups:
        group = groups[0]
        server_ids = group.server.all().values_list('id',flat=True)
    return server_ids

def filter_question_for_server(server_id):
    try:
        server_ids = get_kefuserver_id_list()
        return server_id in server_ids or not server_ids
    except:
        traceback.print_exc()
        return True

def async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        my_thread.setDaemon(True)
        my_thread.start()
    return wrapper

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

exclude_channel_ids =  []

@async
def post_question_to_center(question_model,time_out=10):
    if filter_question_for_server(question_model.server_id) and question_model.channel_id not in exclude_channel_ids:

        qs = QuestionSync(question_model)
        result = qs.post(time_out)
        if not result:
            for i in xrange(5):
                result = qs.post(time_out)
                if result:
                    break
                time.sleep(i)
                
if __name__=='__main__':
    pass
    # for i  in range(4,8):
    # qm = Question.objects.all().order_by('-id')[i]
    # qm = Question.objects.filter(post_user=1000232)[1]
    # print qm.id
    # qs = QuestionSync(qm)
    # print qs.post()
    # print qs.sync_data()
    # print qs.get_data()
    
