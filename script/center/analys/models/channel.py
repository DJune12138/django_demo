# -*- coding: utf-8 -*-

from django.db import models
from django.db import connection, connections

from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute,
                   JSONField)
import datetime, time
import json
import MySQLdb
import traceback
from .resource import Resource
from models.admin import Admin
from models.role import Role
from settings import get_app_label
from django.utils.datastructures import SortedDict
import copy
from django.db.models import Q


class Channel(models.Model, BaseModelMixin):
    '''渠道
    '''
    channel_key = models.CharField(max_length=50)
    login_key = models.CharField(max_length=32)
    name = models.CharField(max_length=20)
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=50)
    create_time = models.DateTimeField(blank=True, auto_now_add=True)
    last_time = models.DateTimeField(blank=True, null=True)
    last_ip = models.CharField(max_length=20)
    logins = models.IntegerField(default=0)
    group_name = models.CharField('渠道平台名', max_length=20, default='', db_index=True)
    game_app_key = models.CharField('游戏APPKEY', max_length=50, db_index=True)
    group_key = models.CharField(max_length=20)
    allow_earn = models.IntegerField('渠道允许的价值数', default=30000)  ###########################
    novice_mail = models.TextField(u'新手邮件')

    @classmethod
    def get_channel_for_agent(self, agent_name):
        return

    def __unicode__(self):
        return 'channel_%s' % self.name

    @staticmethod
    def lock():
        cursor = connections['write'].cursor()
        cursor.execute('LOCK TABLES channel WRITE;')
        row = cursor.fetchone()
        # cursor.close()
        return row

    @staticmethod
    def unlock():
        cursor = connections['write'].cursor()
        cursor.execute('UNLOCK TABLES;')
        row = cursor.fetchone()
        # cursor.close()
        return row

    class Meta:
        db_table = u'channel'
        app_label = get_app_label()
        ordering = ('id',)


class ChannelOther(models.Model, BaseModelMixin):
    cid = models.IntegerField('渠道ID', unique=True, db_index=True, null=False)
    data = JSONField('JSOn数据')

    KEP_MAP = SortedDict([
        # ("service_qq",{"name":"VIP客服QQ","type":"text"}),
        # ("service_time",{"name":"客服时间"}),
        # ("service_phone",{"name":"客服电话"}),
        # ("vip_contact",{"name":"VIP客服电话"}),
        # #  ("vip_contact",{"name":"VIP客服联系方式","remark":"如:VIP客服QQ：8888888,VIP客服电话：21213090,…… 逗号隔开","handler":lambda x:str(x).replace('，',',')}),
        # # 下面是分享的配置
        # ("off_share_type",{"name":"需要关闭的分享类型","remark":"例如:qq,weixin,qzone,sina,写 all的话是关闭所有了"}),
        # ("share_title",{"name":"分享的标题","remark":"","default":"银河争霸"}),
        # ("share_desc",{"name":"分享的副标题","remark":"","default":"穿越星际决战未来！"}),
        # ("share_msg",{"name":"分享类容格式","remark":"%s 是占位符号","default":"服务器-%s，火热开启！我的邀请码是：%s，寻找星际战友，共创银河世纪帝国！"}),
        # ("share_imagePath",{"name":"分享的图片地址","default":"http://xj.gzyouai.com/galaxy/images/po1_p.jpg"}),
        # ("share_openUrl",{"name":"跳转的地址","default":"http://xj.gzyouai.com/galaxy/"}),
        # ("offMonthCard",{"name":"关闭月卡【现活动页卡】","default":"0","remark":"填1就是关闭月卡功能【现活动页卡】"}),
        # ("offGiftCard",{"name":"关闭礼品卡【VIP界面】","default":"0","remark":"填1关闭礼品卡【VIP界面】"})
        ("upload_question", {"name": "上传问题到公司后台", "default": "0", "remark": "0 关闭 1 开启"}),
        ("upload_reyun", {"name": "上传充值数据到热云", "default": "0", "remark": "直接填写appid,如果不需要,则0"}),
        ("upload_track", {"name": "上传充值数据到track", "default": "0", "remark": "直接填写appid,如果不需要,则0"}),
        ("upload_tracking", {"name": "上传充值数据到trackingIO", "default": "0", "remark": "直接填写appid,如果不需要,则0"})
    ])

    def save_filter_data(self, input_data):
        _d = {}
        for k, v in self.KEP_MAP.iteritems():
            value = input_data.get(k, "")
            if value:
                if v.get('type', '') == 'list':
                    if not isinstance(value, list):
                        value = [value]
                    else:
                        if isinstance(value, list):
                            value = value[0]
                handler = v.get('handler', None)
                if handler:
                    value = handler(value)
                if str(value).isdigit():
                    value = int(value)
                _d[k] = value
        self.data = _d

    def get_data_detail(self, key_name=None):
        _d = SortedDict()
        data = self.data
        for k, v in self.KEP_MAP.items():
            tmp_v = copy.copy(v)
            tmp_v['value'] = data.get(k, "") or v.get('default', '')
            if tmp_v.get('handler', None):
                tmp_v.pop('handler')
            _d[k] = tmp_v
        if key_name:
            return _d[key_name]
        return _d

    @classmethod
    def get_channel_models(self, channel_ids=[]):
        '''渠道模型与相应其他信息
        '''
        sql = 'SELECT c.id `id` ,c.channel_key `key`,c.name `name`,co.data `data` FROM channel c LEFT JOIN channel_other co ON c.id=co.cid '
        if channel_ids:
            sql += ' where c.id in (%s)' % ','.join([str(cid) for cid in channel_ids])
        return Channel.objects.raw(sql)

    class Meta:
        db_table = u'channel_other'
        app_label = get_app_label()
        ordering = ('id',)


