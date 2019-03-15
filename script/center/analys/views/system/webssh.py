#! /usr/bin/python
# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response 
from models.admin import Role, Menu
from django.http import HttpResponse,HttpResponseRedirect
from views.base import GlobalPathCfg,mkdir
import json
from urls.AutoUrl import Route
import os,re
import datetime
from util import trace_msg
import urllib,urllib2


from urls.AutoUrl import Route


WebSSHAddress = '127.0.0.1:7001'



@Route('^webssh/(?P<static_file>.*)')
def webssh(request,static_file=''):
    '''连接Webssh服务器
    '''
    PROXY_FORMAT = u'http://%s/%s' % (WebSSHAddress,'%s')


    url = '%s' % static_file

    data = None
    if request.method == 'GET':
        url_encode = '%s?%s' % (url, request.GET.urlencode())
        url = PROXY_FORMAT % url_encode
    elif request.method == 'POST':
        url = PROXY_FORMAT % url
        data = request.POST.urlencode()

    response = urllib2.urlopen(url, data)
    
    content = response.read()
    return HttpResponse(content, status=int(response.code), mimetype=response.headers.gettype())












