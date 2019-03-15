# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

def _p(func_name):
    return 'services.views.%s'%func_name

urlpatterns = patterns('',

    #以下confirm不能去掉
    url(r'^confirm/mycard/success',_p('pay.mycard_billing.confirm_mycard_billing')),
    url(r'^confirm/mycard/fail',_p('pay.mycard_billing.confirm_mycard_billing')),
    url(r'^confirm/mycard/fix',_p('pay.mycard_billing.confirm_mycard_billing_fix')),

    url(r'^result/mycard_tw',_p('pay.mycard.result_mycard'),{'pay_type':'1,2,3'}),
    url(r'^result/mycard',_p('pay.mycard.result_mycard'),{'pay_type':'2,3'}),

    url(r'^confirm/([0-9a-z_]+)',_p('pay.confirm')),
    url(r'^check_client_info$',_p('pay.check_client_info')),   #####韩国

    #对外接口
    url(r'^server_list/(\S+)',_p('service.server_list')),
    url(r'^player_info$',_p('service.player_info')),

    url(r'^get_server_list$', _p('api.get_server_list')),
    url(r'^get_player$', _p('api.get_player')),
    url(r'^goods_permission$', _p('api.goods_permission')),
    url(r'^get_product_list$', _p('api.get_product_list')),
    url(r'^operation$', _p('api.operation')),

    url(r'^convert$', _p('api.convert')),   ###客户端写player_convert

    url(r'^login_query/(\d+)$',_p('service.login_query')),
    url(r'^pay_count$',_p('service.pay_count')),
    url(r'^pay_top$',_p('service.pay_top_list')),
    url(r'^query/([0-9a-z_]+)',_p('service.query')),


    #授权接口
    url(r'^auth/(\S+)/(\d+)', _p('share.auth')),


    url(r'^close', _p('share.close')),

    url(r'^question/sync', _p('question_sync.question_sync_interface')),

    # sgz登录发放奖励接口
    url(r'sgz_betauser_reward', _p('service.sgz_betauser_reward')),

    # 37 聊天监控
    url(r'^player_manage$',_p('service.player_manage')),

    # 37 中奖通知
    url(r'^send_prize$',_p('service.send_prize')),
)
