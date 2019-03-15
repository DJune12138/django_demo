# -*- coding: utf-8 -*-

from django.db import models
from django.db import models
from django.db import connection, connections
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute)

import datetime
import json
import pymongo
import MySQLdb
import traceback
from settings import get_app_label, account_prefix, STATIC_ROOT, STATIC_URL
from models.server import Server, Group
from models.channel import Channel, Agent, ChannelOther
import os, sys
import time
import hashlib


def get_time_str(time):
    if time == '' or time == None:
        return ''
    return time.strftime('%Y-%m-%d %H:%M:%S')


def md5(sign_str):
    signStr = hashlib.md5()
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()


class UserType(models.Model):
    name = models.CharField(u'类型名称', max_length=32)
    type_id = models.IntegerField(u'玩家类型', default=0, db_index=True)
    func_name = models.CharField(u'登录方法', max_length=20, db_index=True)
    func_ver = models.IntegerField(u'登录方法版本', default=0)
    login_config = models.CharField(u'登录设置', max_length=1000)
    remark = models.CharField(u'备注', max_length=200)

    class Meta:
        db_table = u'user_type'
        app_label = get_app_label()
        ordering = ('id',)


class Auth(models.Model):
    TYPE_CHOICES = ((0, 'Facebook'), (1, 'QQ空间'), (2, '新浪微博'), (3, '人人网'),)
    auth_type = models.IntegerField(u'授权类型', default=0, choices=TYPE_CHOICES)
    user_type = models.IntegerField(u'账号类型', default=0, choices=TYPE_CHOICES)
    link_key = models.CharField(u'关联第三方的登录标识', max_length=50)
    access_token = models.CharField(u'授权码', max_length=100)

    class Meta:
        db_table = u'auth'
        app_label = get_app_label()
        ordering = ('id',)


class User(models.Model, BaseModelMixin):
    STATUS_CHOICES = (
    (-4, "封设备"), (-3, "封IP"), (-2, '删号'), (-1, '封号'), (0, '正常'), (1, '游客'), (2, 'VIP'), (3, '测试'), (4, '白名单'))
    TYPE_CHOICES = ((0, '自营'), (1, '当乐'), (2, 'UC'), (3, '91'), (4, '云游'), (5, '飞流'), (6, '乐逗'), (8, '小虎'),)
    RECHARGE_STATUS = ((0, '非标记用户'), (1, '充值返利未发送'), (2, '充值返利已发送'), (3, '物品奖励未发送'), (4, '物品奖励已发送'),)

    username = models.CharField(u'用户名', max_length=128, db_index=True)
    password = models.CharField(u'密码', max_length=32)
    user_type = models.IntegerField(u'账号类型', default=0, db_index=True)
    link_key = models.CharField(u'关联第三方登录的KEY', db_index=True, max_length=50)
    create_time = models.DateTimeField(u'最后登录时间', auto_now_add=True, db_index=True)
    last_time = models.DateTimeField(u'最后登录时间', auto_now_add=True, db_index=True)
    last_ip = models.CharField(u'最后登录IP', max_length=32)
    last_key = models.CharField(u'最后一次验证参数', max_length=50, blank=True, null=True)
    last_server = models.CharField(u'最后登录的服务器', max_length=50, blank=True, null=True)
    login_num = models.IntegerField(u'登录次数', default=1)
    lock_time = models.DateTimeField(u'账号锁定时间', null=True, blank=True)
    login_count = models.IntegerField(u'尝试登陆次数', default=0)

    status = models.IntegerField(u'账号状态', default=0, choices=STATUS_CHOICES)

    channel_key = models.CharField(u'渠道关键字', max_length=20)
    mobile_key = models.CharField(u'手机串号', max_length=50)
    recharge_status = models.CharField(u'充值返还用户标记', max_length=50, default=0)

    other = models.CharField(u'其它信息,其他用户类型用来存储密码', max_length=500, blank=True, null=True)
    other_data = models.CharField(u'其它信息,白名单用户用来存储部门姓名', max_length=1000, null=True)
    clientId = models.IntegerField(u'客户ID', null=False)

    def __unicode__(self):
        return '%d_%s' % (self.user_type, self.username)

    SIGN_KEY = 'testkey'

    def get_user_key(self):
        '''生成签名key和时间戳
        '''
        timestamp = int(time.time())
        if self.user_type == 0:
            self.link_key = self.id
        user_key = md5('%s&%s&%s' % (self.link_key, timestamp, self.SIGN_KEY))

        if self.user_type > 0:  # 其他平台生成sign:用户类型_关联标示_sign
            user_key = '%s_%s_%s' % (self.user_type, self.link_key, user_key)
        return user_key, timestamp

    def set_guest_username(self):
        '''设置游客账号
        '''
        self.username = '%s_%s' % (account_prefix, str(self.id).rjust(8, '0'))

    def user_type_name(self):
        return self.TYPE_CHOICES.get(self.user_type, '未知')

    def create_time_str(self):
        return get_time_str(self.create_time)

    def last_time_str(self):
        return get_time_str(self.last_time)

    def is_lock(self):
        if self.status < 0:
            return True
        else:
            return False

    class Meta:
        db_table = u'users'
        app_label = get_app_label()
        ordering = ('-id',)


