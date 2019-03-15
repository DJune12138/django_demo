# -*- coding: utf-8 -*-
#
#日志类相关
#
#django 常用导入
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
#==========================================

import MySQLdb
from models.log import Log, LogDefine
import json, MySQLdb,copy
from models.server import Server
import settings
from util import trace_msg
from urls.AutoUrl import Route
from views.base import notauth

@Route()
def log_list(request):
    '''日志类列表
    '''
    list_record = LogDefine.objects.using('read').all()
    return render_to_response('log/log_list.html', locals())

@Route()
def log_edit(request, log_id=0):
    '''日志类编辑
    '''
    log_id = log_id or int(request.REQUEST.get('id', '0'))
    log_key = request.REQUEST.get('log_key','')
    if log_id  :
        model = LogDefine.objects.using('read').get(id=log_id)
    elif log_key:
        model = LogDefine.objects.using('read').get(key=log_key)
    else:
        model = LogDefine()
        model.id = log_id
    #print LogDefine.get_create_table_sqls(is_center=False)
    return render_to_response('log/log_edit.html',locals())
    

@Route()
def log_save(request, log_id=0):
    '''日志类保存
    '''
    try:
        log_id = int(request.REQUEST.get('id', '0'))
        if log_id:
            log_def =  LogDefine.objects.get(id=log_id)
        else:
            log_def = LogDefine()
        log_def.set_attr('key',request.REQUEST.get('key', '').strip(),null=False)
        log_def.set_attr('name',request.REQUEST.get('name', '').strip(),null=False)
        log_def.set_attr('remark',request.REQUEST.get('remark', '').strip(),null=True)
        log_def.set_attr('status',request.REQUEST.get('status',''),null=False)
        log_def.set_attr('config',request.REQUEST.get('config',''),json.loads,null=False)
        log_def.set_attr('trigger',request.REQUEST.get('trigger','').strip(),null=True)
        log_def.save(using='write')
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html',locals())

 
@Route()
def log_remove(request, log_id=0):
    '''删除日志类型
    '''
    try:
        log_ids = request.REQUEST.getlist('id')
        LogDefine.objects.filter(id__in=log_ids).delete()
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html',locals())
 

@Route()
def log_syncdb(request, server_id=0):
    '''同步表界面
    '''
    err_msg = ''
    action = request.REQUEST.get('action','')
    server_ids = request.REQUEST.getlist('sid')
    if action == 'syncdb':
        return log_syncdb_do(request)
    if server_ids:
        if int(server_ids[0]) == 0:
            center_server = Server()
            center_server.id = 0
            center_server.name = '中央服'
            list_record = [center_server]
        else:
            list_record = Server.objects.using('read').filter(id__in=server_ids)
    else:
        err_msg = '没有选择服务器!'

    return render_to_response('log/log_sync_status.html', locals())


def sql_handle(sql,server_id):
    sql = sql.replace('{{server_id}}',str(server_id)).replace('{{server}}',str(server_id))
    return sql

def log_syncdb_do(request,server_id=0):
    '''同步数据库
    '''
    server_id = server_id or int(request.REQUEST.get('sid', '0'))
    is_ajax = request.is_ajax() or request.REQUEST.get('ajax','')
    err_msg = ''
    _r = {"code":1,"content":[]}
    sync_status = {}

    try:
        if server_id:
            is_center = False
            the_server = Server.objects.get(id=server_id)
            the_server.create_base_table()                          #创建数据库,创建player表,创建log基表
            conn = the_server.mysql_conn()
        else:
            is_center = True
            conn = Server.get_conn(0)
        
        table_status = {"tol_num":0,
                       "sync_num":0,
                       "already_num":0
                       }
        
        index_status = copy.deepcopy(table_status)
        
        status = LogDefine.Status.CENTER if is_center else LogDefine.Status.NORMAL
        cur = conn.cursor()
        log_defs = LogDefine.objects.filter(status=status)
        for log_def in log_defs:
            table_status["tol_num"] += 1
            create_tabls_sql = log_def.get_create_table_sql()
            try:
                cur.execute(create_tabls_sql) #同步表
                table_status["sync_num"] += 1
            except MySQLdb.Warning,e:
                table_status["already_num"] += 1
                
            for create_index_sql in log_def.get_create_index_sqls() : #同步索引
                index_status["tol_num"] += 1
                #print create_index_sql
                try:
                    cur.execute(create_index_sql)
                    index_status["sync_num"] += 1
                except MySQLdb.OperationalError,e:
                    index_status["already_num"] += 1  
                except:
                    err_msg = trace_msg()  
                    print trace_msg()  
        for log_def in log_defs:         #防止触发器引用没建的表,报错
            for other_sql in  log_def.get_other_sqls():      #其他sql语句
                other_sql = sql_handle(other_sql,server_id)
                try:
                    cur.execute(other_sql) 
                except MySQLdb.Warning,e:
                    pass
                except MySQLdb.OperationalError,e:
                    pass
                except:
                    print other_sql
                    err_msg = trace_msg()  
                    print err_msg
                
        _r['content'] += [table_status,index_status]
        if not err_msg : _r['code'] = 0
        conn.close()
    except Exception,e:
        err_msg = trace_msg()
        
    if is_ajax:
        _r['msg'] = err_msg
        render = HttpResponse(json.dumps(_r))
    else:
        render = render_to_response('feedback.html', locals())
    return render



