# -*- coding: utf-8 -*-
#
# 查询类相关
#
# django 常用导入
# =========================================
from django.core.urlresolvers import reverse
from django.db import connection, connections
from django.utils.html import conditional_escape
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, HttpResponseRedirect
from django.views.generic import ListView, View
# ==========================================

from settings import TEMPLATE_DIRS, DEBUG
from util import trace_msg
from models.log import Log, LogDefine, DictDefine, DictValue
from models.menu import Menu
from models.query import Query
from views.base import getConn, md5, GlobalPathCfg
from views.log.exprot_file import ExportFile, QueryExprot
from util import filter_sql
from cache.memcached_util import MemcachedUtil, clear_cache, CACHE_TYPE
from util.cache import cache_func, clear_cache, CACHE_TYPE
import datetime, os
from models.center import Server
from models.server import Group
from models.query import QueryAnalysis, SqlAnalysis
from urls.AutoUrl import Route
from views.base import notauth
from views.widgets import get_agent_channels_dict, get_group_servers_dict, get_group_channels_dict, groups_servers
from models.channel import Channel
import json, time
from django.utils.datastructures import SortedDict


def get_field_id_for_dict(field_dict, value):
    _r = value
    for k, v in field_dict.iteritems():
        if value.strip() == v:
            _r = k
            break
    return str(_r)


@Route('^interface/query/(\S+)$')
@notauth
def interface(request, query_name, template='query_csv'):
    '''查询接口
    '''
    if not hasattr(request, 'admin'):
        pass

    return query_view(request, query_name=query_name, is_query_do=True)


@Route('^query/widget/(\S+)')
@Route('^query/widget[/]?$')
def query_widget(request, query_name):
    return query_view(request, query_name=query_name, is_query_do=False, template='query/query_widget.html')


# def get_group_channels_dict():
#     """在分区等业务重构后，渠道不在隶属于平台，改为隶属于分区"""
#
#     # 查出分区的查询集
#     groups = Group.objects.all()
#
#     # 查出每个分区对应的渠道查询集，并组成字典
#     dic = {}
#     for group in groups:
#         channels = group.channel.all()
#         dic[group] = channels
#
#     # 返回字典
#     return dic