class UserInfo(models.Model):
    '''账号的其他信息
    '''

    user_type = models.IntegerField(u'账号类型', default=0, db_index=True)
    channel_id = models.CharField(u'渠道id', db_index=True, max_length=20)
    link_key = models.CharField(u'关联第三方登录的KEY', db_index=True, max_length=50)
    info = models.TextField(u'其它信息', null=True, default="")

    class Meta:
        db_table = u'users_info'
        app_label = get_app_label()
        ordering = ('-id',)


class SafeQuestion(models.Model):
    user = models.ForeignKey(User)
    question = models.CharField(u'安全问题', max_length=100)
    answer = models.CharField(u'安全答案', max_length=100)
    create_time = models.DateTimeField(u'设置时间', default=datetime.datetime.now, db_index=True)

    class Meta:
        db_table = u'safe_question'
        app_label = get_app_label()


class Notice(models.Model):
    class Notine_Type:
        scroll = 1
        game = 2
        group = 3
        push = 4
        login = 5

    TYPE_DICT = {
        # Notine_Type.game:{"name":'小公告',"path":"game"},
        # Notine_Type.group:{"name":'分区首页公告',"path":"login"},
        # Notine_Type.game:{"name":'世界公告',"path":"game"},
        Notine_Type.game: {"name": '最新消息', "path": "login"},
        Notine_Type.push: {"name": '推送消息', "path": "push"},
        Notine_Type.login: {"name": '登录弹窗公告', "path": "login"},
    }

    STATUS_CHOICES = ((0, '隐藏'), (1, '显示'),)

    TYPE_CHOICES = [(k, v['name']) for k, v in TYPE_DICT.items()]

    TAG_CHOICES = ((0, '新'), (1, '重要'), (2, '紧急'),)

    channel = models.ManyToManyField(Channel)
    server = models.ManyToManyField(Server)
    group = models.ManyToManyField(Group)
    client_ver = models.CharField(u'针对客户端版本', max_length=50, default='')
    title = models.CharField(u'消息标题', max_length=200)
    sub_title = models.CharField(u'消息副标题', max_length=200)
    content = models.TextField(u'消息内容')
    link_url = models.CharField(u'消息链接', max_length=100, blank=True)
    begin_time = models.DateTimeField(u'公告开始时间', default=datetime.datetime.now, db_index=True)
    end_time = models.DateTimeField(u'公告过期时间', default=datetime.datetime.now, db_index=True)
    create_time = models.BigIntegerField(u'公告生成时间戳', default=int(time.time()), db_index=True)
    status = models.IntegerField(u'状态', default=0, choices=STATUS_CHOICES)
    pub_ip = models.CharField(u'操作人IP地址', max_length=20)
    pub_user = models.IntegerField(u'操作人ID', db_index=True)
    notice_type = models.IntegerField(u'类型', default=0, choices=TYPE_CHOICES)
    intervalSecond = models.IntegerField(u'间隔时间', default=0)
    size = models.CharField(u'显示的size', max_length=20, default='0.9,0.9')
    tag = models.IntegerField(u'公告标记', default=0, choices=TAG_CHOICES)
    is_temp = models.IntegerField(u'是否开服模版', default=0)
    sort = models.IntegerField(u'公告排序', default=0)
    photo_id = models.IntegerField(u'推送公告图片ID', default=0)
    jump = models.CharField(u'跳转函数', max_length=100)

    def is_scroll_notice(self):
        return self.notice_type == Notice.Notine_Type.scroll

    def is_game_notice(self):
        return self.notice_type == Notice.Notine_Type.game

    def is_group_notice(self):
        return self.notice_type == Notice.Notine_Type.group

    def is_login_notice(self):
        return self.notice_type == Notice.Notine_Type.login

    def begin_time_str(self):
        return get_time_str(self.begin_time)

    def end_time_str(self):
        return get_time_str(self.end_time)

    def in_time_range(self):
        return self.begin_time <= datetime.datetime.now() <= self.end_time

    class Meta:
        db_table = u'notice'
        app_label = get_app_label()
        ordering = ('notice_type',)


