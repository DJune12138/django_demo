# -*- coding: utf-8 -*-

from views.base import notauth
from django.http import HttpResponse
from models import Channel


@notauth
def login_init_info(request):
    """游戏前端请求服务器列表"""

    # 获取渠道ID
    channel = request.GET.get('channel')

    # 获取对应的渠道模型
    channel = Channel.objects.get(id=channel)

    # 获取渠道对应的服务器
    servers = channel.group_set.first().server.all()

    # 遍历服务器，并组织数据
    json_content = '{"serverList": ['
    for server in servers:
        json_content += u'{"serverName": "%s", "serverId": %s, "ip": "%s"}, ' % (server.name, server.id, server.game_addr)
    json_content = json_content.rstrip(', ') + ']}'

    # 返回数据
    return HttpResponse(json_content)