def query_view(request, query_name='', query_model=None, is_query_do=False, list_data_handle=False,
               template='query/query_view.html'):
    '''查询视图,request 传入
    @param query_name:查询名称
    @param is_query_do: 是否执行查询
    '''
    now = datetime.datetime.now()
    _g = request.REQUEST.get
    _gl = request.REQUEST.getlist

    query_name = query_name or _g('query_name', '') or _g('name', '')
    print 'NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN', query_name
    query_id = int(_g('query_id', '') or _g('qid', '') or 0)
    # 不传id则使用查询名
    if query_id:
        the_query = Query.objects.get(id=query_id)
    elif query_name:
        the_query = Query.objects.using('read').get(name=query_name)
    elif query_model:
        the_query = query_model

    else:
        return HttpResponse('没有 ID[%s] 或者  [%s] 的查询' % (query_id, query_name))

    params = dict(request.GET)
    params.update(dict(request.POST))  # 必须为POST
    # print params
    log_def = the_query.log_def
    query_analysis = QueryAnalysis(the_query, params)
    is_center_query = the_query.is_center_query
    is_export = _g('is_export', 'False') == 'true'

    if is_export:  # 导出
        return query_export_do(request, query_analysis)
    if is_query_do or request.method == 'POST' or request.REQUEST.get('query_do') or request.GET.get('template', ''):
        return query_do(request, query_analysis, list_data_handle=list_data_handle)

    same_log_key_query_list = Query.objects.filter(log_key=the_query.log_key)  # 查询的表定义
    field_configs = SortedDict()
    conditions_configs = []

    for cloumn in the_query.selects:
        field_config_item = the_query.field_config.get(cloumn, {})
        field_configs[cloumn] = field_config_item

    for k in the_query.field_config.keys():
        field_config_item = the_query.field_config[k]
        if field_config_item.get('single', ''):
            default_value = DictDefine.get_dict_for_key(field_config_item.get('dict', ''))
        else:
            default_value = params.get(field_config_item.get('name', ''), [''])[0]
        field_config_item['value'] = default_value
        order_num = int(field_config_item.get('order_num', 0) or 99)
        conditions_configs.append((k, field_config_item, order_num))

    conditions_configs.sort(key=lambda x: x[2])

    sd = request.REQUEST.get('sd', '') or now.strftime('%Y-%m-%d 00:00:00')
    ed = request.REQUEST.get('ed', '') or now.strftime('%Y-%m-%d 23:59:59')

    has_sd = query_analysis.has_mark('sd')
    has_ed = query_analysis.has_mark('ed')

    sdate = request.REQUEST.get('sdate', '') or now.strftime('%Y-%m-%d 00:00:00')
    edate = request.REQUEST.get('edate', '') or now.strftime('%Y-%m-%d 23:59:59')

    has_sdate = query_analysis.has_mark('sdate')
    has_edate = query_analysis.has_mark('edate')
    has_channel = query_analysis.has_mark('channel_id') or query_analysis.has_mark('channel_ids')
    has_server = query_analysis.has_mark('server_id') or query_analysis.has_mark('server_ids')
    has_server = has_server or not is_center_query
    has_neibuhao = query_analysis.has_mark('neibuhao')
    has_platform = query_analysis.has_mark('platform_id') or query_analysis.has_mark('platform_ids')
    has_conditions = query_analysis.has_conditions()

    if request.admin.is_agent and not has_channel:
        return render_to_response('block.html', {"err_msg": "'此查询非法!'"})

    plugin_templates = []
    if the_query.template_name:
        for template_name in the_query.template_name.split(','):
            if template_name.strip():
                if template_name == "邮件列表":
                    dj = json.dumps(eval(DictValue.objects.get(dict_id=88).json_dict))

                plugin_templates.append('query/plugins/%s.html' % template_name)

    if has_server:
        # group_servers_dict = get_group_servers_dict(request)
        group_servers_dict = groups_servers(request)
    select_server_ids = [int(sid) for sid in request.REQUEST.getlist('sid') if str(sid).isdigit()]
    if has_channel:
        group_channels_dict = get_group_channels_dict()
    if has_platform:
        platforms = request.admin.get_resource('platform')
    server_id = int(request.REQUEST.get('server_id', 0))
    return render_to_response(template, locals())


def query_export_do(request, query_analysis):
    '''查询导出文件
    '''

    _g = request.REQUEST.get
    _gl = request.REQUEST.getlist
    export_key = _g('export_key', '')
    is_finish = _g('is_finish', '')  # 完成标记 合并文件
    export_type = int(_g('export_type', '') or 0)
    q_server_id = int(request.REQUEST.get('server_id', '') or 0)
    page_num = int(_g('page_num', '') or 0) or 1  # 页码
    file_type = request.REQUEST.get('file_type', '')
    page_size = 1000
    request.POST.setlist('page_size', [page_size])

    fields = query_analysis.query.selects
    is_summary = _g('is_summary', '')  # 汇总

    query_exprot = QueryExprot(export_key, export_type)
    if is_finish:  # 完成,文件合并
        merge_file_name = query_exprot.merge_files(fields)
        _r = {"url": '/static/export/query/%s' % merge_file_name, "export_key": query_exprot.export_key,
              'export_type': query_exprot.export_type}
    elif is_summary:  # 文件汇总
        merges = [int(x) for x in request.REQUEST.getlist('merges')]
        done_summary_file_name = query_exprot.summary_file(merges)
        new_url = '/static/export/query/%s' % done_summary_file_name
        return HttpResponseRedirect(new_url)
    else:
        total_record, list_data = query_do(request, query_analysis, built_in=True)
        export_file_name = '%s_%s' % (query_analysis.query.name, q_server_id)
        _r = query_exprot.gene_file(export_file_name, list_data, fields, page_num, page_size, total_record)
    _r["code"] = 0
    _r["server_id"] = q_server_id
    return HttpResponse(json.dumps(_r))