class AgentAdminMinxin(object):

    @classmethod
    def get_admin(cls, agent_id):
        agnet_objs = cls.objects.prefetch_related('channel', 'server', 'server_group').filter(id=agent_id)
        agnet_obj = agnet_objs[0]
        admin = Admin()
        admin.id = -1
        admin.alias = agnet_obj.alias
        admin.username = agnet_obj.username
        admin.last_ip = agnet_obj.last_ip
        admin.login_count = agnet_obj.login_count
        admin.last_ip = agnet_obj.last_ip
        admin.create_time = agnet_obj.create_time
        admin.last_time = agnet_obj.last_time
        admin.session_key = agnet_obj.session_key

        menu_resouces = Role.objects.get(name="渠道").get_resource('menu')

        admin.set_resource('menu', menu_resouces)
        admin.set_resource('channel', agnet_obj.channel)
        admin.set_resource('agent', agnet_objs)

        # 如果勾选了分区 即有分区下的所有服务器权限

        from models.server import Server
        agent_servers = Server.objects.filter(Q(group__id__in=agnet_obj.server_group.all()) \
                                              | Q(id__in=agnet_obj.server.all())
                                              ).distinct()

        admin.set_resource('server', agent_servers)
        admin.set_resource('server_group', agnet_obj.server_group)
        return admin


class Agent(models.Model, BaseModelMixin, AgentAdminMinxin):
    '''平台模型
    '''
    name = models.CharField('平台名,英文字母', max_length=20, db_index=True)
    alias = models.CharField('别名', max_length=20)
    username = models.CharField('登录名', max_length=20, db_index=True)
    password = models.CharField('密码', max_length=50, db_index=True)
    create_time = models.DateTimeField('创建时间', blank=True, auto_now_add=True)
    last_time = models.DateTimeField('最后时间', blank=True, auto_now_add=True)
    last_ip = models.CharField('登录ip', max_length=20)
    login_count = models.IntegerField('登录次数', default=0)

    session_key = models.CharField('会话key', max_length=40, db_index=True)
    game_app_key = models.CharField('游戏APPKEY', max_length=50, db_index=True)

    channel = models.ManyToManyField(Channel, verbose_name='渠道')
    # from models.server import Group
    # server_group = models.ManyToManyField(Group,verbose_name='分区')
    from models.server import Server
    server = models.ManyToManyField(Server, verbose_name='服务器')

    @classmethod
    def get_agent_channels(cls):
        _r = {}
        for a in cls.objects.all():
            _r[a] = cls.get_channel(a.name)
        return _r

    @classmethod
    def get_channel(cls, agent_name):
        return Channel.objects.filter(agent_name=agent_name)

    class Meta:
        db_table = u'agent'
        app_label = get_app_label()
        ordering = ('id',)


# class ConferenceAdminMinxin(object):
#
#     @classmethod
#     def get_admin(cls,agent_id):
#         conference_objs =  cls.objects.prefetch_related('channel').filter(id=agent_id)
#         agnet_obj = conference_objs[0]
#         admin = Admin()
#         admin.id = -1
#         admin.alias = agnet_obj.alias
#         # admin.username = agnet_obj.username
#         # admin.last_ip = agnet_obj.last_ip
#         # admin.login_count = agnet_obj.login_count
#         # admin.last_ip = agnet_obj.last_ip
#         admin.create_time = agnet_obj.create_time
#         admin.last_time = agnet_obj.last_time
#         admin.session_key = agnet_obj.session_key
#
#         menu_resouces = Role.objects.get(name="渠道").get_resource('menu')
#
#         admin.set_resource('menu', menu_resouces)
#         admin.set_resource('channel', agnet_obj.channel)
#         admin.set_resource('conference',agnet_obj)
#
#         #如果勾选了分区 即有分区下的所有服务器权限
#
#         agent_servers = Server.objects.filter(Q(group__id__in=agnet_obj.server_group.all())\
#                                                 |Q(id__in=agnet_obj.server.all())
#                                              ).distinct()
#
#         admin.set_resource('server', agent_servers)
#         admin.set_resource('server_group', agnet_obj.server_group)
#         return admin

class Conference(models.Model, BaseModelMixin):  ####################
    '''公会模型
    '''
    name = models.CharField('平台名,英文字母', max_length=20, db_index=True)
    alias = models.CharField('别名', max_length=20)
    create_time = models.DateTimeField('创建时间', blank=True, auto_now_add=True)
    last_time = models.DateTimeField('最后时间', blank=True, auto_now_add=True)

    game_app_key = models.CharField('游戏APPKEY', max_length=50, db_index=True)
    channel = models.ManyToManyField(Channel, verbose_name='渠道')

    class Meta:
        db_table = u'conference'
        app_label = get_app_label()
        ordering = ('id',)


Resource.register('channel', Channel)
Resource.register('agent', Agent)
Resource.register('Conference', Conference)