class Upgrade(models.Model):
    ver_num = models.IntegerField(u'新版本号', default=0)
    ver_name = models.CharField(u'新版本名称', max_length=20)
    filesize = models.CharField(u'文件包大小', max_length=10)
    channel = models.ManyToManyField(Channel)
    group = models.ManyToManyField(Group)
    client_ver = models.CharField(u'针对客户端版本', max_length=50, default='')
    min_client_ver = models.CharField(u'最低客户端版本', max_length=50, default='')
    download_url = models.CharField(u'下载包路径', max_length=500)
    ios_url = models.CharField(u'ios整包更新地址', max_length=500)
    android_url = models.CharField(u'android整包地址', max_length=500)
    increment_url = models.CharField(u'增量包更新地址', max_length=500)
    subpackage_url = models.CharField(u'分包下新地址', max_length=500)
    md5_num = models.CharField(u'分包下新地址', max_length=500)
    page_url = models.CharField(u'下载页面URL', max_length=500)
    remark = models.CharField(u'更新备注', max_length=500)
    create_time = models.DateTimeField(u'发布时间', default=datetime.datetime.now, auto_now_add=True)
    pub_ip = models.CharField(u'操作人IP地址', max_length=20)
    pub_user = models.IntegerField(u'操作人ID', db_index=True)
    notice_switch = models.IntegerField(u'关闭健康游戏公告', default=0)

    def create_time_str(self):
        return get_time_str(self.create_time)

    class Meta:
        db_table = u'upgrade'
        app_label = get_app_label()
        ordering = ('-ver_num',)