@Route(r'^log/dbsql$')
@notauth
def log_dbsql(request):
    '''获取分服sql语句接口
    '''
    #根据服务器获取分服数据库所需的SQL结构表信息
    server_id = int(request.GET.get('server_id', '') or 0)
    is_truncate_table = request.REQUEST.get('truncate','') == 'true'
    if not server_id:
        return HttpResponse('服务器不存在，请求失败.')
    sqls = []
    the_server = Server()
    the_server.id = server_id
    sqls.append(the_server.get_base_database_sql())        #创建数据库
    sqls.append('USE %s;' % the_server.db_name)
    if is_truncate_table:
        '''清数据的接口
        '''
        sqls.extend( LogDefine.get_truncate_table_sqls() )
        sqls.append('truncate table player_%d;' % server_id)
    else: 
        sqls.extend(the_server.get_create_player_table_sqls()) #创建player_表
        sqls.extend(the_server.get_create_gang_table_sqls())   #创建gang_表
        sqls.append(the_server.get_drop_base_log_sql())        #先删除下log基表
        sqls.append(the_server.get_create_base_log_sql())      #创建log_x基表
        
        log_defs = LogDefine.objects.filter(status=LogDefine.Status.NORMAL)
        for log_def in log_defs:
                sqls.append(log_def.get_create_table_sql())
                for create_index_sql in log_def.get_create_index_sqls(): #同步索引
                    sqls.append(create_index_sql)  
        for log_def in log_defs:
            for other_sql in log_def.get_other_sqls(is_sql_file=True): #触发器
                sqls.append(sql_handle(other_sql,server_id))
    
    return HttpResponse('\n'.join(sqls))


@Route(r'^log/merge$')
@notauth
def merge_server(request):
    '''
    运维合服专用
    '''
    master_server = int(request.REQUEST.get('master',0))
    sub_server = request.GET.get('sub',[])
    if not master_server or not sub_server:
        return HttpResponse('没有母服或子服务器')
    default_module = {"1":[]}
    try:
        sub_server = json.loads(sub_server)
        sub_server.append(master_server)
        for sid in sub_server:
            if sid == master_server:
                server = Server.objects.filter(id=1000)
            else:
                server = Server.objects.filter(id=sid)
            if not server:
                return HttpResponse("没有id为1000的服务器！")
            server = server[0]
            _s = {}
            db_config = server.get_log_db_config()
            if db_config:
                _s["dbPort"] = db_config["port"]
                _s["serverType"] = 0 if sid >= 1000 else 1
                _s["dbIp"] = db_config["host"]
                _s["dbName"] = "ss_logic%s"%(master_server if sid == master_server else sid)
                _s["dbPassword"] = db_config["password"]
                _s["dbUser"] = db_config["user"]
                _s["serverId"] = int(sid)
            default_module["1"].append(_s)
        return HttpResponse(json.dumps(default_module))
    except BaseException as e:
        return HttpResponse("有错误:%s"%e)


