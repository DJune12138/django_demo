#coding=utf-8
# Create your views here.
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from models.card import Card,CardBatch,CardLog,letter
from models.center import Server,Group
import datetime,time
import random

from views.log.exprot_file import CardExport
from django.db import connections
import re,traceback
from views.base import get_server_list
from views.card.batch import group_ajax
import sys
import json
    
#新手卡列表
def card_list(request):
    msg = ''
    batch_id = int(request.REQUEST.get('batch_id', '0'))
    page_num = int(request.REQUEST.get('page_num', '1'))    
    if page_num < 1:
        page_num = 1 
    page_num = int(request.REQUEST.get('page_num', '1'))
    page_size = 50
    list_data = []    
    search_type = int(request.REQUEST.get('search_type','0'))
    status = request.REQUEST.get('status','')
    
    sdate = request.REQUEST.get('start_date','')
    edate = request.REQUEST.get('end_date','')
    
    search_val = request.REQUEST.get('search_val','')
    query = ['1=1']
    total_record = 0
    card_batch = None
    list_server = get_server_list()
    server_id = int(request.REQUEST.get('server_id','0'))
    if batch_id > 0:
        query.append(" and batch_id = '%s'"%batch_id)
        try:
            card_batch = CardBatch.objects.using('card').get(id = batch_id)
            key = card_batch.key
            Card._meta.db_table = Card.get_card_table_name(key)
            if search_type != 0 and search_val !='':
                if search_type == 1:
                    query.append(" and number = '%s'"%search_val)
                elif search_type == 2:
                    query.append(" and player_id = '%s'"%search_val)
#                elif search_type == 3:
#                    query.append(" and password = '%s'"%search_val)                    
            if server_id != 0:
                query.append(" and server_id = %d "%server_id)
            if status != '':
                try:
                    status = int(status)
                    query.append(" and status = %d "%status)
                except:
                    pass
            if sdate != '' and edate != '':
                query.append(" AND DATE(`use_time`) >= '%s' AND DATE(`use_time`) <= '%s'"%(sdate,edate))
            total_record = Card.objects.using('card').extra(where=[''.join(query)]).count()
            if total_record > 0:
                list_data = Card.objects.using('card').extra(where=[''.join(query)]).order_by('-id')[(page_num - 1) * page_size:page_num * page_size]
                for item in list_data:
                    item.server = ''
                    if item.server_id:
                        the_server = Server.objects.get(id = item.server_id)
                        if the_server:
                            item.server = the_server.name
        except Exception, e:
            print('create card number error:', e)   
            msg = '%s'%e        

    parg = {} 

    parg['page_num'] = page_num
    parg['page_size'] = page_size
    parg['total_record'] = total_record
    parg['msg']  = msg 
    parg['list_data'] = list_data
    parg['card_batch'] = card_batch
    parg['search_type'] = search_type
    parg['search_val'] = search_val
    parg['batch_id'] = batch_id
    parg['list_server'] = list_server
    parg['server_id'] = server_id
    parg['status'] = status
    parg['sdate'] = sdate
    parg['edate'] = edate
    return render_to_response('card/card_list.html', parg)

