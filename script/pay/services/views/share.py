#! /usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from models.center import Server,Channel,Auth
from models.log import Log
from models.pay import PayAction,PayChannel
import datetime,time
import json,urllib
import MySQLdb
from django.db import connection
from util.http import http_post
from django.utils.http import urlquote
import random
from util import trace_msg

SHARE_ADDRESS = 'http://service.yhzbonline.com/'

#分享图片id的连接
_IMG_ID_LIST = ['001.jpg','002.jpg','003.jpg','004.jpg','005.jpg','006.jpg']
SHARE_LINK = {
              '0100020010':'http://t.cn/zjfSbJV',
}

DEFAULT_SHARE_LINK = 'http://www.7725.com/html/cskgalaxy/'



test_msg = '''galaxy share'''
share_type_list = ['facebook','msn']


class ShareType(object):
    def __init__(self,request,share_model):
        self.share_model = share_model
        http_protocol = 'https' if request.is_secure() else 'http'
        self.auth_url = '%s://%s/client/share/auth/%s' % (http_protocol,request.get_host(),share_model.id)
        self.link_url = '%s://%s/client/share/link/%s' % (http_protocol,request.get_host(),share_model.id)
    
    def get_auth_url(self):pass
    
    def get_share_result(self,access_token):pass


class FacebookShare(ShareType):
    app_id = '790335917717012'
    
    def get_auth_url(self):
        return 'https://graph.facebook.com/oauth/authorize?&scope=publish_stream&client_id=%s&redirect_uri=%s&display=page' % (self.app_id,self.auth_url)
    
    def get_share_result(self,access_token):
        import facebook as FaceBook
        pic_url = self.share_model.f3
        msg = self.share_model.f6
        graph = FaceBook.GraphAPI(access_token,5)
        post_args = {'message':msg.encode('utf-8'),
                     'picture':pic_url,
                     'link':self.link_url
                     }
        result_json = graph.request('me/feed',post_args=post_args)
        print result_json
        return self.link_url
    
def get_share_type_cls(share_type_str):
    if share_type_str == 'facebook':
        return FacebookShare

def auth(request,shard_id=0):
    '''认证完成访问页面
    '''
    http_protocol = 'https' if request.is_secure() else 'http'
    access_token = request.REQUEST.get('code','')
    try:
        if shard_id and access_token:
                Log._meta.db_table = 'log_share'
                share_model = Log.objects.using('read').get(id=shard_id)
                share_type = share_model.f4
                share_type_cls = get_share_type_cls(share_type)
                share_type_obj = share_type_cls(request,share_model)
                
                return share_type_obj.get_share_result(access_token)
    except:
        print trace_msg()
    return HttpResponse('error')




def page(request,server_id=0,player_id=0,template='share/page.html'):
    '''客户端分享页面
    '''
    channel_key = request.REQUEST.get('qd','test')
    msg = request.REQUEST.get('msg',test_msg).replace('\n','')
    http_protocol = 'https' if request.is_secure() else 'http'
    title = request.REQUEST.get('title','')
    off_share_type = request.REQUEST.get('type','')
    off_share_type_list = [ x for x in off_share_type.split(',') if x]
    if server_id and player_id and channel_key and msg :
        the_img_id = random.choice(_IMG_ID_LIST)
        pic_url = '%s://%s/static/img/%s' % (http_protocol,request.get_host(),the_img_id)
        share_log = write_share_log(server_id,player_id,channel_key,msg,title,pic_url)
        share_link = '%s://%s/client/share/link/%s' % (http_protocol,request.get_host(),share_log.id)
        return render_to_response(template,locals())
    else:
        return HttpResponse('params error!')


#def page(request,server_id=0,player_id=0,template='share/page.html'):
#    '''客户端分享页面
#    '''
#    channel_key = request.REQUEST.get('qd','test')
#    msg = request.REQUEST.get('msg',test_msg).replace('\n','')
#    http_protocol = 'https' if request.is_secure() else 'http'
#    title = request.REQUEST.get('title','')
#    share_type = request.REQUEST.get('type','')
#    if share_type_list:
#        template = 'share/%s.html' % share_type
#        if server_id and player_id and channel_key and msg :
#            the_img = random.choice(_IMG_ID_LIST)
#            pic_url = '%s://%s/static/img/%s' % (http_protocol,request.get_host(),the_img)
#            share_log = write_share_log(server_id,player_id,channel_key,msg,title,pic_url,share_type)
#            share_type_cls = get_share_type_cls(share_type)
#            get_share_type_obj = share_type_cls(request,share_log)
#            #跳到认证接口
#            auth_url = get_share_type_obj.get_auth_url()
#            share_link = get_share_type_obj.link_url
#        return render_to_response(template,locals())
#    else:
#        return HttpResponse('params error!')

def share_link(request,shard_id=0,template='share/link.html'):
    '''分享连接 只要有人点击就保存
    '''
    if shard_id and str(shard_id).isdigit():
        Log._meta.db_table = 'log_share'
        log = Log.objects.using('read').get(id=shard_id)
        channel_key = log.f2
        link = SHARE_LINK.get(channel_key, DEFAULT_SHARE_LINK)
        #if request.REQUEST.get('post_id',''):
        log.log_result += 1         #访问连接的次数加1
        log.data = int(time.time()) #最新时间戳
        log.save(using='write')
        description = log.f6
        title = log.f1
        pic_url = log.f3
        return render_to_response(template,locals())
    return HttpResponse('ShareId error!')

def result(request,server_id=0,player_id=0):
    '''分享结果
    '''
    code = 0
    if server_id and player_id:
        try:
            Log._meta.db_table = 'log_share'
            log = Log.objects.using('read').get(log_user=player_id,log_server=server_id)
            code = log.log_result
        except:
            pass
    return HttpResponse(code)


def md5(sign_str):
    import hashlib
    signStr=hashlib.md5() 
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()

def write_share_log(server_id,player_id,channel_key,msg,title='',pic_url='',share_type=''):
    Log._meta.db_table = 'log_share'
    log,created = Log.objects.get_or_create(log_server=server_id,log_user=player_id)
    log.log_type = 28
    log.log_channel = 0
    log.log_data = 0
    if msg and pic_url: #第一次创建
        log.f6 = msg #分享内容
        log.f2 = channel_key
        log.f1 = title
        log.f3 = pic_url
        log.f4 = share_type
        log.log_time = datetime.datetime.now() #分享时间
        log.save(using='write')
    return log

    
def http_post(the_url,post_data=None):
    import urllib2

    proxy=urllib2.ProxyHandler({'https': 'http://10.172.48.92:3300','http': 'http://10.172.48.92:3300'})
    opener=urllib2.build_opener(proxy)
    urllib2.install_opener(opener)
    result = ''
    try:
        if post_data==None:
            result = urllib2.urlopen(the_url).read()
        else:
            req = urllib2.Request(the_url, post_data)
            result = urllib2.urlopen(req).read()
    except Exception,e:
        print('http_post has error',e)
    return result    