def query_do(request, query_analysis, built_in=False, list_data_handle=None):
    '''执行查询
    '''
    template_name = request.REQUEST.get('template', '') or 'json'
    now = getattr(request, '_start_time', time.time())
    _g = request.REQUEST.get
    _gl = request.REQUEST.getlist
    err_msg = ''

    if _gl('server_id'):
        server_id = int(_gl('server_id')[0] or 0)
    else:
        server_id = int(request.REQUEST.get('server_id', '') or 0)

    params = (request.GET)
    if params.has_key('server_id'):
        server_id = int(params['server_id'])

    use_neibuhao = request.REQUEST.get('use_neibuhao', 'false') == 'true'  # 内部号过滤
    total_record = total_page = 0
    page_num = int(_g('page_num', '') or 0) or 1  # 页码
    page_size = int(_g('page_size', '') or 0) or 50  # 页数
    session_id = request.REQUEST.get('session_id', '')

    is_ajax = request.is_ajax() or _g('ajax', False)
    list_data = []
    tfoot_data = []
    query_sql = count_sql = ''
    try:
        if not query_analysis.query.is_center_query:
            if server_id:
                try:
                    server_model = Server.objects.get(id=server_id)
                    conn = server_model.mysql_conn()
                    master_id = server_model.master_server.id
                    query_analysis.params.update({"master_id": [master_id]})  # 传母服id
                    query_analysis.params.update({"master_db": [server_model.master_server.db_name]})  # 传母服数据库名
                    query_analysis.params.update({"server_name": [server_model.name]})  # 传服务器名
                except:
                    err_msg = '数据库链接出错!'
            else:
                err_msg = '没有服务器ID'
        else:
            conn = connections['read']

        if use_neibuhao:  # 设置内部号
            query_analysis.set_neibuhao()

        # 限制渠道查询 不是root的都需要限制,渠道用户如果没有channel_ids标记则提示错误
        if not request.admin.is_root:
            if query_analysis.has_mark('platform_ids'):
                # 获取请求参数 ,如果没有就用这个用户所有的权限
                old_platform_ids = query_analysis.params.get('platform_id', [])
                new_platform_ids = old_platform_ids or list(
                    request.admin.get_resource('platform').values_list('key', flat=True))
                query_analysis.params['platform_id'] = new_platform_ids or ['-99']
                # 如果是平台的查询就不需要限制服务器和渠道了
            else:
                if query_analysis.has_mark('server_ids'):
                    old_server_ids = query_analysis.params.get('server_id', [])
                    new_server_ids = request.admin.get_resource_ids('server', old_server_ids)
                    new_server_ids = new_server_ids or [-99]
                    new_server_ids.append(0)  # 激活数据服务器是0的
                    query_analysis.params['server_id'] = new_server_ids

                if query_analysis.has_mark('channel_ids'):
                    old_channel_ids = query_analysis.params.get('channel_id', [])
                    new_channel_ids = request.admin.get_resource_ids('channel', old_channel_ids)
                    query_analysis.params['channel_id'] = new_channel_ids or [-99]
                elif request.admin.is_agent:
                    err_msg = '此查询未包涵渠道过滤条件!'

        if not err_msg:
            fields = query_analysis.query.selects
            query_analysis.set_limit(page_size, page_num)
            query_analysis.query_sql_handle()

            # 设置排序
            sort_type = _g('sort_type', '')
            sort_fields_index = int(_g('sort_index', '') or -1)
            if sort_fields_index >= 0 and len(fields) >= sort_fields_index:
                sort_field_name = fields[sort_fields_index]
                sort_key = query_analysis.query.field_config.get(sort_field_name, {}).get('name', '')
                if sort_key and sort_type:
                    query_analysis.set_order(sort_key, sort_type)

            count_sql = query_analysis.get_count_sql()
            query_sql = query_analysis.get_query_sql()

            fields = query_analysis.query.selects  # 查询的表头

            print '--------------------------》》》》'
            print query_sql
            print '--------------------------------'
            # print count_sql

            cache_time = int(query_analysis.query.cache_validate)
            count_sql_key = md5('%s_%s' % (count_sql, server_id))
            cursor = conn.cursor()
            total_record, result_cache_time = cache_func(count_sql_key, get_query_result_cout, (conn, count_sql),
                                                         timeout=cache_time)

            if total_record:
                query_sql_key = md5('%s_%s' % (query_sql, server_id))
                total_page = total_record / page_size
                if total_record % page_size != 0:
                    total_page += 1
                list_data, result_cache_time = cache_func(query_sql_key, get_query_result, (conn, query_sql),
                                                          timeout=cache_time)
                list_data, result_cache_time = cache_func('display_%s' % query_sql_key, query_display_process,
                                                          (query_analysis, list_data, page_num, page_size),
                                                          timeout=cache_time)
                tfoot_sql = query_analysis.get_tfoot_sql()

                if tfoot_sql:
                    tfoot_sql_key = md5('%s_%s' % (tfoot_sql, server_id))
                    tfoot_data, result_cache_time = cache_func('tfoot_%s' % tfoot_sql_key, get_query_result,
                                                               (conn, tfoot_sql), timeout=cache_time)
    except Exception, e:
        err_msg = trace_msg()
        print err_msg
        err_msg = '%s\nthe_sql:%s' % (err_msg, query_sql)

    if list_data_handle and callable(list_data_handle):
        list_data = list_data_handle(list_data)
    if built_in:  # 导出
        return (total_record, list_data)

    exec_time = '%.3f' % (time.time() - now)
    response = render_to_response('query/return/%s.html' % template_name, locals())
    response['Order-Record-Count'] = total_record
    response['Page-Num'] = page_num
    response['Page-Size'] = page_size
    response['Total-Page'] = total_page
    return response