# @Route(r'^logic/dbsql$')
# @notauth
# def logic_dbsql(request):
#     '''获取逻辑服sql语句接口
#     '''
#     #根据服务器获取分服数据库所需的SQL结构表信息
#     server_id = int(request.GET.get('server_id', '') or 0)
#     is_truncate_table = request.REQUEST.get('truncate','') == 'true'
#     if not server_id:
#         return HttpResponse('服务器不存在，请求失败.')

#---------------- old ------------------------------
def log_server(request, log_id=0):
    if log_id > 0 :
        log_def = LogDefine.objects.get(id=log_id)
    
    list_server = Server.get_server_list()
    
    parg = {}
    parg["list_server"] = list_server
    parg["log_def"] = log_def
    
    return render_to_response('log/log_server.html', parg)


def log_clear(request, server_id=0, log_type=0, clear_type=0):
    '''清除日志数据
    '''
    server_id = int(server_id)
    log_type = int(log_type)
    clear_type = int(clear_type)
    err_msg = ''
    if log_type > 0 :
        log_def = LogDefine.objects.get(id=log_type)
        try:
            if server_id > 0:
                try:
                    conn = Server.get_conn(server_id)
                except:
                    err_msg = '数据库链接出错!'
            else:
                conn = connection
            if clear_type == 0:
                sql = 'delete from log_%s' % log_def.key
            else:
                sql = 'drop table log_%s' % log_def.key
            cursor = conn.cursor()
            cursor.execute(sql)
            cursor.close()
        except Exception, e:
            print('clear data error:%s' % e)
    
    parg = {}
    parg["err_msg"] = err_msg
    
    return render_to_response('feedback.html', parg)

def sync_log_index(request, server_id=0):
    if server_id == 0:
        server_id = int(request.GET.get('server_id', '0'))
    
    log_list = []
    server_list = []
    if server_id == 0:
        log_list = LogDefine.objects.filter(status = LogDefine.Status.CENTER)
    else:
        server_list = Server.get_server_list()
        log_list = LogDefine.objects.filter(status = LogDefine.Status.NORMAL)
        
    return render_to_response('log/sync_log_index.html', {"server_id": server_id, "log_list": log_list, "server_list":server_list})



#过滤的索引名称
def pass_index_name(index_name):
    if index_name == 'PRIMARY':
        return True


def create_index(conn, index_name, table_name, column_name, save_path):
    sql_tmp = "CREATE INDEX %s ON %s (%s)"
    sql = sql_tmp % (index_name, table_name, column_name)
    if '' == save_path:
        cursor = conn.cursor()
        cursor.execute(sql)
    else:
        file_handler = open(save_path, "a")
        file_handler.write(sql + ';')
        file_handler.close()

def delete_index(conn, index_name, table_name, save_path):
    sql = "DROP INDEX %s ON %s" % (index_name, table_name)
    
    if '' == save_path:
        cursor = conn.cursor()
        cursor.execute(sql)
    else:
        file_handler = open(save_path, "a")
        file_handler.write(sql + ';')
        file_handler.close()


def get_table_index(conn, table_name):
    sql = " SHOW INDEX FROM %s " % table_name 
    cursor = conn.cursor()
    list_data = []
    try:
        cursor.execute(sql)
        list_data = cursor.fetchall()
    except:
        return list_data
    return list_data

def log_syncdb_data(request, server_id=0):
    '''同步创建表
    '''
    err_msg = ''
    
    server_id = int(server_id)
    if 0 == server_id:
        server_id = int(request.GET.get('server_id', 0))
    
    if 0 == server_id:
        server_id = int(request.POST.get('server_id', 0))
    
    if server_id > 0:
        try:
            conn = Server.get_conn(server_id)
        except:
            err_msg = '数据库链接出错!'
    else:
        conn = connection
        
    if err_msg != '':
        parg = {}
        parg["err_msg"] = err_msg
        return render_to_response('feedback.html', parg)
    cursor = conn.cursor()
    is_reload = True
    page_size = 50
    try:
        #sql = 'select id,log_result from log_create_role where log_channel=0 limit %d'%page_size
        sql = 'select id,log_result from log_create_role where log_channel=0 and log_result>0 limit %d' % page_size
        print(sql)
        cursor.execute(sql)
        list_record = cursor.fetchall()
        if len(list_record) < 10:
            is_reload = False
        for item in list_record:
            the_user = User.objects.get(id=item[1])
            if the_user.channel_key != '':
                the_channel = Channel.objects.get(channel_key=the_user.channel_key)
                sql = 'update log_create_role set log_channel=%d where id=%d' % (the_channel.id, int(item[0]))
                print(sql)
                cursor.execute(sql)
    except Exception, e:
        print('syncdb data has error', e)

    #cursor.close()  
    
    page_num = int(request.GET.get('page_num', '0'))
    sync_num = page_num * page_size
    page_num += 1
    
    parg = {}
    parg["server_id"] = server_id
    parg["is_reload"] = is_reload
    parg["sync_num"] = sync_num
    parg["page_num"] = page_num
    
    return render_to_response('log/log_sync_data.html', parg)



