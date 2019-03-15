# -*- coding: utf-8 -*-


from django.conf.urls import patterns, include, url
import settings


urlpatterns = patterns('',
    url(r'^card/(\S+)/([\w]{3,})[/]?$', 'views.index'),

    url(r'^card_service/card_get/([\w]{3,})[/]?$', 'views.show'),
    #  客户端礼包卡接口
    url(r'^card_service[/]?$', 'views.card'),
    # 服务端礼包接口
    url(r'^card_service/interface[/]?$', 'interface.gift'),
    # 绑定游客奖励接口
    url(r'^card_service/reward/([\w]{3,})/(.*)[/]$', 'views.interface.reward'),
    # 绑定游客奖励接口
    url(r'^card_service/reward_get/([\w]{3,})/(.*)[/]$', 'views.interface.reward_get'),

    url(r'^card/prize/get/([\w]{3})[/]?$', 'prize.prize_get'),
    url(r'^card/prize/([\w]{3})[/]?$', 'prize.prize_view'),
    url(r'^card/(\S+)/([\w]{3})[/]?$', 'views.index'),

    url(r'^static/(?P<path>.*)$','django.views.static.serve',{'document_root':settings.STATIC_ROOT}),
    url(r'^(\S+.[jpg|gif|js|css|ico])$','django.views.static.serve',{'document_root':settings.STATIC_ROOT}),
)
