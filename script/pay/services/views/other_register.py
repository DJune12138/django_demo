# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, HttpResponse
from django.db.models import Q
from models.center import Question, User, Channel, SafeQuestion
from models.log import Log
from views import md5,hash256
import time, datetime, json, hashlib, base64, re
from util.http import http_post
import os
import traceback
import json
from xml.dom import minidom

def ip(request):
    return HttpResponse(request.META['REMOTE_ADDR'])  



def register_gfan(username, password, mail):
    from tea import encrypt
    channel_id = 86
    app_key = 'fengyunanghu218&'
    post_url = 'http://api.gfan.com/uc1/common/register'
    post_data = u'<request><username>%s</username><password>%s</password><email>%s</email></request>' % (username, password, mail)
    post_data = post_data.encode('utf-8') #map(ord, post_data)
    app_key = app_key.encode('utf-8') #map(ord, app_key)
    #print(post_data,app_key)
    post_data = base64.encodestring(encrypt(post_data, app_key))

    user_agent = 'channelID=%d' % channel_id
    result = http_post(post_url, post_data, 'text', user_agent)
    print(result)
    link_key = 0
    if result != '':
        xml_dom = minidom.parseString(result)
        xml_root = xml_dom.documentElement
        link_key = xml_root.getElementsByTagName('uid')[0].toxml().replace('<uid>', '').replace('</uid>', '')
        #print(result_code,result_msg,link_key)
    return link_key

def login_baidu(username, password):
    login_url = 'http://duokoo.baidu.com/openapi/client/login'
    client_id = '443a533492ed342ea2e29671bd54f2cc'
    game_id = '112'
    Aid = ''
    session_secret = '5845d760f622b7e2c9094b466589a179'
    
    result_code, result_msg, link_key = [1, '', '']
#    print(password)
#    password = urlquote(password)
    from urllib2 import quote,unquote, urlopen
#    password = unquote(password)
#    print(password)
    client_secret = '%s%s%s%s%s%s' % (client_id, game_id, Aid, username, unquote(password), session_secret)
    client_secret = md5(client_secret)
#    password = urlquote(password)
    query_url = '%s?client_id=%s&game_id=%s&Aid=%s&user_name=%s&user_pwd=%s&client_secret=%s' % (login_url, client_id, game_id, Aid, quote(username), password, client_secret)
    print(query_url)
#    if True:
    try:
        result = urlopen(query_url,timeout=5).read()
#        result = http_post(query_url)
        print('result:', result)
        if result != '':
            result = json.loads(result)
            if result.get('uid', None) != None:
                link_key = result['uid']
                result_code = 0
                result_msg = [result['uid'], result['client_secret'], result['access_token']]
            else:
                result_msg = result.get('error_msg', '')
            
    except Exception, e:
        result_code = -1
        print('login baidu has error', e)
    
    return (result_code, result_msg, link_key)

def register_baidu(username, password):
    login_url = 'http://duokoo.baidu.com/openapi/client/register'
    client_id = '443a533492ed342ea2e29671bd54f2cc'
    game_id = '112'
    Aid = ''
    session_secret = '5845d760f622b7e2c9094b466589a179'
    
    result_code, result_msg, link_key = [1, '', 0]
    
    client_secret = '%s%s%s%s%s%s' % (client_id, game_id, Aid, username, password, session_secret)
    client_secret = md5(client_secret)
    
    query_url = '%s?client_id=%s&game_id=%s&Aid=%s&user_name=%s&user_pwd=%s&client_secret=%s' % (login_url, client_id, game_id, Aid, username, password, client_secret)
    try:
        from urllib2 import urlopen
#        print(query_url)
        result = urlopen(query_url,timeout=5).read()
#        result = http_post(query_url)
        print('result:', result)
        result = json.loads(result)
        if result.get('uid', None) != None:
            link_key = result['uid']
            result_code = 0
            result_msg = [result['uid'], result['client_secret'], result['access_token']]
        else:
            result_msg = result.get('error_msg', '')
            
    except Exception, e:
        result_code = -1
        print('login baidu has error', e)
    
    return (result_code, result_msg, link_key)