def log_syncdb_player(request, server_id=0):
    from pymongo import Connection
    server_id = int(server_id)
    err_msg= ''
    if server_id == 0:
        err_msg = '参数错误!'
        return render_to_response('log/log_sync_player.html', locals())
    try: 
        the_server = Server.objects.get(id=server_id)
        the_db_config = json.loads(the_server.log_db_config)
        conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], passwd=the_db_config['password'], db=the_db_config['db'], charset='utf8')
        cursor = conn.cursor()
    except:
        err_msg = 'mysql数据库链接出错!'
        return render_to_response('log/log_sync_player.html', locals())
    if True:
#    try:
        mg_conn = Connection(the_db_config['host'], the_db_config.get('mongo_port', 27017))
        mg_db = mg_conn['sid%d' % server_id]
        mg_player = mg_db['sg.player']
#    except:
#        err_msg = 'mongo数据库链接出错!'
#        return render_to_response('log_sync_player.html',locals())
    
    pos = int(request.GET.get('pos', 0))
    if pos == 0:
        mg_count = mg_player.count()
        sql = 'select count(distinct log_user) from log_create_role'
        
        cursor.execute(sql)
        mysql_count = int(cursor.fetchone()[0])
            
        if mg_count <= mysql_count:
            err_msg = '数据总数量一致,无需再次同步!'
            return render_to_response('log/log_sync_player.html', locals())
    page_size = 100
    list_player = mg_player.find({"player_id":{"$gt":pos}}, {"player_id":1, "uid":1, "nn":1}).sort("player_id", 1).limit(page_size)
    begin_player = 0
    last_player = 0
    is_reload = True
    total_record = 0
    list_record = []
    for item in list_player:
        try:
            list_record.append(item)
            last_player = item['player_id']
            if begin_player == 0:
                begin_player = last_player
            total_record += 1
        except:
            print('has unkonw error')
        #print(last_player)
    pos = last_player
    if pos == 0:
        is_reload = False
    sql = 'select count(distinct log_user) from log_create_role where log_user between %d and %d' % (begin_player, last_player)
    cursor.execute(sql)
    mysql_count = int(cursor.fetchone()[0])
    #print(sql,total_record,mysql_count)
    sync_list = []
    if mysql_count != total_record:
        for item in list_record:
            sql = 'select count(0) from log_create_role where log_user=%d' % item['player_id']
            cursor.execute(sql)
            total_record = int(cursor.fetchone()[0])
            #print(sql,total_record)
            if total_record == 0:
                sync_list.append(str(item['player_id']))
                try:
                    sql = 'insert into log_create_role(log_type,log_data,log_server,log_user,log_result,log_time,f1)values(6,0,%d,%d,%d,now(),"%s")' % (server_id, item['player_id'], item['uid'], item['nn'].replace('\\', '\\\\').encode('utf-8'))
                    #print(sql)
                    cursor.execute(sql)
                except Exception, e:
                    print('has error sync role %d,%s' % (item['player_id'], e))
        sync_list = u'已同步%s' % ','.join(sync_list)
    else:
        sync_list = u'无需同步'
    conn.close()
    mg_conn.close()
    
    parg = {}
    parg["total_record"] = total_record
    parg["server_id"] = server_id
    parg["pos"] = pos
    parg["sync_list"] = sync_list
    parg["err_msg"] = err_msg
    parg["is_reload"] = is_reload
    
    return render_to_response('log/log_sync_player.html', parg)