#礼包卡列表
def card_log_list(request):
    export = int(request.REQUEST.get('export', '0'))
    close_export = int(request.REQUEST.get('close_export', '0'))
    clear_export_old_file = int(request.REQUEST.get('clear_export_old_file', '0'))
        
    msg = ''
    batch_id = int(request.REQUEST.get('batch_id', '0'))
    page_num = int(request.REQUEST.get('page_num', '1'))    
    if page_num < 1:
        page_num = 1 
    page_size = 50
    if export > 0:
        page_size = 500     
    list_data = []    
    search_type = int(request.REQUEST.get('search_type','0'))
    search_val = request.REQUEST.get('search_val','')
    status = request.REQUEST.get('status','')
    now = datetime.datetime.now()
    sdate = request.REQUEST.get('start_date',now.strftime("%Y-%m-01 00:00:00"))
    edate = request.REQUEST.get('end_date',now.strftime("%Y-%m-%d %H:%M:%S"))    
    query = ['1=1']
    total_record = 0
    group = int(request.REQUEST.get('group','0')) 
    list_group = Group.objects.all()
    if 0 != group:
        try:
            list_server = Group.objects.get(id = group).server.all()
        except:
            list_server = None
            pass
    else:
        list_server = get_server_list() 
    server_id = int(request.REQUEST.get('server_id','0'))
    if batch_id > 0:
        query.append(" and card_key = '%s'"%batch_id)
    try:
        if search_type != 0 and search_val !='':
            if search_type == 1:
                query.append(" and `number` = '%s'"%search_val)
            elif search_type == 2:
                query.append(" and `player_id` = '%s'"%search_val)
            elif search_type == 3:
                query.append(" and `card_key` = '%s'"%search_val)
            elif search_type == 4:
                query.append(" and `id` = %d "% int(search_val)) 
            elif search_type == 5:
                query.append(" and `card_name` like '%s%s%s'"%('%%',search_val,'%%'))
#                elif search_type == 3:
#                    query.append(" and password = '%s'"%search_val) 
        if status != '':
            query.append(" and `status` = %d " % int(status))

        if sdate != '' and edate != '':
            query.append(" AND `create_time` >= '%s' AND `create_time` <= '%s'"%(sdate,edate))
                        
        if server_id != 0:
            query.append(" and server_id = %d "%server_id)
        elif group != 0:
            query_server_id = []
            for server_item in list_server:
                query_server_id.append(int(server_item.id))
            if len(query_server_id) != 0:
                query_server_id = tuple(query_server_id)
                query.append(" and `server_id` in %s "%str(query_server_id))
            else:
                query.append(" and 0 ")  
        total_record = CardLog.objects.using('card').extra(where=[''.join(query)]).count()
        print ''.join(query)
        if total_record > 0:
            list_data = CardLog.objects.using('card').extra(where=[''.join(query)]).order_by('-id')[(page_num - 1) * page_size:page_num * page_size]
            server_models_dict = {}
            for s in Server.objects.all().values('id','name'):
                server_models_dict[s['id']] = s['name']
            for item in list_data:
                item.server = ''
                if item.server_id:
                    item.server = server_models_dict.get(int(item.server_id),item.server_id)
                    
        #处理 导出文件
        if  export >0: 
            print export
            export_data = []
            fields = [u'礼包ID',u'礼包卡名',u'礼包卡号',u'礼包卡标识',u'使用时间',u'奖励内容',u'角色ID',u'服务器',u'奖励状态']
            try:
                for item in list_data:
                    export_data.append([item.id,item.card_name, item.number, item.card_key, item.create_time_str(), item.prize, item.player_id, item.server_name(), item.get_status_name()])
            except Exception,e:
                print 'error',e
            

            #session ID 
            session_id = request.COOKIES.get('sessionid')
            pre_file_name = ''   
            if search_val != '':
                pre_file_name = '%s%s_'%(pre_file_name,search_val)
            if group != 0:
                try:
                    pre_file_name = '%s%s_'%(pre_file_name,Group.objects.get(id = group).name)
                except:
                    pass
            if server_id != 0:
                try:
                    pre_file_name = '%s%s_'%(pre_file_name,Server.objects.get(id = server_id).name)
                except:
                    pass           
            file_name = '%s%s_%s___%s'%(pre_file_name, sdate.replace("-","").replace(":","").replace(" ",""), edate.replace("-","").replace(":","").replace(" ",""), session_id)
            file_name = file_name.encode("utf-8")
            card_export = CardExport(file_name,export)   

            return HttpResponse(json.dumps(card_export.gene_file(file_name,export_data, fields=fields, page_num=page_num, page_size=page_size, total_record=total_record)) )             
         
    except Exception, e:
        traceback.print_exc()
        print('search CardLog error:', e)   
        msg = '%s'%e        
    usm = request.admin
    parg = {} 
    parg["usm"] = usm
    parg['page_num'] = page_num
    parg['page_size'] = page_size
    parg['total_record'] = total_record
    parg['msg']  = msg 
    parg['list_data'] = list_data
    parg['search_type'] = search_type
    parg['search_val'] = search_val
    parg['batch_id'] = batch_id
    parg['list_server'] = list_server
    parg['server_id'] = server_id
    parg['status'] = status
    parg['list_group'] = list_group
    parg['group'] = group
    parg['sdate'] = sdate
    parg['edate'] = edate    
    return render_to_response('card/card_log_list.html', parg)