class Question(models.Model):
    TYPE_MAP = ((0, 'BUG'), (1, '投诉'), (2, '建议'), (3, '其他'), (4, '战报'))

    server_id = models.IntegerField(db_index=True)
    channel_id = models.IntegerField(default=0, db_index=True)
    question_type = models.IntegerField(choices=TYPE_MAP)  # BUG 0 投诉 1 建议 2 其他3
    status = models.IntegerField(default=0, db_index=True)  # 已回复 1 #已查看 2 #未回复 0 #忽略 3以上
    question = models.CharField(max_length=400)
    answer = models.CharField(max_length=400)
    post_time = models.DateTimeField(auto_now_add=True, db_index=True)
    reply_time = models.DateTimeField(blank=True, null=True, db_index=True)
    post_user = models.IntegerField(default=0, db_index=True)
    post_user_id = models.IntegerField(default=0, db_index=True)
    # post_user=models.ForeignKey(User)
    score = models.IntegerField(default=-1, db_index=True)
    reply_user = models.CharField(max_length=20, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    info = models.CharField(max_length=1000)

    check_time = models.DateTimeField(blank=True, null=True, db_index=True)  # 用户查看回复时间
    order_time = models.DateTimeField(blank=True, null=True, db_index=True)  # 客服接单时间
    order_user = models.CharField(max_length=20, default="")
    session_id = models.IntegerField('会话id', default=0)

    def __unicode__(self):
        return '%d_%s' % (self.post_user_id, self.post_time.strftime('%Y-%m-%d'))

    def post_time_str(self):
        return get_time_str(self.post_time)

    def reply_time_str(self):
        s = ''
        if self.reply_time != None and self.reply_time != '':
            s = self.reply_time.strftime('%Y-%m-%d %H:%M:%S')

        return s

    class Meta:
        db_table = u'question'
        ordering = ('-id',)
        app_label = get_app_label()


class QuestionOther(models.Model):
    '''问题的附属
    '''
    TYPE_MAP = ((0, '普通BUG反馈'), (1, '战斗战报BUG反馈'))
    qid = models.IntegerField('问题ID', db_index=True)
    type = models.IntegerField('类型', choices=TYPE_MAP)
    data = models.TextField('数据')

    SAVE_DIR_NAME = 'last_report'
    LAST_REPORT_SAVE_PATH = os.path.join(STATIC_ROOT, SAVE_DIR_NAME)
    try:
        os.makedirs(LAST_REPORT_SAVE_PATH, 0755)
    except:
        pass

    def get_last_report_path(self):
        return os.path.join(self.LAST_REPORT_SAVE_PATH, '%s.br' % self.qid)

    def get_last_report_url(self):
        return '%s%s/%s' % (STATIC_URL, self.SAVE_DIR_NAME, '%s.br' % self.qid)

    class Meta:
        db_table = u'question_other'
        app_label = get_app_label()


class Voice(models.Model):
    '''语音文件保存
    '''
    player_id = models.IntegerField('角色ID', db_index=True)
    server_id = models.IntegerField('服务器ID', db_index=True)
    channel_id = models.IntegerField('服务器ID', db_index=True)
    voice_path = models.FileField(upload_to='voice')

    class Meta:
        db_table = u'voice'
        app_label = get_app_label()


class BlockUser(models.Model):
    user = models.ForeignKey(User)
    server = models.ForeignKey(Server)

    class Meta:
        db_table = u'block_user'
        ordering = ('-id',)
        app_label = get_app_label()


class VipList(models.Model):
    '''vip玩家保存
    '''
    TYPE_CHOICES = ((0, '未验证'), (1, '未领取'), (2, '已领取'))
    player_id = models.IntegerField('角色ID', db_index=True)
    server_id = models.IntegerField('服务器ID', db_index=True)
    privilege_type = models.IntegerField('特权礼包状态', default=0, choices=TYPE_CHOICES)
    everyday_type = models.IntegerField('每日礼包状态', default=1, choices=TYPE_CHOICES)

    class Meta:
        app_label = get_app_label()
        db_table = u'viplist'


class RebateUser(models.Model):
    '''
    删档返利的用户
    '''
    REBATE_STATUS = ((0, '未发送'), (1, '已发送'))
    LOGIN_REWARD = ((0, '否'), (1, '是'))

    username = models.CharField(u'用户名', max_length=128, db_index=True)
    rebate_status = models.IntegerField(u'返利类型', default=0, choices=REBATE_STATUS)
    expire_time = models.DateTimeField(u'返还过期时间', auto_now_add=True, db_index=True)
    server_id = models.IntegerField('创角服务器ID', db_index=True)
    last_time = models.DateTimeField(u'最后操作时间', auto_now_add=True)
    pay_reward = models.IntegerField(u'充值数返利', default=0)
    login_reward = models.IntegerField(u'连续登录奖励', default=0, choices=LOGIN_REWARD)
    other_reward = models.CharField(u'其他返利', max_length=100)

    class Meta:
        db_table = u'rebate_user'
        app_label = get_app_label()


class BanIpList(models.Model):
    '''
    封禁IP的列表
    '''
    STATUS_CHOICES = ((-3, '封IP'), (0, '正常'), (4, '白名单'))

    username = models.CharField(u'用户名', max_length=128)
    ip = models.CharField(u'最后登录IP', max_length=32, unique=True)
    last_time = models.DateTimeField(u'最后记录时间', auto_now_add=True)
    status = models.IntegerField(u'账号状态', default=0, choices=STATUS_CHOICES)
    other = models.CharField(u'其它信息', max_length=500, blank=True, null=True)
    f1 = models.IntegerField(u"开启OR关闭", max_length=100, default=0, null=True, blank=True)
    f2 = models.IntegerField(u"1个IP最大角色数", max_length=100, default=0, null=True, blank=True)

    class Meta:
        db_table = u'banip_list'
        app_label = get_app_label()