#日志表结构信息
def table_info(request):
    
    log_id = int(request.GET.get('log_id', '0'))
    server_id = int(request.GET.get('server_id', '0'))
    
    if 0 == server_id:
        server_id = int(request.POST.get('server_id', '0'))
    
    log_list = []
    if 0 == server_id:
        log_list = LogDefine.objects.filter(status = LogDefine.Status.CENTER).all()
    else:
        log_list = LogDefine.objects.filter(status = LogDefine.Status.NORMAL).all()
    
    server_list = Server.get_server_list()
    
    parg = {}
    
    if 0 != log_id and -1 != server_id:
        if 0 == LogDefine.objects.filter(id = log_id).count():
            return HttpResponse('请选择日志表')
        
        log_def = None
        for item in log_list:
            if item.id == log_id:
                log_def = item
        
        if None == log_def:
            return HttpResponse('请选择日志表')
        
        query_sql = 'show index from log_%s' %  log_def.key
        conn = conn_switch(server_id)
        cursor = conn.cursor()
        cursor.execute(query_sql) 
        list_data = cursor.fetchall()
        #raise Exception, query_sql
        conn.close()
        
        parg['log_def'] = log_def
        parg['list_data'] = list_data
    
    parg['log_id'] = log_id
    parg['log_list'] = log_list
    parg['server_list'] = server_list
    parg['server_id'] = server_id
    
    return render_to_response('log/table_info.html', parg)


def del_index(request):
    
    if not request.admin.is_root:
        return HttpResponse('权限不足')
    
    log_key = request.GET.get('log_key', '')
    index_name = request.GET.get('index_name', '')
    
    server_id = int(request.GET.get('server_id', '-1'))
    
    if -1 == server_id:
        return HttpResponse('没有选择服务器')
    
    if log_key == '' or index_name == '':
        return HttpResponse('没有选择日志表  或  索引')
    
    if not check_table_is_log(log_key):
        return HttpResponse('非法操作，该表不是日志表')
    
    sql = 'drop index %s on log_%s;' % (index_name, log_key)
    
    conn = conn_switch(server_id)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.close()
    
    return table_info(request)
    
    

def check_table_is_log(log_key):
    if 0 == LogDefine.objects.filter(key = log_key).count():
        return False
    return True
    
def conn_switch(server_id):
    conn = None
    if 0 != server_id:
        conn = Server.get_conn(server_id)
    else:
        conn = connections['write']
    return conn
 
# 删除日志数据   
def log_data_delete(request, log_type):
    
    log_type = int(log_type)
    
    sdate = request.GET.get('sdate','')
    edate = request.GET.get('edate','')
    server_id = int(request.GET.get('server_id','0'))
    
    delete_date = ''
    size = 300
    msg = ''

    if server_id > 0:
        delete_server = " AND `log_server` = %d " % server_id
    else:
        msg = '服务器ID不能为空！'  
            
    if sdate != '' and edate != '':
        delete_date +=  "`log_time` >='%s' AND `log_time` <= '%s' " %(sdate, edate) 
        print delete_date
        
    else:
        msg = '时间不能为空！'     
        
    is_finish = 0
    record = 0
    if log_type > 0 and msg == '':
        print 'yes'
        log_def = LogDefine.objects.get(id=log_type)
        try:
            if server_id > 0:
                try:
                    conn = Server.get_conn(server_id)
                except:
                    msg = '数据库链接出错!'
                    print msg
            else:
                conn = connection
            cursor = conn.cursor()
            
            record_sql = "SELECT COUNT(*) FROM `log_%s` WHERE %s %s"%(log_def.key, delete_date, delete_server)
            print record_sql
            cursor.execute(record_sql)
            record = int(cursor.fetchone()[0])
            if record > 0:
                sql = 'DELETE FROM `log_%s` WHERE %s %s LIMIT %d' % (log_def.key, delete_date, delete_server,size)
                is_finish = cursor.execute(sql)
            else:
                is_finish = 0
            cursor.close()
        except Exception, e:
            print('clear data error:%s' % e)    
            msg = '%s'%e
    return HttpResponse('{"is_finish":%d,"msg":"%s","record":"%s"}'%(is_finish,msg, record))