def query_clear_cache(request):
    '''清除查询缓存
    '''
    clear_cache(CACHE_TYPE.LOG_CACHE)
    return HttpResponse('成功!')
    # return render_to_response('feedback.html')


def get_query_result_cout(conn, sql):
    return int(get_query_result(conn, sql)[0][0])


def get_query_result(conn, sql):
    cursor = conn.cursor()
    setattr(cursor, 'use_cache', False)  # 设置一个属性给缓存中间件使用
    cursor.execute(sql)
    _r = cursor.fetchall()
    return _r


def query_display_process(query_analysis, list_data, page_num, page_size):
    '''值定义处理
    '''
    fields = query_analysis.query.selects  # 查询的表头
    field_configs = []
    for field_name in fields:
        field_config = query_analysis.query.field_config.get(field_name, {})
        field_config['field_name'] = field_name
        dict_key = field_config.get('dict', '')
        value_defs = DictDefine.get_dict_for_key(dict_key, reverse=False)
        field_config['value_defs'] = value_defs
        field_configs.append(field_config)
        if field_name == '排名':
            field_config['rank'] = True
    new_list_data = []
    list_data = list(list_data)
    n = (page_num - 1) * page_size if page_num > 1 else 0
    for row in list_data:
        item = list(row)
        item_len = len(item)
        n += 1
        for i, _ in enumerate(fields):
            if item_len > i:
                field_config = field_configs[i]
                if field_config.get('rank', False):
                    item[i] = n
                else:
                    item[i] = display_format(field_config, item[i])
        new_list_data.append(item)

    return new_list_data


def display_format(field_config, value):
    '''转格式
    '''
    field_name = field_config.get('field_name', '')
    def_values = field_config['value_defs']

    if isinstance(value, (datetime.datetime, datetime.date)):
        if '时间' in field_name:
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        elif '日期' in field_name:
            value = value.strftime('%Y-%m-%d')
        elif '小时' in field_name:
            value = value.strftime('%Y-%m-%d %H')
        else:
            value = value.strftime('%Y-%m-%d %H:%M:%S')
    elif value != None and def_values:
        tmp_value = def_values.get(value,
                                   def_values.get(unicode(value), value)
                                   )
        if field_config.get('merge_value', False):
            value = '%s(%s)' % (tmp_value, value)
        else:
            value = tmp_value

    return value


