#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from .base import GMProtocol
from django.shortcuts import render_to_response
from views.base import get_server_list
from django.http import HttpResponse
from urls.AutoUrl import Route
from views.widgets import get_group_servers_dict
from util import datetime_to_timestamp
from util import trace_msg


@Route()
def shop_daily_list(request):
    '''
    每日限购列表
    '''
    page_size = 15
    page_sum = 0
    context = {}

    server_id = int(request.GET.get('server_id', 0))
    page_num = int(request.GET.get('page_num', '1'))
    page_num = 1 if page_num < 1 else page_num
    total_record = 0

    the_user = request.admin
    server_list = the_user.get_resource("server").all()
    if len(server_list) == 0:
        server_list = get_server_list()

    if server_list.__len__() == 0:
        return HttpResponse("没有服务器可管理")

    server_id = server_list[len(server_list) - 1].id if server_id <= 0 else server_id
    server_shop_list = {}
    server_shop_list[server_id] = []
    while True:
        try:
            gmp = GMProtocol(server_id)
            _server_shop_list, page_sum = gmp.get_shop_list(page_num)
            server_shop_list[server_id].extend(_server_shop_list)
            total_record = page_sum * page_size
            break
            # _server_shop_list, page_sum = gmp.get_shop_list(page_num)
            # for i in _server_shop_list:
            #     if i[0] > 10000:
            #         server_shop_list[server_id].append(i)
            # total_record = page_sum * page_size
            # if len(server_shop_list[server_id]) or page_num > page_sum:
            #     break
            # else:
            #     page_num += 1
        except:
            context['err_msg'] = trace_msg()
            break

    context['server_list'] = server_list
    context['server_id'] = server_id
    context['server_shop_list'] = server_shop_list

    context['page_num'] = page_num
    context['page_size'] = page_size
    context['total_record'] = total_record

    template_path = 'game/shop_daily_list.html'
    return render_to_response(template_path, context)


def convert_res_info(res_desc, level_ratio):
    import copy
    res_info = None
    if level_ratio:
        res_info = copy.deepcopy(res_desc)
        for i in res_info:
            for j in level_ratio:
                if j[1] and i['aID'] == j[0]:
                    i['x'] = j[1]
    return res_info


@Route()
def shop_daily_edit(request):
    '''
    每日限购编辑
    '''
    MIN_ITEM_ID = 10000

    item_id = int(request.GET.get('item_id', 0))
    server_id = int(request.GET.get('server_id', 0))
    page_num = int(request.GET.get('page_num', 1))

    if item_id and item_id <= MIN_ITEM_ID:
        return HttpResponse("无法修改本地数据（商品ID < 10000）")

    item = []
    server_time = None
    res_info = None
    if item_id and server_id:
        try:
            gmp = GMProtocol(server_id)
            server_time = gmp.query_server_time()[0]
            shop_list, page_sum = gmp.get_shop_list(page_num)
            item = [i for i in shop_list if i[0] == item_id][0]
            res_info = convert_res_info(item[14], item[16])
        except Exception, e:
            err_msg = trace_msg()

    context = {}
    context["item_id"] = item_id
    context["item"] = item
    context["res_info"] = res_info
    context["server_id"] = server_id
    context["server_time"] = server_time
    context["group_servers_dict"] = get_group_servers_dict(request)
    context["select_server_ids"] = [server_id]

    template_path = 'game/shop_daily_edit.html'
    return render_to_response(template_path, context)


