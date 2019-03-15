# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # Examples:
    url(r'^view/$', 'analys.views.help.help.view'),
    url(r'^view/(\S+)', 'analys.views.help.help.view'),
    url(r'^add', ' analys.views.help.help.help_add'),
    url(r'^save/(\d+)', 'analys.views.help.help.save'),
    url(r'^save$', 'analys.views.help.help.save'),
    url(r'^edit/(\d+)', 'analys.views.help.help.edit'),
    url(r'^edit$', 'analys.views.help.help.edit'),
    url(r'^list/', 'analys.views.help.help.help_list'),
    url(r'^list$', 'analys.views.help.help.help_list'),
    url(r'^del[/]?$', 'analys.views.help.help.help_del'),
    url(r'^del/(\d+)', 'analys.views.help.help.help_del'),
    url(r'^category/list', 'analys.views.help.help.category_list'),
    url(r'^category/save/(\d+)', 'analys.views.help.help.category_save'),
    url(r'^category/save$', 'analys.views.help.help.category_save'),
    url(r'^category/del/(\d+)', 'analys.views.help.help.category_del'),
    url(r'^category/del$', 'analys.views.help.help.category_del'),
    url(r'^filecreate/(\d+)', 'analys.views.help.help.file_create'),
    url(r'^filecreate$', 'analys.views.help.help.file_create'),
    url(r'^import', 'analys.views.help.help.import_html_data'),
    url(r'^export[/]?$', 'analys.views.help.help.help_export'),
    url(r'^upload[/]?$', 'analys.views.help.help.help_upload'),
)
