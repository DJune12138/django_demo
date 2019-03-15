# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^list', 'analys.views.channel.question_list'),
    url(r'^result/list', 'analys.views.channel.channel_view'),
    url(r'^result/list/(\d+)', 'analys.views.channel.channel_view'),
    url(r'^result/query/(\d+)', 'analys.views.channel.channel_list_allchannel'),
    url(r'^pay/list', 'analys.views.channel.pay_list'),
    url(r'^player/list', 'analys.views.channel.player_list'),
    url(r'^player/query', 'analys.views.channel.player_query'),
    url(r'^question/list', 'analys.views.channel.question_list'),
    url(r'^question/user/list/(\d+)', 'analys.views.channel.manage_question_list_user'),
    url(r'^question/remove/(\d+)$', 'analys.views.server.question.manage_question_remove'),
    url(r'^question/answer$', 'analys.views.server.question.manage_question_answer'),
    url(r'^login/do', 'analys.views.channel.channel_login_do'),
    url(r'^login$', 'analys.views.channel.channel_login'),
    url(r'^logout$', 'analys.views.channel.channel_logout'),
    url(r'^change_password/do$', 'analys.views.channel.change_password_do'),
    url(r'^change_password$', 'analys.views.channel.change_password'),
    url(r'^login_key$', 'analys.views.channel.login_key'),
    url(r'^user/lock/(\d+)/(\d+)', 'analys.views.channel.user_lock'),
    url(r'^user/password/(\d+)', 'analys.views.channel.user_password'),
    url(r'^player/block/(\d+)/(\d+)', 'analys.views.channel.player_block'),
    url(r'^selectServer$','analys.views.channel.channel_change_server'),
    url(r'^pay/rank/list$','analys.views.channel.channel_pay_rank_list'),
    url(r'^player/shutup/(\d+)','analys.views.game.player.channel_player_shutup'),#渠道后台  屏蔽玩家发言
    url(r'^query/result/(\d+)', 'analys.views.channel.channel_query_result'),#渠道后台查询日志数据
    url(r'^$', 'analys.views.channel.index'),

)