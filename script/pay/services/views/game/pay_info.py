# -*- coding:utf-8 -*-#
__author__ = 'Administrator'


from django.shortcuts import HttpResponse, render_to_response
from analys.cache import center_cache
from analys.models.pay import PayAction, PayChannel
from analys.views.base import get_server_list
from django.db.models import  Q

fields_refer = {'0':'query_id', '1':'order_id', '2':'pay_user', '3':'card_no', '4':'remark__contains'}

def game_pay_info(request):
    player_id = int(request.GET.get('player_id', 0))
    condition = request.POST.get('condition', 0)
    condition_value = request.POST.get('condition_value', '')
    if not player_id:
        return HttpResponse('无效请求!')

    server_id = player_id >> 20     #右移20位获得服务器ID？！
    server_id = center_cache.get_server_config(server_id, 'master_server_id', server_id)

    query = Q()

    if server_id:
        query = query & Q(server_id = server_id)

    if player_id:
        query = query & Q(pay_user = player_id)

    if condition and condition_value:
        q_filter = {fields_refer[condition]: condition_value}
        query = query & Q(**q_filter)

    pay_infos = PayAction.objects.filter(query)
    if pay_infos:
        server_list = {}
        for serv in get_server_list():
            server_list[serv.id] = serv.name

        payChannels = {}
        for channel in PayChannel.objects.all():
            payChannels[channel.id] = channel.name

        for info in pay_infos:
            info.server_name = server_list.get(info.server_id, '')
            info.pay_type_name = payChannels.get(info.pay_type, '')

    result = {}
    result['server_id'] = server_id
    result['condition'] = condition
    result['condition_value'] = condition_value
    result['player_id'] = player_id
    result['datas'] = pay_infos

    return render_to_response("game/pay_info.html", result)