def card_log_recover(request):
    import json
    ids = request.REQUEST.getlist('id')
    status = int(request.REQUEST.get('status','') or 0 )
    result_code = 1
    msg = ''
    if ids != '':
        try:
            card_log = CardLog.objects.using('card').filter(id__in = ids, status__in=[2,3])
            for item in card_log:
                item.status = status
                item.save(using='card')
            result_code = 0
            msg = '激活成功！'
        except Exception, e:
            print('card_log_recover error:', e)
            msg = '激活失败！'
    else:
        msg = '礼包卡号不存在'
    return HttpResponse(json.dumps({"code" : result_code, "msg" : "%s" % msg}))
        
        
from views.base import getConn


def card_create(request):
    '''创建礼包卡
    '''
    msg = ''
    card_count = int(request.REQUEST.get('card_count','0'))
    batch_id = int(request.REQUEST.get('batch_id','0'))
    record = int(request.REQUEST.get('record','0'))

    card_size = 2000
    if card_count < card_size:
        card_size = card_count
        
    if card_count - record < card_size:
        card_size = card_count - record
    
    is_finish = 0
    
    if card_count == record:
        is_finish = 1    
   
    if batch_id > 0 and card_count > 0 and card_size > 0 and is_finish == 0:
        try:
            card_batch = CardBatch.objects.using('card').get(id = batch_id)
            key = card_batch.key
            #card = Card()
            card_table_name = Card.get_card_table_name(key)
            Card._meta.db_table = Card.get_card_table_name(key)
            card = Card()      
            card.batch_id = batch_id     
            
            conn = connections['card']
            cursor = conn.cursor()              
            if card_batch:
                insert_sql = []
                add_time = datetime.datetime.now()
                number_cache_list = []
                for i in range(0,card_size):
                    while True:
                        number = Card.get_card_number(key)
                        if number not in number_cache_list:
                            number_cache_list.append(number)
                            break
                    count_sql = "SELECT COUNT(*) FROM `%s` c WHERE c.`number` = '%s' "%(card_table_name,number)
                    cursor.execute(count_sql)
                    count = cursor.fetchone()
                    repeat_count = int(count[0])   
                    if repeat_count == 0:          
                        insert_sql.append("('%s','%s','%s',0,0)"%(batch_id,number,add_time))
                        i = i + 1
                cursor.execute('INSERT INTO `%s`(`batch_id`,`number`,`add_time`,`status`,`use_count`) VALUES  %s'%(card_table_name, ','.join(insert_sql)))
                cursor.close()
                card_batch.total_count = card_batch.total_count + i
                card_batch.save(using='card')
                record = record + i
        except Exception, e:
            print('create card number error:', e)
            traceback.print_exc()
            msg = '%s'%e
            
    return HttpResponse('{"is_finish":%d,"msg":"%s","record":"%s"}'%(is_finish,msg, record))

def toTrueText(s):
    if None == s : 
        return ''
    #先过滤CDATA
    re_cdata=re.compile('//<!\[CDATA\[[^>]*//\]\]>',re.I) #匹配CDATA
    re_script=re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>',re.I)#Script
    re_style=re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>',re.I)#style
    re_h=re.compile('</?\w+[^>]*>')#HTML标签
    re_comment=re.compile('<!--[^>]*-->')#HTML注释
    s=re_cdata.sub('',s)#去掉CDATA
    s=re_script.sub('',s) #去掉SCRIPT
    s=re_style.sub('',s)#去掉style
    s=re_h.sub('',s) #去掉HTML 标签
    s=re_comment.sub('',s)#去掉HTML注释
    return s

