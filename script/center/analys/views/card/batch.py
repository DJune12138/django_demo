#coding=utf-8
# Create your views here.
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response

from models import DictDefine
from models.card import CardBatch,Card
from django.db import connections
import datetime

from util import constant
from views.base import get_server_list
from models.channel import  Channel
from models.server import Group
import re,json
import random
import sys
from models.admin import Admin
from views.widgets import get_group_servers_dict, get_agent_channels_dict, get_group_channels_dict, groups_servers


def group_ajax(request):
    group = int(request.POST.get('group', '0'))
    option_str = []
    option_str.append('<option value="0">服务器</option>')
    if 0 != group:
        list_server = Group.objects.get(id = group).server.all()
    else:
        list_server = get_server_list() 
    if len(list_server) != 0:
        for item in list_server:
            option_str.append('<option value="%s">%s</option>'%(item.id, item.name))
    return HttpResponse(''.join(option_str))   
    
def batch_list(request):

    # list_group = Group.objects.all()   
    list_group = request.admin.get_resource(
        'server_group').all().values('id', 'name') 
    
    query = ['1=1']
    status = int(request.GET.get('status','1'))
    query.append(' and status = %d '% status)
    page_size = 20
    page_num = int(request.GET.get('page_num', '1'))    
    if page_num < 1:
        page_num = 1 
    search_card = int(request.GET.get('search_card','0'))
    search_card_val = request.GET.get('search_card_val','')
  
    server_id = int(request.GET.get('server_id','0'))    
    group = int(request.GET.get('group','0')) 
    if 0 != group:
        try:
            list_server = Group.objects.get(id = group).server.all()
        except:
            list_server = None
            pass
    else:
        # list_server = get_server_list() 
        list_server = request.admin.get_resource(
        'server').all().order_by("-status", "order")
    card_batch = None
    if status == 1:
        query.append(" and end_time >= '%s'"%(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    elif status == 0:
        query.append(" or end_time < '%s'"%(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    if search_card != 0 and search_card_val !='':
        if search_card == 1:
            query.append(" and `key` = '%s'"%search_card_val)
        elif search_card == 2:
            query.append(" and `name` like '%s%s%s'"%('%%',search_card_val,'%%'))        
    if server_id != 0:
        query.append(" and `server` REGEXP '^%d$|,%d$|^%d,' "%(server_id,server_id,server_id))
    elif group != 0:
        query_server_id = []
        for item in list_server:
            query_server_id.append("`server` REGEXP '^%d$|,%d$|^%d,' "%(item.id,item.id,item.id))
        if len(query_server_id) != 0:
            query.append(" and (%s) "%(' or '.join(query_server_id)))
        else:
            query.append(" and 0 ")

    if not request.admin.is_root:
        query_server_id = []
        if list_server:
            for item in list_server:
                query_server_id.append("`server` REGEXP '^%d$|,%d$|^%d,' "%(item.id,item.id,item.id))

            if len(query_server_id) != 0:
                query.append(" and (%s) "%(' or '.join(query_server_id)))
            else:
                query.append(" and 0 ")

    total_record = CardBatch.objects.using('card').extra(where=[''.join(query)]).count() 
    if total_record:   
        card_batch = CardBatch.objects.using('card').extra(where=[''.join(query)]).order_by('-id')[(page_num - 1) * page_size:page_num * page_size] 
        admins_list = Admin.objects.values_list('id','alias').all()
        admin_dict = dict(admins_list)
        for item in card_batch:
            item.prize_content = item.prize
            item.server_content = item.get_server_content()
            item.channel_content = item.get_channel_content()
            item.expire = 0
            item.create_user = admin_dict.get(item.create_user,item.create_user)
            if item.end_time < datetime.datetime.now():
                item.expire = 1
                
            if item.used_count == item.total_count:
                item.rate = 100
            else:
                item.rate = round(float(item.used_count) * 100 / item.total_count,2)
    parg = {}
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    parg["batch"] = card_batch
    parg['status'] = status
    parg['list_server'] = list_server
    parg['server_id'] = server_id
    parg['search_card'] = search_card
    parg['search_card_val'] = search_card_val   
    parg['list_group'] = list_group 
    parg['group'] = group
    parg['request'] = request
    return render_to_response('card/batch_list.html', parg)

def batch_edit(request):

    model_id = request.GET.get('id', 0)
    group_id = int(request.REQUEST.get('group_id','') or 0 )
    card_id = request.GET.get('card_id', 0)
    is_copy = request.GET.get('is_copy', '')
    
    # group_servers_dict = get_group_servers_dict(request,group_id)
    group_servers_dict = groups_servers(request)
    # agent_channels_dict = get_agent_channels_dict(request)
    group_channels_dict = get_group_channels_dict()

    query_server = []
    query_channel = []
                        
    model_id = int(model_id)
    
    the_key = ''
    if model_id > 0:
        model = CardBatch.objects.using('card').get(id=model_id)
        select_server_ids = model.get_server_ids()
        select_channel_ids = model.get_channels_ids()
        prize = model.prize
    else :
        try:
            conn = connections['card']
            cursor = conn.cursor()
            sql = "SELECT SUBSTR(`table_name`,7) FROM INFORMATION_SCHEMA.`TABLES` WHERE `table_schema` = 'fytx2_card' AND `table_name` REGEXP '^cards_[[:lower:]]{3}$' ORDER BY `table_name` DESC LIMIT 1"
            cursor.execute(sql)
            count = cursor.fetchone()
            the_key = count[0]
        except:
            pass

        now = datetime.datetime.now()
        model = CardBatch()
        model.id = model_id
        model.limit_count = 1
        print '7' * 40
        print the_key
        model.make_card_key(the_key)
        model.start_time = "2000-01-01 00:00:00"
        model.end_time = (now + datetime.timedelta(days=90)).strftime("%Y-%m-%d 00:00:00")

        if is_copy and card_id > 0:
            card_model = CardBatch.objects.using('card').get(id=card_id)
            select_server_ids = card_model.get_server_ids()
            select_channel_ids = card_model.get_channels_ids()
            prize = card_model.prize

    is_dialog = request.REQUEST.get('is_dialog','')
    last_url = '/card/batch/?status=1'

    # 道具、资源列表
    property_dict = DictDefine.objects.get(id=constant.property_id_dict).json_dict
    resource_dict = DictDefine.objects.get(id=constant.resource_id_dict).json_dict

    return render_to_response('card/batch_edit.html', locals())  

def generate_password(num_len = 0, lower_len = 0, upper_len = 0):
    num = '23456789'
    lower = 'abcdefghjkmnpqrstuvwxyz'
    upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    char = ''.join([lower,upper,num])
    tmp = ''
    password = ''
    
    if num_len != 0:
        tmp += ''.join(random.sample(num,int(num_len)))

    if lower_len != 0:
        tmp += ''.join(random.sample(lower,int(lower_len)))
                
    if upper_len != 0:
        tmp += ''.join(random.sample(upper,int(upper_len)))
    
    if tmp != '':
        password = ''.join(random.sample(tmp,int(num_len) + int(lower_len) + int(upper_len)))
        
    if password == '':
        password = ''.join(random.sample(char,6))
    return password

def batch_save(request):
    msg = ''
    server_list = request.POST.getlist('server_id')
    channel_list = request.POST.getlist('channel_id')
    
    
    model_id = request.GET.get('id','')
    model_id = int(model_id)
    key = request.POST.get('key','').lower()
    name = request.POST.get('name','')
    limit_count = request.POST.get('limit_count','')
    remark = request.POST.get('remark','')
    start_time = request.POST.get('start_time','')
    end_time = request.POST.get('end_time','')
    
    prize = request.POST.get('prize','')
    show = request.POST.get('show','')
    
    level = request.POST.get('level','0')
    other_condition = request.POST.get('other_condition','{}')
    card_limit_count = int(request.POST.get('card_limit_count','') or 0)
    create_user = int(request.admin.id)
    if not CardBatch.check_card_key(key):
        msg = '标识只能是3位纯小写字母！'
    elif name == '':
        msg = '名称不能为空！'
    elif limit_count == '' or not re.match('^\d+$', limit_count):
        msg = '可用次数只能是纯数字！'   
    elif start_time == '' or end_time == '':
        msg = '时间不能为空！'        
    elif start_time > end_time:
        msg = '开始时间不能大于结束时间！'
    elif end_time < datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
        msg = '结束时间不能小于服务器时间！'
    
    if model_id > 0:
        model = CardBatch.objects.using('card').get(id = model_id)
    else:
        model = CardBatch() 
        if CardBatch.objects.using('card').filter(key = key).count() > 0:
            msg = '礼包卡类标识已经存在！'
    if prize != '':
        try:
            json.loads(prize)
        except Exception,e:
            print 'json error',e
            msg = '奖励格式有误！请检查！'
    if msg == '' and key != '' and name !='' and limit_count != ''  and start_time != '' and end_time != '':
        try:
   
            if model_id == 0:    
                model.key = key
            model.name = name
            model.start_time = start_time
            model.end_time = end_time
            model.limit_count = limit_count
            model.prize = prize
            model.server = ','.join(set(server_list))
            model.show = int(show)
            model.level = int(level)
            model.card_limit_count = card_limit_count
            model.channels = ','.join(channel_list)
            model.create_user = create_user
            try:
                _ = json.loads(other_condition)
                model.other_condition = other_condition
            except:
                msg = '条件解析错误!'
            
            model.remark = remark
            if model.code == '' or model.code == None or model.code == 'None':
                model.code = generate_password(2, 3, 3)
            model.save(using='card')
            if model.id > 0 and model_id == 0:
                try:
                    sql = "CREATE TABLE IF NOT EXISTS `%s` LIKE `card_0`" % Card.get_card_table_name(key)
                    conn = connections['card']
                    cursor = conn.cursor()
                    cursor.execute(sql)
                    cursor.close()
                except Exception,e:
                    print 'create table `card_%s` error' % Card.get_card_table_name(key)
                    msg = '礼包卡类标识已经存在！%s' % e
        except Exception,e:
            print 'save batch error',e
            msg = '%s'%e
    parg = {} 
    parg['err_msg'] = msg
    parg['next_url'] = '/card/batch/?status=1'
    is_dialog = request.REQUEST.get('is_dialog','')
    if msg:
        return HttpResponse(msg)
    if msg and is_dialog:
        return render_to_response('feedback.html', parg)
    parg['msg'] = '保存成功！'
    return render_to_response('card/feedback.html', parg)
    # return HttpResponse("保存成功")
    
def batch_del(request):
    ids = request.GET.get('ids','0')
    if ids != '':
        try:
            card_batch = CardBatch.objects.using('card').filter(id__in = ids.split(','))
            for item in card_batch:
                item.status = 0 
                item.save(using='card')

#            elif status == -1:             
#                card_batch.status = 0
#                card_batch.save(using='card')
#            elif status == 2:
#                key = card_batch.key
#                Card._meta.db_table = 'card_%s'%key
#                Card.objects.using('card').extra(where=["status = 1"]).delete()                     
        except Exception, e:
            print('del batch error:', e)
    else:
        return HttpResponse("id不能为空！")
    return render_to_response('feedback.html')

def batch_recover(request):
    ids = request.GET.get('ids','0')
    if ids != '':
        try:
            card_batch = CardBatch.objects.using('card').filter(id__in = ids.split(','))
            for item in card_batch:
                item.status = 1 
                item.save(using='card')

#            elif status == -1:             
#                card_batch.status = 0
#                card_batch.save(using='card')
#            elif status == 2:
#                key = card_batch.key
#                Card._meta.db_table = 'card_%s'%key
#                Card.objects.using('card').extra(where=["status = 1"]).delete()                     
        except Exception, e:
            print('recover batch error:', e)
    else:
        return HttpResponse("id不能为空！")
    return render_to_response('feedback.html')
