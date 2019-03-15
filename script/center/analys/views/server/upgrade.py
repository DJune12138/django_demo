# -*- coding: utf-8 -*-
#版本更新相关
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.template.context import RequestContext
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================

from settings import STATIC_ROOT
from models.server import Group,Server
from models.channel import Channel
from models.center import Upgrade
from util import trace_msg
from views.widgets import get_agent_channels_dict
import os

from urls.AutoUrl import Route

#更新设置
def upgrade_list(request):
    
    group_id = int(request.GET.get('group_id', 0))
    
    list_group = Group.objects.all()
    
    list_record = []
    if group_id == 0:
        list_record = Upgrade.objects.all()
    else:
        list_record = Upgrade.objects.filter(group__id=group_id)
    
    parg = {}
    parg["list_record"] = list_record
    parg["list_group"] = list_group
    parg["group_id"] = group_id
    
    return render_to_response('server/upgrade_list.html', parg)

def upgrade_clear(request):
    list_group = Group.objects.using('read').all()
    rootPath = os.path.dirname(__file__)
    
    for item_group in list_group:
        folderPath = os.path.abspath(os.path.join(STATIC_ROOT, 'upgrade' ,item_group.key))
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
        #clear old file
        for file_item in os.listdir(folderPath):
            try:
                itemsrc = os.path.join(folderPath, file_item)
                if os.path.isfile(itemsrc):
                    os.remove(itemsrc)
            except:
                pass
    return render_to_response('feedback.html')

def upgrade_make(request,model_id=0):
    list_upgrade = Upgrade.objects.using('read').all().prefetch_related('channel','group')
    rootPath = os.path.dirname(__file__)
    model_id = int(model_id)
    if 0 == model_id:
        model_id = int(request.GET.get('model_id', '0'))
    
    is_ajax = False
    if '1' == request.GET.get('ajax', '0'):
        is_ajax = True
#    if True:

    if model_id == 0:
        upgrade_clear(request)
    
    try:

        for item in list_upgrade:
            
            if model_id > 0 and model_id != item.id:
                continue
            
#            upgradeInfo = u'{"newVerCode":%d,"newVerName":"%s","apkSize":"%s","apkDlLink":"%s","verMsg":"%s","updateLink":"%s","clientVer":[%s],"min_sn":"%s"}' % (item.ver_num, item.ver_name, item.filesize, item.download_url, item.remark, item.page_url, item.client_ver,item.min_client_ver)
            upgradeInfo = u'{"newVerCode":%d,"newVerName":"%s","apkSize":"%s","iosLink":"%s","androidLink":"%s","incrementLink":"%s","subpackageLink":"%s","md5Num":"%s","verMsg":"%s","updateLink":"%s","clientVer":[%s],"min_sn":"%s","notice_switch":%d}' % (item.ver_num, item.ver_name, item.filesize, item.ios_url, item.android_url,item.increment_url,item.subpackage_url,item.md5_num,item.remark, item.page_url, item.client_ver,item.min_client_ver,item.notice_switch)

            fileContent = upgradeInfo.encode('utf-8')
            
            for item_group in item.group.all():
                folderPath = os.path.abspath(os.path.join(STATIC_ROOT, 'upgrade' ,item_group.key))
                if not os.path.exists(folderPath):
                    os.makedirs(folderPath)
                
                for item_channel in item.channel.all():
                    filePath = os.path.join(folderPath, '%s.json' % item_channel.key)
                    if not os.path.exists(filePath):
                        if os.path.isfile(filePath) and model_id > 0:
                            print 1
                            os.remove(filePath)
                        file_handler = open(filePath, "w")
                        file_handler.write(fileContent)
                        file_handler.close()

    except Exception, e:
        err_msg = trace_msg()
        print('write server list has error:%s' % e)
    
    if is_ajax:
        return HttpResponse('{"code":0}')
    return render_to_response('feedback.html',locals())