def export_card(request): 
    page_size = 500
    is_chl = int(request.REQUEST.get('is_chl','0'))
    clear_export_old_file = int(request.REQUEST.get('clear_export_old_file', '0'))
    page_num = int(request.REQUEST.get('page_num', '1'))    
    batch_id = int(request.REQUEST.get('batch_id','0'))
    card_status = int(request.REQUEST.get('card_status','0'))
    start_date = request.REQUEST.get('start_date','')
    end_date = request.REQUEST.get('end_date','')
    export = int(request.REQUEST.get('export','2'))
    if page_num < 1:
        page_num = 1  
    fields = ''    
    #处理 导出文件
    if batch_id > 0 and export > 0: 
        try:
            select_sql = ''
            where_sql = ''
            card_data = []
            card_batch = CardBatch.objects.using('card').get(id = batch_id)
            key = card_batch.key     
            card_table =  Card.get_card_table_name(key)
            from settings import DATABASES
            import MySQLdb
            the_conn_str = DATABASES['card']
            port = int(the_conn_str.get('PORT',3306))
            conn = MySQLdb.connect(host=the_conn_str['HOST'],user=the_conn_str['USER'],passwd=the_conn_str['PASSWORD'], port=port, db=the_conn_str['NAME'],charset='utf8') 
            #conn = connections['card']
            cursor = conn.cursor()
            fields = [u'卡号',u'使用状态']
            if card_status == 3:
                select_sql = ",IF(c.`status`=0,'未使用',IF(c.`status`=1,'已领取',IF(c.`status` = 2,'已使用','删除')))"
                where_sql = ''
            elif card_status == 0:
                where_sql = ' AND c.`status` = 0'
                select_sql = ",'未使用' "                    
            elif card_status == 1:
                where_sql = ' AND c.`status` = 1'
                select_sql = ",'已领取' "
            elif card_status == 2:
                where_sql = ' AND c.`status` = 2'
                select_sql = ",'已使用',c.`use_count`, c.`use_time`,c.`player_id`, c.`server_id` "
                fields = [u'卡号','使用状态',u'使用次数',u'使用时间', u'角色ID', u'服务器']
                
            if start_date != '' and end_date != '':
                if card_status == 2:
                    where_sql += " AND c.`use_time` >= '%s' AND c.`use_time` <= '%s'"%(start_date,end_date)
                else:
                    where_sql += " AND c.`add_time` >= '%s' AND c.`add_time` <= '%s'"%(start_date,end_date)
                
            sql = "SELECT c.`number` %s FROM `%s` c WHERE 1=1 %s ORDER BY c.`id` "%(select_sql,card_table,where_sql)
            count_sql = "SELECT COUNT(*) FROM (%s) a" % sql
            cursor.execute(count_sql)
            count = cursor.fetchone()
            total_record = int(count[0])  
            file_name = [] 
            export_key = '%s_%s' % (card_batch.name,request.admin.id)
            card_export = CardExport(export_key,export)

            file_name.append('%s' % key)
            file_name = ''.join(file_name)
            if total_record > 0:  
                sql = "%s LIMIT %s,%s"%(sql,(page_num - 1) * page_size,page_size) 
                cursor.execute(sql)
                card_data = cursor.fetchall()
                
                if card_status == 2:
                    new_data = []
                    for item in card_data:
                        item = list(item)
                        if item[4]:
                            the_server = Server.objects.get(id = int(item[4]))
                            if the_server:
                                item[4] = the_server.name
                        new_data.append(item)
                    card_data = new_data
                try:
                    is_finish = False
                    de = total_record / page_size
                    if total_record % page_size >= 1:
                        total_page =  de + 1 
                    else:
                        total_page =  de
                    if page_num+1 > total_page:
                        is_finish = True                    
                    if is_chl == 1 and card_status == 0 and is_finish:
                        min_max_sql = "SELECT MIN(c.`id`), MAX(c.`id`) FROM `%s` c WHERE 1 = 1 %s "%(card_table,where_sql)
                        cursor.execute(min_max_sql)
                        min_max = cursor.fetchone()
                        if min_max[0] != None and min_max[1] != None:
                            min_val = int(min_max[0])             
                            max_val = int(min_max[1])
                            update_sql = "UPDATE `%s` SET `status` = 1 WHERE `id` >= %d AND `id` <= %d AND `status` = 0"%(card_table, min_val, max_val)
                            cursor.execute(update_sql)
                            conn.commit()
                except Exception,e:
                    print 'commit error',e 
        except Exception,e:
            traceback.print_exc()
            print 'export card error',e

        response = HttpResponse(json.dumps(card_export.gene_file(file_name,card_data, fields=fields, page_num=page_num, page_size=page_size, total_record=total_record)) )             
        return response
    return HttpResponse('导出出错！请重试！')    