@Route()
def shop_daily_save(request):
    import urllib
    '''
    每日限购保存
    '''
    MIN_ITEM_ID = 10000

    server_id = int(request.GET.get('server_id', 0))
    usm = request.admin
    server_ids  = request.POST.getlist('server_id')
    server_ids  = list(set([int(i) for i in server_ids]))

    item_id     = request.POST.get('item_id', 0)
    item_name   = request.POST.get('item_name', '')
    item_desc   = request.POST.get('item_desc', '')
    # 处理 % 符号
    item_desc   = urllib.quote(item_desc.encode('utf-8'))
    item_type   = int(request.POST.get('item_type', 0))
    content     = int(request.POST.get('content', 0))
    currency    = int(request.POST.get('currency', -1))
    tag         = request.POST.get('tag', '')
    discount    = int(request.POST.get('discount', 10))
    price       = float(request.POST.get('price', 0))
    limit_num   = int(request.POST.get('limit_num', 0))
    limit_vip   = int(request.POST.get('limit_vip', 0))
    limit_rank  = int(request.POST.get('limit_rank', 0))
    begin_time  = request.POST.get('begin_time', '0')
    end_time    = request.POST.get('end_time', '0')

    reward_desc = json.loads(request.POST.get('reward_desc', ''))
    output_path = request.POST.get('output_path', '')

    level_ratio = json.loads(request.POST.get('level_ratio', ''))
    res_info = convert_res_info(reward_desc, level_ratio)

    if begin_time and end_time:
        begin_time = datetime_to_timestamp(begin_time)
        end_time = datetime_to_timestamp(end_time)
    elif not begin_time and not end_time:
        begin_time = 0
        end_time = 0
    else:
        return HttpResponse("日期错误")

    ishot = False
    if tag and tag == "ishot":
        ishot = True
        discount = 10
    elif discount not in range(1, 11):
        return HttpResponse('折扣数据非法')

    item = [None, item_name, item_desc, content, currency, ishot, price,
            item_type, discount, limit_num, limit_vip, limit_rank,
            begin_time, end_time, reward_desc, output_path, level_ratio]

    allow_create = True
    #  权限判断   //如果不是管理员账号
    if not usm.is_manager:
        user_server_list = usm.get_resource('server').all()  # 获取当前登陆的管理员账号有权限管理的服务器列表
        user_server_id = []
        for user_server in user_server_list:
            user_server_id.append(user_server.id)

    if not allow_create:
        return HttpResponse('没有权限添加')


    if server_ids:
        for new_server_id in server_ids:
            gmp = GMProtocol(new_server_id)
            if new_server_id == server_id and item_id:
                item_id = int(item_id)
            else:
                # 添加商品ID
                _s, _p = gmp.get_shop_list(1)
                shop_list, _p = gmp.get_shop_list(_p)
                item_ids = [i[0] for i in shop_list]
                item_id = max(max(item_ids), MIN_ITEM_ID) + 1
            item[0] = item_id
            msg = [item, ]
            try:
                result = gmp.set_shop_list(msg)
            except:
                return HttpResponse('{"code":1, "data": "添加出错"}')
            else:
                if len(result) > 1 and not result[1]:
                    return HttpResponse('{"code":1, "data": "添加出错"}')

    server_time = None
    if server_id != 0:
        gmp = GMProtocol(server_id)
        server_time = gmp.query_server_time()[0]

    template_path = 'game/shop_daily_edit.html'
    context = {}
    item[2] = urllib.unquote(item[2])
    context["item"] = item
    context["item_id"] = item_id
    context["res_info"] = res_info
    context["server_id"] = server_id
    context["server_time"] = server_time
    context["group_servers_dict"] = get_group_servers_dict(request)
    context["select_server_ids"] = server_ids

    ajax = request.GET.get('ajax', '')
    if ajax:
        return HttpResponse('{"code":0}')
    return render_to_response(template_path, context)


@Route()
def shop_daily_remove(request):
    '''
    删除商品
    '''
    item_id = int(request.GET.get('item_id', 0))
    server_id = int(request.GET.get('server_id', 0))
    if item_id and server_id:
        try:
            msg = [[item_id, True], ]
            gmp = GMProtocol(server_id)
            result = gmp.set_shop_list(msg)
        except:
            return HttpResponse('删除出错')
        else:
            if len(result) > 1 and not result[1]:
                return HttpResponse('删除出错')

    ajax = request.GET.get('ajax', '')
    if ajax:
        return HttpResponse('{"code":0}')
    return render_to_response('feedback.html')

@Route()
def flash_sale_pilot(request,template_path = 'game/flash_sale_pilot.html'):
    '''限时抢购武将
    '''
    server_ids = request.POST.getlist('server_id')
    server_ids = list(set(server_ids)) if server_ids else []
    server_ids = [int(i) for i in server_ids]
    result_dict = {}

    if server_ids:
        for sid in server_ids:
            try:
                gmp = GMProtocol(sid)
                result = gmp.get_flash_sale_pilot()
                result_dict[sid] = result
            except Exception,e:
                print e

    select_server_ids = server_ids
    group_servers_dict = get_group_servers_dict(request)
    return render_to_response(template_path, locals())

@Route()
def flash_sale_pilot_edit(request,template_path = 'game/flash_sale_pilot_edit.html'):
    '''修改限时抢购武将
    '''
    print request.REQUEST
    _r = {'code':-1, 'msg':''}
    ty = int(request.REQUEST.get('ty','0'))
    sid = int(request.GET.get('sid','0'))
    server_id = int(request.POST.get('server_id','0'))
    msg_json = request.POST.get('msg','0')
    context = {}
    context["group_servers_dict"] = get_group_servers_dict(request)
    result = ''
    if sid:
        try:
            gmp = GMProtocol(sid)
            result = gmp.get_flash_sale_pilot()

        except Exception,e:
            print e

    if ty == 0:
        context['ty'] = ty

    if ty == 1:
        context['ty'] = ty
        context['select_server_ids'] = sid
        context['result'] = result

    if ty == 2:
        context['ty'] = ty
        if sid:
            try:
                gmp = GMProtocol(sid)
                msg = result
                msg[0] = ty
                result = gmp.modify_flash_sale_pilot(msg)
                if result != 0:
                    return HttpResponse('删除出错')

            except Exception,e:
                print e

        return render_to_response('feedback.html')

    if server_id:
        try:
            gmp = GMProtocol(server_id)
            msg = json.loads(msg_json)
            result = gmp.modify_flash_sale_pilot(msg)
            if result == 0:
                _r['code'] = result
                _r['msg'] = '成功'
        except Exception,e:
            _r['msg'] = e
        return HttpResponse(json.dumps(_r))

    return render_to_response(template_path, context)