def upgrade_edit(request, model_id=0):
    model_id = int(model_id)
    
    if model_id == 0:
        model_id = int(request.GET.get('model_id', '0'))
    
    model = None
    if model_id > 0:
        model = Upgrade.objects.using('read').prefetch_related('channel','group').get(id=model_id)
        
        
    group_list = Group.objects.all()
    if model == None:
        model = Upgrade()
        model.id = 0
    else:
        model.remark = model.remark.replace('\\n', '\r\n')
    
    parg = {}
    parg["model"] = model
    parg["group_list"] = group_list
    parg["select_group"] = model.group.all()
    parg["agent_channels_dict"] = get_agent_channels_dict(request)
    parg['select_channel_ids'] = [ c.id for c in model.channel.all() ]
    
    return render_to_response('server/upgrade_edit.html', parg)

@Route()
def batch_upgrade_save(request):
    ids = request.REQUEST.getlist('file_id')
    update_params = {}
    msg = ''
    try:
        if ids:
            for k in request.REQUEST.keys():
                if k == 'file_id':
                    continue
                value = request.REQUEST.get(k,'')
                if value:
                    update_params[k] = value
                    msg += '%s:%s' % (k,value)
            if update_params:
                print update_params
                Upgrade.objects.using('write').filter(id__in=ids).update(**update_params)
                msg += '\n更新成功!'
            else:
                msg = '没有更新配置!'
        else:
            msg = '没有选择更新'
    except:
        msg = trace_msg()
    return HttpResponse(msg)

def upgrade_save(request, model_id=0):
    model_id = int(model_id)
    
    if model_id == 0:
        model_id = int(request.GET.get('model_id', '0'))
    
    model = None
    if model_id > 0:
        model = Upgrade.objects.using('write').get(id=model_id)
    if model == None:
        model = Upgrade()
        #model.id = 0

    model.client_ver = request.POST.get('client_ver', '')
    model.ver_num = int(request.POST.get('ver_num', '0'))
    model.ver_name = request.POST.get('ver_name', '')
#    model.download_url = request.POST.get('download_url', '')
    model.ios_url = request.POST.get('ios_url', '')
    model.android_url = request.POST.get('android_url', '')
    model.increment_url = request.POST.get('increment_url', '')
    model.subpackage_url = request.POST.get('subpackage_url', '')
    model.md5_num = request.POST.get('md5_num', '')
    model.filesize = request.POST.get('filesize', '')
    model.page_url = request.POST.get('page_url', '')
    model.remark = request.POST.get('remark', '').replace('\r', '').replace('\n', '\\n')
    model.create_time = request.POST.get('create_time', '')
    model.pub_ip = request.META.get('REMOTE_ADDR', '')
    model.pub_user = int(request.session.get('userid', '0'))
    model.min_client_ver = request.POST.get('client_ver', '')
    model.notice_switch = int(request.POST.get('notice_switch', '0'))

    try:

        if model.id :
            model.channel.clear()
            model.group.clear()
        model.save(using='write')
        channel_ids = request.POST.getlist('channel_id')
        if '0' in channel_ids:channel_ids.remove('0')  
        model.channel.add(*Channel.objects.using('write').filter(id__in=channel_ids))
        group_ids = request.POST.getlist('group_id')
        model.group.add(*Group.objects.using('write').filter(id__in=group_ids))
        
    except Exception,e:
        err_msg = trace_msg()
        print('upgrade save error:',e)
    return render_to_response('feedback.html', locals())
    


def upgrade_remove(request, model_id=0):
    model_id = int(model_id)
    
    if model_id == 0:
        model_id = int(request.GET.get('model_id', '0'))
    
    if model_id > 0 :
        try:
            model = Upgrade.objects.using('write').get(id=model_id)
            model.channel.clear()
            model.delete(using='write')
        except Exception, e:
            print('upgrade remove error:', e)
    return render_to_response('feedback.html')