# 删除新手卡号
def card_del(request):
    model_id = int(request.REQUEST.get('id','0'))
    batch_id = int(request.REQUEST.get('batch_id','0'))
    if model_id > 0 and batch_id > 0:
        try:
            card_batch = CardBatch.objects.using('card').get(id = batch_id)
            key = card_batch.key
            Card._meta.db_table = Card.get_card_table_name(key)
            the_card = Card.objects.using('card').get(id=model_id)
            the_card.status = -1
            the_card.save(using='card')
            
        except Exception, e:
            print('update error:', e)
    else:
        return HttpResponse("操作有误！<a href='javascript:history.back();'>点击返回</a>")
    return render_to_response('feedback.html')

# 领取新手卡号
def card_get(request,batch='0',server_id=0):
    server_id = int(server_id)
    batch = int(batch)
    model_id = request.POST.get('id','')
    number = 0
    count = 0
    if batch == 0 and server_id == 0:
        server = Server.objects.filter(status__gt=1)
        return render_to_response('card/card_obtain.html',{'server':server})    
    elif 'id' in request.POST and request.POST['id']:
        model_id = int(model_id)
        card =Card.objects.filter(status=0,is_use=1,server_id=int(model_id),batch_id=batch)
        count = len(card)     
    elif batch == 0 and server_id > 0:
        card =Card.objects.filter(status=0,is_use=1,server_id=server_id)
        count = len(card)
    elif batch != 0:
        server = Card.objects.filter(batch_id=batch,is_use=1)
        server.query.group_by = ['server_id']
        server = server
        return render_to_response('card/card_get.html',{'server':server,'batch':batch})       
    if count:
        try:
            cid = card[0].id
            number = card[0].number
            c = Card.objects.get(id=int(cid))
            c.status = 1
            c.get_time = datetime.datetime.now()
            c.safe_save()
            return render_to_response('feedback.html')
        except Exception, e:
            print('update error:', e)        
            return HttpResponse("领取失败！<a href='javascript:history.back();'>返回</a>")
    else:
        return HttpResponse("卡号不足，领取失败！<a href='javascript:history.back();'>点击返回</a>")
    return HttpResponseRedirect('/card/list/?number=%s'%number)
    
# 使用新手卡号
def card_use(request):
    number = request.POST.get('number','')
    password = request.POST.get('password','')
    if number != '':
        #query = Card.objects.filter(number=number,password=password,status=1)
        query = Card.objects.filter(number=number,status=1,is_use=1)
        if query:
            c = Card.objects.get(number=number)
            if c.password != '' and c.password != password:
                return render_to_response('card/card_use.html',{'msg':'卡号或密码错误！'})
            c.status = 2
            c.use_time = datetime.datetime.now()
            c.safe_save()
            return render_to_response('feedback.html')
        else:
            return render_to_response('card/card_use.html',{'msg':'卡号有误'})
    else:
        return render_to_response('card/card_use.html')