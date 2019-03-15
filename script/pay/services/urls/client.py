# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

def _p(func_name):
    return 'services.views.%s'%func_name

urlpatterns = patterns('',
    url(r'^login$', _p('client.login')),
    url(r'^guest/register$', _p('client.register_guest')),
    url(r'^guest/bind', _p('client.bind_guest')),
    url(r'^register$', _p('client.register')),
    url(r'^change_password$', _p('client.change_password')),

    url(r'^account/set_safe_question/$', _p('client.set_safe_question')),
    url(r'^account/get_safe_question/$', _p('client.get_safe_question')),
    url(r'^account/reset_password/$', _p('client.reset_password')),

    url(r'^open/([\S\s]+)$', _p('client.client_open')),

    url(r'^player_history$',_p('client.player_history')),

    url(r'^ip', _p('client.ip')),

    #客服
    url(r'^question/post/(\d+)[/]?$', _p('client.question_post')),
    url(r'^question/score/(\d+)/(\d+)[/]?$', _p('client.question_score')),
    url(r'^question/status/(\d+)/(\d+)[/]?$', _p('client.question_status')),
    url(r'^question/list/(\d+)/(\d+)/(\d+)[/]?$', _p('client.question_list')),
    url(r'^question/list/(\d+)/(\d+)[/]?$', _p('client.question_list')),


    #充值
#    url(r'^pay_note/$', _p(''pay_note.resend')),
    url(r'^pay/qq/(\d+)/(\d+)$', _p('pay.qq.pay_qq')),
    url(r'^pay$', _p('pay.pay')),
    url(r'^pay/baoruan$', _p('pay.pay'),{'pay_type':142}),
    url(r'^pay/channel/(\d+)', _p('pay.pay_channel')),
    url(r'^getgold$', _p('pay.get_gold.get_gold')),
    url(r'^checkgetgold$', _p('pay.get_gold.check_get_gold')),
    url(r'^pay/result/(\d+)/(\d+)/$', _p('pay.result_user')),


    url(r'^pay/google', _p('pay.confirm'),{'func_name':'google'}),
    url(r'^pay/confirm/([0-9a-z_]+)',_p('pay.confirm')),
    url(r'^pay/apple', _p('pay.confirm'),{'func_name':'apple'}),

    url(r'^pay/mycard/(\d+)', _p('pay.mycard_billing.pay_mycard_billing_select')),
    url(r'^pay/mycard/go/(\d+)', _p('pay.mycard_billing.pay_mycard_billing_go')),

    #gash Plus
    url(r'^pay/gash/transaction$', _p('pay.gash.pay_gash_transaction')),
    url(r'^pay/gash/telecom$', _p('pay.gash.pay_gash_telecom')),
    url(r'^pay/gash/settle$', _p('pay.gash.client_settle')),
    url(r'^pay/gash/checkorder$', _p('pay.gash.check_order')),


    #点入广告
    url(r'^ads/dianru/download$', _p('ads.dianru.download')),
    url(r'^ads/dianru/active/([\S\s]+)$', _p('ads.dianru.active')),

    #分享-----------
    url(r'^share/page/(\d+)/(\d+)[/]?$', _p('share.page')),
    url(r'^share/page[/]?/(.*)$', _p('share.page')),
    url(r'^share/link/(\d+)[/]?$', _p('share.share_link')),
    url(r'^share/link/(.*)$', _p('share.share_link')),
    url(r'^share/auth/(\d+)[/]?$', _p('share.auth')),
    url(r'^share/auth/(.*)$', _p('share.auth')),
    url(r'^share/result/(\d+)/(\d+)[/]?$', _p('share.result')),
    url(r'^share/result[/]?/(.*)$', _p('share.result')),
    #----------------

    #游爱账号注册
    url(r'register_youai_user[/]?',_p('client.register_youai_user')),
    #游爱账号获取
    url(r'get_youai_user[/]?',_p('client.get_youai_user')),


    #客户端最后信息提交
    url(r'^lastinfo/post/(\d+)/(\d+)/([0-9a-z_]+)[/]?$', _p('client.post_client_last_info')),
    #客户端最后信息获取
    url(r'^lastinfo/get/(\d+)/(\d+)/([0-9a-z_]+)[/]?$', _p('client.get_client_last_info')),

    #客户端语音提交接口
    url(r'^voice/post[/]?$', _p('client.post_voice')),

    # 37wan验证获得openid，旧
    url(r'get_37openid[/]?$',_p('client.get_a37wan_openid')),

    # 37wan验证获得openid，新，返回JSON格式
    url(r'get_37openid_v2[/]?',_p('client.get_a37wan_openid_v2')),

    # 根据37联远Id获取分区key
    url(r'get_partition_id[/]?',_p('client.get_partition_id')),

)
