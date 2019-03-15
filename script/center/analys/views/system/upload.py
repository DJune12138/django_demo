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
import urllib

STATIC_PATH = os.path.join(GlobalPathCfg().get_static_folder_path(),'upload')# 保存路径
mkdir(STATIC_PATH)

inputName = 'filedata'
upExt='txt,rar,zip,jpg,jpeg,gif,png,swf,wmv,avi,wma,mp3,mid'#上传扩展名


def wirte_static_file(file_name,cont):
    err_msg = url =''
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    
    try:
        file_name = urllib.unquote(file_name).encode('utf-8')
        file_suffix = os.path.splitext(file_name)[1].lstrip('.').lower()
        if file_suffix in upExt.split(','):
                the_path = os.path.join(STATIC_PATH,date_str)
                mkdir(the_path)
                fp = open(os.path.join(the_path,file_name),'wb')
                fp.write(cont)
                fp.close()
                url = '/static/upload/%s/%s' % (date_str,file_name)
        else:
            err_msg = '不允许的文件后缀 %s' % file_suffix
    except Exception,e:
            err_msg = trace_msg()
    return (err_msg,url)

@Route()
def img(request):
    _ret_d = {'err':'','msg':{'url':'','localname':'','id':'1'}}
    html5_file_des = request.META.get('HTTP_CONTENT_DISPOSITION','')
    file_name = cont = ''
    if html5_file_des:
        _m = re.match(r'attachment;\s+name="(.+?)";\s+filename="(.+?)"', html5_file_des,)
        if _m and len(_m.groups())==2:
            file_name = _m.group(2)
            cont = request.body
    if file_name and cont:
        err_msg,url = wirte_static_file(file_name,cont)
        _ret_d['err'] = err_msg
        _ret_d['msg']['localname'] = file_name
        _ret_d['msg']['url'] = url
    return HttpResponse(json.dumps(_ret_d))



