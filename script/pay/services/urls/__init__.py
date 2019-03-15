# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from services import settings

urlpatterns = patterns('', 
 #支付通知相关
    url(r'^service/', include('services.urls.service')),

# api 相关
    url(r'^api/', include('services.urls.service')),

    #支付通知相关
#    url(r'^game/', include('services.urls.game')),
    
    #客户端相关
    url(r'^client/', include('services.urls.client')),
    
    
    url(r'^static/(?P<path>.*)$','django.views.static.serve',{'document_root':settings.STATIC_ROOT}),
    url(r'^(\S+.[jpg|gif|js|css|ico|py])$','django.views.static.serve',{'document_root':settings.STATIC_ROOT}),
)
