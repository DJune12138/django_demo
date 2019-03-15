# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    #服务器参数
    url(r'^server/info/(\d+)$', 'views.game.server.server_info'),
    url(r'^server/info$', 'views.game.server.server_info'),
    url(r'^server/active/list$', 'views.game.server.server_active_cfg_list'),#服务器   活动参数配置
    url(r'^server/active/edit$', 'views.game.server.edit_server_active_cfg'),
    url(r'^server/active/save$', 'views.game.server.save_server_active_cfg'),
    url(r'^server/active/del$', 'views.game.server.delete_server_active_cfg'),
    url(r'^server/modify/(\d+)$', 'views.game.server.server_modify'),
    url(r'^server/modify$', 'views.game.server.server_modify'),
    
    #发送消息
    url(r'^send/(\d+)$', 'views.game.player.send_msg'),
    url(r'^send$', 'views.game.player.send_msg'),
    
    #GM协议编辑
    url(r'^gm/(\d+)[/]?$', 'views.game.gm.gm'), 
    url(r'^gm/list$', 'views.game.def_gm.gm_list'),
    url(r'^gm/edit/(\d+)$', 'views.game.def_gm.gm_edit'),
    url(r'^gm/edit$', 'views.game.def_gm.gm_edit'),
    url(r'^gm/save$', 'views.game.def_gm.gm_save'),
    url(r'^gm/del$', 'views.game.def_gm.gm_del'),
    

    url(r'^pay/info$', 'views.game.pay_info.game_pay_info'),
)