def query_list(request, log_key=''):
    '''查询列表
    '''
    list_model = []
    log_key = request.REQUEST.get('log_key', '')

    if log_key:
        list_model = Query.objects.using('read').filter(log_key=log_key).order_by("id")
    else:
        list_model = Query.objects.using('write').all().order_by("id")

    logDefine_list = []
    _logDefine_list = LogDefine.objects.using('read').all()
    logDefineIdName = {}
    for logDefineItem in logDefine_list:
        logDefineIdName[logDefineItem.id] = logDefineItem.key

    allow_menu_keys = request.allow_menu.keys()
    for log_def in _logDefine_list:
        log_def.name = log_def.name.rstrip('流水')
        if '[%s]' % log_def.name in allow_menu_keys or request.admin.is_root:
            logDefine_list.append(log_def)

    for item in list_model:
        item.log_typeName = logDefineIdName.get(item.log_type, '')
    return render_to_response('query/query_list.html', locals())


def query_edit(request, query_id=0, log_type=0):
    '''查询类编辑
    '''
    if request.REQUEST.get('edit_type', ''):
        return QueryTemplateEdit(request)()
    is_copy = request.REQUEST.get('is_copy', '')
    query_id = int(request.REQUEST.get('query_id', '') or 0)
    log_key = request.REQUEST.get('log_key', '')

    if query_id:
        model = Query.objects.using('read').get(id=query_id)
        if model.cache_validate == None:
            model.cache_validate = 0
        if is_copy:
            model.id = 0
            model.name = '%s-copy' % model.name
    else:
        model = Query()
        model.id = query_id
        model.name = ''
        model.cache_validate = 0
        model.log_key = log_key

    log_defs = LogDefine.objects.using('read').all()
    return render_to_response('query/query_edit.html', locals())


def query_save(request, query_id=0):
    _g = request.REQUEST.get
    query_id = int(_g('query_id', '') or 0)

    if query_id:
        model = Query.objects.get(id=query_id)
    else:
        model = Query()

    err_msg = ''
    model.log_type = 0
    model.log_key = request.REQUEST.get('log_key', '0')
    model.select = request.REQUEST.get('select', '')
    model.remark = request.REQUEST.get('remark', '')
    model.name = request.REQUEST.get('name', '')
    model.where = request.REQUEST.get('where', '')
    model.group = request.REQUEST.get('group', '')
    model.order = request.REQUEST.get('order', '')
    model.cache_validate = int(request.REQUEST.get('cache_valid', 0))
    model.order_type = int(request.REQUEST.get('order_type', '0'))
    model.sql = request.REQUEST.get('sql', '')
    model.other_sql = request.REQUEST.get('other_sql', '')
    model.field_config = request.REQUEST.get("field_config", "")
    model.template_name = request.REQUEST.get('template_name', '')
    try:
        save_id = int(_g('save_id', '') or 0)
        if save_id != query_id and Query.objects.filter(id=save_id):
            err_msg = 'ID 已经存在'
        else:
            if save_id:
                model.id = save_id
                query_id = save_id
            model.save(using='write')
    except Exception, e:
        err_msg = trace_msg()
        print('query save error:', e)
    return render_to_response('feedback.html', locals())


def query_remove(request, query_id=0):
    _g = lambda x, y='': request.POST.get(x, request.GET.get(x, y))
    model_id = int(query_id)

    if model_id == 0:
        model_id = int(_g('query_id', '0'))

    if model_id > 0:
        model = Query.objects.get(id=model_id)

        model.delete(using='write')
    return render_to_response('feedback.html')


class QueryTemplateEdit(object):
    __static_path = GlobalPathCfg().get_static_folder_path()
    __template_dir = TEMPLATE_DIRS[0]

    def __init__(self, request):
        self.r = request
        self.edit_type = self.r.REQUEST.get('edit_type', 'query')
        self.template_name = request.REQUEST.get('template_name')
        self.file_path = self.get_path()
        self.action = self.r.REQUEST.get('action')

    def get_path(self):
        return os.path.join(self.__template_dir, 'query', 'plugins', '%s.html' % self.template_name)

    def save(self, data):
        with open(self.file_path, 'wb') as f:
            f.write(data)

    def __call__(self):
        template_name = self.template_name
        edit_type = self.edit_type
        if self.action == 'save':
            file_content = self.r.REQUEST.get('code', '')
            self.save(file_content)
        elif os.path.exists(self.file_path):
            with open(self.file_path, 'rb') as f:
                file_content = f.read()
        else:
            file_content = ''
        return render_to_response('query/query_template_edit.html', locals())
