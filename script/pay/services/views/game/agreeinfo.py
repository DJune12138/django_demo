# -*- coding: utf-8 -*-
#
#游戏玩家相关
#
#django 常用导入
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.db.models import Q 
from django.utils.html import conditional_escape 
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
from django.template import loader, Context, Template
#==========================================
from settings import TEMPLATE_DIRS, MEDIA_ROOT, STATIC_ROOT
from urls.AutoUrl import Route
import hashlib, datetime, json, MySQLdb, urllib, os
from views.base import GlobalPathCfg
from util import trace_msg
import os

_globalpathcfg = GlobalPathCfg()

@Route()
def create_agreeinfo(request,template='game/agree_info.html'):
    '''
    '''
    path = '%s/argreeinfo' %STATIC_ROOT
    filetext = '%s/argreeinfo.txt' %path

    if not os.path.exists(path):
        os.makedirs(path)
        os.mknod(filetext)

    try:
        filet = open(filetext, 'r')
        content = filet.read()
        filet.close()
    except Exception,e:
        err_msg = trace_msg()

    if request.method == 'POST':
        content = request.POST.get('content', '')
#        url = request.POST.get('url', '')
        filet = open(filetext, 'w')
        filetext = filet.write(content.encode('utf-8'))
        filet.close()
        file_url = create_agreeinfo_html(request,content)

        return HttpResponse(u'保存成功!<br>地址：%s'%'<a href="%s" target="_blank">%s</a>'%(file_url,file_url))

    return render_to_response(template, locals())


def create_agreeinfo_html_file(content,use_template=True):
    '''创建公告模版
    '''
#    gl_path = _globalpathcfg
    file_name = 'argreeinfo.html'
    save_path = '%s/argreeinfo/argreeinfo.html' %STATIC_ROOT
    template_path = '%s/argreeinfo/argreeinfo_template.html' %STATIC_ROOT
    file_tpl = open(template_path, 'r')
    tpl_content = file_tpl.read()
    file_tpl.close()
    t = Template(tpl_content)
    html_file = open (save_path, 'w')
    if use_template:
        c = Context({"title":"用户协议", "content": content})
        c = t.render(c)
    else:
        c = content # 只保存内容，不使用模版
    html_file.write(c.encode('utf-8'))
    html_file.close()
    return file_name

def create_agreeinfo_html(request,content,use_template=True):
    file_name = create_agreeinfo_html_file(content, use_template)
    file_url = 'http://%s/static/argreeinfo/%s' % (request.get_host(), file_name)

    return file_url

