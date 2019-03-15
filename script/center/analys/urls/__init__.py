# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.http import HttpResponseForbidden
import settings
from AutoUrl import get_handlers, Route

_urls = ['',

         url(r'^$', lambda request: HttpResponseForbidden('403')),
         # 游爱帐号相关
         url(r'^user/list$', 'views.player.user.user_list'),
         url(r'^user/lock/(\d+)/(\d+)$', 'player.user.admin.user_lock'),
         url(r'^user/unlock$', 'views.player.user.user_unlock'),
         url(r'^user/lock$', 'views.player.user.user_lock'),
         url(r'^user/password/(\d+)$', 'views.player.user.user_password'),
         url(r'^user/password$', 'views.player.user.user_password'),
         url(r'^user/convert/(\d+)$', 'views.player.user.user_convert'),
         url(r'^user/pay', 'views.pay.pay.user_pay'),
         url(r'^user/mibao/clear', 'views.player.user.clear_mibao'),
         url(r'^user/mibao/modify[/]?$', 'views.player.user.modify_mibao'),
         url(r'^user/user_status_edit$', 'views.player.user.user_status_edit'),
         #    url(r'^user/login.json','views.player.user_login'),

         # 角色相关
         url(r'^player/list$', 'views.player.player.player_list'),
         url(r'^player/type$', 'views.player.user_type.user_type_list'),
         url(r'^player/type/edit$', 'views.player.user_type.user_type_edit'),
         url(r'^player/type/save$', 'views.player.user_type.user_type_save'),
         url(r'^player/type/save/(\d+)$', 'views.player.user_type.user_type_save'),
         url(r'^player/type/del$', 'views.player.user_type.user_type_del'),
         url(r'^player/info$', 'views.player.player.player_info'),

         # 分区相关
         url(r'^group/list$', 'views.server.group.group_list'),
         url(r'^group/edit/(\d+)$', 'server.group.admin.group_edit'),
         url(r'^group/edit$', 'views.server.group.group_edit'),
         url(r'^group/save/(\d+)$', 'server.group.admin.group_save'),
         url(r'^group/save$', 'views.server.group.group_save'),
         # 服务器分组
         url(r'^grouplist/edit$', 'views.server.group.grouplist_edit'),
         url(r'^grouplist/save$', 'views.server.group.grouplist_save'),
         url(r'^grouplist/remove/(\d+)$', 'views.server.group.grouplist_remove'),

         # 公告相关
         url(r'^notice/list$', 'views.server.notice.notice_list'),
         url(r'^notice/edit/(\d+)$', 'views.server.notice.notice_edit'),
         url(r'^notice/edit$', 'views.server.notice.notice_edit'),
         url(r'^notice/save/(\d+)$', 'views.server.notice.notice_save'),
         url(r'^notice/save$', 'views.server.notice.notice_save'),
         url(r'^notice/remove/(\d+)$', 'views.server.notice.notice_remove'),
         url(r'^notice/remove$', 'views.server.notice.notice_remove'),
         url(r'^notice/create/(\d+)$', 'views.server.notice.notice_createStaticFile'),
         url(r'^notice/create$', 'views.server.notice.notice_createStaticFile'),
         url(r'^notice/check$', 'views.server.notice.notice_check'),

         url(r'^push/create$', 'views.server.notice.push_create'),
         url(r'^push/list$', 'views.server.notice.notice_list', {'notice_type': 4}),
         url(r'^push/edit/(\d+)$', 'views.server.notice.notice_edit', {'notice_type': 4}),
         url(r'^push/edit$', 'views.server.notice.notice_edit', {'notice_type': 4}),

         # 更新相关
         url(r'^upgrade/list$', 'views.server.upgrade.upgrade_list'),
         url(r'^upgrade/edit/(\d+)$', 'views.server.upgrade.upgrade_edit'),
         url(r'^upgrade/edit$', 'views.server.upgrade.upgrade_edit'),
         url(r'^upgrade/save/(\d+)$', 'views.server.upgrade.upgrade_save'),
         url(r'^upgrade/save$', 'views.server.upgrade.upgrade_save'),
         url(r'^upgrade/make/(\d+)$', 'views.server.upgrade.upgrade_make'),
         url(r'^upgrade/make$', 'views.server.upgrade.upgrade_make'),
         url(r'^upgrade/clear$', 'views.server.upgrade.upgrade_clear'),
         url(r'^upgrade/remove/(\d+)$', 'views.server.upgrade.upgrade_remove'),
         url(r'^upgrade/remove$', 'views.server.upgrade.upgrade_remove'),

         # 充值列表
         url(r'^pay/list/(\S+)$', 'views.pay.pay.pay_result_list'),
         url(r'^pay/list$', 'views.pay.pay.pay_result_list'),
         url(r'^pay/check[/]?$', 'views.pay.pay.pay_check'),
         url(r'^pay/check/(\d+)$', 'views.pay.pay.pay_check'),
         url(r'^pay/confirm[/]?$', 'views.pay.pay.pay_confirm'),
         url(r'^pay/confirm/(\d+)$', 'views.pay.pay.pay_confirm'),
         url(r'^pay/user/rank', 'views.pay.pay.pay_user_rank'),
         url(r'^pay/pay_fix$', 'views.pay.pay.pay_fix'),
         url(r'^pay/update_channel$', 'views.pay.pay.update_pay_action_channel'),
         url(r'^pay/add/(\S+)$', 'views.pay.pay.add'),
         url(r'^pay/add/$', 'views.pay.pay.add'),
         url(r'^pay/do_add$', 'views.pay.pay.do_add'),
         url(r'^pay/convert$', 'views.pay.pay.pay_convert'),
         url(r'^pay/reissue', 'views.pay.pay.pay_reissue'),
         # 日志相关
         url(r'^log/data/delete/(\d+)', 'views.log.log.log_data_delete'),

         # 查询相关
         url(r'^query/list', 'views.log.query.query_list'),
         url(r'^query/edit$', 'views.log.query.query_edit'),
         url(r'^query/save$', 'views.log.query.query_save'),
         url(r'^query/view$', 'views.log.query.query_view'),
         url(r'^query/view/(\S+)$', 'views.log.query.query_view'),
         url(r'^query/remove$', 'views.log.query.query_remove'),
         url(r'^query/clear/cache$', 'views.log.query.query_clear_cache'),
         url(r'^query/interface$', 'views.log.query.query_view'),
         url(r'^query/interface/(\d+)$', 'views.log.query.query_view'),
         url(r'^query/task/(?P<channel>\w+)/$', 'views.log.task.interface'),

         # 统计相关
         url(r'^statistic/list/(\d+)$', 'views.log.statistic.statistic_list'),
         url(r'^statistic/list', 'views.log.statistic.statistic_list'),
         url(r'^statistic/edit/(\d+)/(\d+)$', 'views.log.statistic.statistic_edit'),
         url(r'^statistic/edit/(\d+)$', 'views.log.statistic.statistic_edit'),
         url(r'^statistic/edit$', 'views.log.statistic.statistic_edit'),
         url(r'^statistic/save/(\d+)$', 'views.log.statistic.statistic_save'),
         url(r'^statistic/save$', 'views.log.statistic.statistic_save'),
         url(r'^statistic/remove/(\d+)$', 'views.log.statistic.statistic_remove'),
         url(r'^statistic/remove$', 'views.log.statistic.statistic_remove'),
         url(r'^statistic/execute/(\d+)/(\d+)$', 'views.log.statistic.statistic_execute'),
         url(r'^statistic/execute/(\d+)$', 'views.log.statistic.statistic_execute'),
         url(r'^statistic/execute$', 'views.log.statistic.statistic_execute'),
         url(r'^statistic/execute/batch$', 'views.log.statistic.batch_statistic'),

         # 帮助相关
         url(r'^help/', include('urls.help')),

         # 充值通道
         url(r'^pay/channel/list$', 'views.pay.pay.pay_channel_list'),
         url(r'^pay/channel/edit/(\d+)$', 'views.pay.pay.pay_channel_edit'),
         url(r'^pay/channel/edit$', 'views.pay.pay.pay_channel_edit'),
         url(r'^pay/channel/save/(\d+)$', 'views.pay.pay.pay_channel_save'),
         url(r'^pay/channel/save$', 'views.pay.pay.pay_channel_save'),
         url(r'^pay/channel/remove/(\d+)$', 'views.pay.pay.pay_channel_remove'),
         url(r'^pay/channel/remove$', 'views.pay.pay.pay_channel_remove'),
         url(r'^pay/server/paychannel', 'views.pay.pay.pay_server_paychannel'),

         url(r'^question/convert$', 'views.server.question.question_convert'),

         # 客服问题
         url(r'^question/remove', 'views.server.question.manage_question_remove'),
         url(r'^question/answer$', 'views.server.question.manage_question_answer'),
         url(r'^question/list/(\d+)/(\d+)/(\d+)$', 'views.server.question.manage_question_list'),
         url(r'^question/list/(\d+)/(\d+)$', 'views.server.question.manage_question_list'),
         url(r'^question/list/(\d+)$', 'views.server.question.manage_question_list'),
         # url(r'^question/list/user/(\d+)', 'views.admin.manage_question_list_user'),
         url(r'^question/list/user', 'views.server.question.manage_question_list_user'),
         url(r'^question/list', 'views.server.question.manage_question_list'),
         url(r'^question/category$', 'views.server.question.edit_category'),
         url(r'^question/viplist$', 'views.server.question.viplist'),
         url(r'^question/viplist_save$', 'views.server.question.viplist_save'),
         url(r'^question/viplist_edit$', 'views.server.question.viplist_edit'),

         # *************后台同步管理*************#
         url(r"^sync/backstage$", 'views.sync.backstage.backstage_list'),
         url(r"^sync/backstage/$", 'views.sync.backstage.backstage_list'),
         url(r"^sync/backstage/edit$", 'views.sync.backstage.backstage_edit'),
         url(r"^sync/backstage/remove$", 'views.sync.backstage.backstage_remove'),
         url(r"^sync/backstage/push$", 'views.sync.backstage.backstage_push'),
         url(r"^sync/backstage/dosync$", 'views.sync.backstage.do_backstage_sync'),
         url(r"^sync/backstage/remotedb$", 'views.sync.backstage.get_remote_push_data'),
         # *************后台同步管理END*************#

         # 游戏相关
         url(r'^game/', include('urls.game')),

         # 帮助
         url(r'^help/', include('urls.help')),

         # 中央统计后台需要的接口
         url(r'^interface/statistic_data[/]$', 'views.log.interface.statistic_data'),  # 统计数据接口
         url(r'^interface/agent_channel[/]$', 'views.log.interface.agent_channel'),  # 统计数据平台渠道接口
         url(r'^interface/group_server[/]$', 'views.log.interface.group_server'),  # 统计数据分区服务器接口

         ##渠道管理相关
         #    url(r'^manage/channel/list', 'views.server.channel.manage_channel_list'),
         #    url(r'^manage/channel/edit/(\d+)$', 'views.server.channel.manage_channel_edit'),
         #    url(r'^manage/channel/edit$', 'views.server.channel.manage_channel_edit'),
         #    url(r'^manage/channel/save/(\d+)$', 'views.server.channel.manage_channel_save'),
         #    url(r'^manage/channel/save$', 'views.server.channel.manage_channel_save'),
         #    url(r'^manage/channel/remove/(\d+)$', 'views.server.channel.manage_channel_remove'),
         #    url(r'^manage/channel/remove$', 'views.server.channel.manage_channel_remove'),
         #    url(r'^manage/channel/view/(\d+)$', 'views.server.channel.channel_view'),
         #    url(r'^manage/channel/view$', 'views.server.channel.channel_view'),
         #
         #    #渠道后台相关
         #    url(r'^channel/', include('urls.channel')),

         # 游戏卡管理相关
         url(r'^card/', include('analys.urls.card')),

         url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
         url(r'^(\S+\.[jpg|gif|js|css|ico|py|png])$', 'django.views.static.serve',
             {'document_root': settings.STATIC_ROOT}),

         # 游戏前端请求服务器列表
         url(r'^login/initInfo$', 'views.leading_end.login_init_info')
         ]

_auto_handlers = get_handlers()
urlpatterns = (patterns(*tuple(_urls + _auto_handlers)))
