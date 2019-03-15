# coding=utf-8
#

from django.db import models
from server import Server
import datetime,time
import json
from .base import (BaseModelMixin,
                   CacheAttribute,
                   CachedClassAttribute,
                   JSONField)
        
from settings import get_app_label   
from util import datetime_to_str,trace_msg
    
        
class Activity(models.Model,BaseModelMixin):
    '''游戏活动模型
    '''
    
    TYPE_MAP = {
                } 
    AUTO_ON_LIST = set()
    AUTO_OFF_LIST = set()

    NOT_CONFLICT_CHECK_LIST = set()

    TYPE_ID = {u'七天热卖':7,u'累积单笔充值':9,u'每日累充':10,u"累积登陆":11,
    u'战力排行':12,u'部族排行':13,u'等级排行':14,u'限时礼包':15,u'部族名门':16,
    u'部族管理排行':17,u'宠物排行榜':18,u'充值积分活动':19,u'兑换活动':21,
    u"活跃活动":23,u'超值特卖':24,u'轩辕传奇':25,u"羽化登仙":26,u"福气红包":27,
    u"福气砸蛋":28,u"福气烟花":29,u"幻境副本":33,u"怪物嘉年华":34,u"BOOS嘉年华":35,
    u"充值大返利":36}

    STATUS_CHOICES = ((0,'未开始'),(1,'关闭成功'),(2,'开启成功'),(3,'服务器配置异常'),)

    name = models.CharField('活动名称',max_length=50,db_index=True)
    info = models.CharField('活动详情',max_length=1000)
    type = models.CharField('活动类型',max_length=20,db_index=True)
    sdate = models.DateTimeField('活动开启时间',null=False)
    edate = models.DateTimeField('活动结束时间',null=False)
    msg = models.TextField('活动配置JSON串',null=False,default="{}")
    server = models.ManyToManyField(Server,verbose_name="活动参与的服务器") 
    is_auto = models.IntegerField('是否自动开启',default=1)
    is_auto_off = models.IntegerField('是否自动关闭', default=0)
    is_temp = models.IntegerField('是否开服模版', default=0)
    status = models.IntegerField('活动状态',choices=STATUS_CHOICES,default=0)

    server_ids = []

    @property
    def msg_obj(self):
        try:
            return json.loads(self.msg)
        except:
            return {}
        
    @property
    def now(self):
        return datetime.datetime.now()
    
    @property
    def timestamp(self):
        return int(time.time())

    
    @property
    def activity_template(self):
        return 'game/%s.html' % self.type if self.type else ''
    
    @classmethod
    def activity_id(cls,Type):
        return cls.TYPE_ID[Type] or 0

    @classmethod
    def  register(cls,activity_type_name,activity_protocol_class):
        activity_type_name = unicode(activity_type_name)
        cls.TYPE_MAP[activity_type_name] = activity_protocol_class
        if getattr(activity_protocol_class,'IS_AUTO_ON'):
            cls.AUTO_ON_LIST.add(activity_type_name)           #如果是添加属性
        if getattr(activity_protocol_class,'IS_AUTO_OFF'):
            cls.AUTO_OFF_LIST.add(activity_type_name)
        if getattr(activity_protocol_class,'NOT_CONFLICT_CHECK'):
            cls.NOT_CONFLICT_CHECK_LIST.add(activity_type_name)    #如果是添加属性表示没有
            
    def get_activity_protocol_class(self):
        return self.__class__.TYPE_MAP.get(unicode(self.type),None)
    
    def delete(self,*args,**kwargs):
        self.server.clear()
        super(Activity,self).delete(*args,**kwargs)
        
    def save(self,*args,**kwargs):

        _r = super(Activity,self).save(*args,**kwargs)
        if self.server_ids:
            self.server.clear()
            self.server.add(*Server.objects.using(self.__class__.objects.db).filter(id__in=self.server_ids))
        return _r
        
    
    class Meta: 
        db_table = u'game_activity'
        app_label = get_app_label()
        

class ActivityTemplate(models.Model,BaseModelMixin):
    name = models.CharField('活动模版名',max_length=50,null=False)
    type = models.CharField('活动模版类型',max_length=20,null=False,db_index=True)
    msg = models.TextField('活动模版配置JSON串',null=True,default="{}")
    create_time = models.DateTimeField('模版创建时间',null=False,auto_now_add=True)
    create_user_name = models.CharField('模版创建者名',max_length=20)
    info = models.CharField('模版详情',max_length=1000)
    
    @property
    def msg_obj(self):
        try:
            return json.loads(self.msg)
        except:
            return {}
    
    def save(self,*args,**kwargs):
        if isinstance(self.msg,(dict,list)) :
            try:self.msg = json.dumps(self.msg,ensure_ascii=False)
            except:self.msg = '{}'
            
        super(ActivityTemplate,self).save(*args,**kwargs)
    
    class Meta: 
        db_table = u'game_activity_template'
        app_label = get_app_label()
        ordering = ('id',)
        

class Mail(models.Model,BaseModelMixin):

    STATUS_CHOICES = ((0,'未审核'),(1,'审核成功'),(2,'审核失败'),)
    TYPE_CHOICES = ((0,'个人'),(2,'全服'),(3,'联远商ID'))

    title = models.CharField('邮件标题',max_length=50,db_index=True)
    content = models.CharField('邮件内容',max_length=1000)
    bonus_content = models.CharField('奖励内容',max_length=1000)
    status = models.IntegerField('状态',default=0,choices=STATUS_CHOICES,db_index=True)
    type = models.IntegerField('类型',default=0,choices=TYPE_CHOICES) 
    create_time = models.DateTimeField('创建时间',auto_now_add=True)
    server_ids = models.CharField('服务器',max_length=1000)
    channel_id = models.IntegerField('渠道',null=True,max_length=15)
    player_id = models.CharField('收信用户',max_length=1000,db_index=True,null=True)
    Applicant = models.CharField('发送人',max_length=50,db_index=True,null=False)
    Auditor = models.CharField('审核人',max_length=50,db_index=True,null=True)

    def delete(self,*args,**kwargs):
        super(Mail,self).delete(*args,**kwargs)

    class Meta:
        db_table = u'mail_list'
        app_label = get_app_label()


class BattleList(models.Model,BaseModelMixin):

    WORLD_LEVEL = {39: 1, 49: 3, 59: 8,69: 15, 79: 25, 89: 39, 99: 61}
    STATUS_CHOICES = ((0,u'未发送'),(1,u'已发送'),(2,u'已结算'),)

    server = models.IntegerField('server_id',db_index = True,null=False)
    create_time = models.DateTimeField(u'开服时间',null=False)
    last_time = models.DateTimeField(blank=True,null=True)
    run_time = models.DateTimeField(u'执行时间',blank=True,null=True)
    sort = models.IntegerField('一组9个,从1开始',null=True,max_length=10)
    group = models.CharField('分组,3个服务器为1组ABC',null=True,max_length=10)
    sub_group = models.CharField('子分组,123',null=True,max_length=10)
    sub_server = models.CharField('子服务器',null=True,max_length=100)
    version = models.IntegerField('服务器分区的版本号',null=True,max_length=20)
    f1 = models.CharField(u'魔星积分',max_length=100, default='',null=True, blank=True)
    f2 = models.CharField(u'荒兽积分',max_length=100, default='',null=True, blank=True)
    f3 = models.CharField(u"战场排名",max_length=100, default='',null=True, blank=True)
    f4 = models.CharField(max_length=100, default='',null=True, blank=True)
    f5 = models.CharField(max_length=100, default='',null=True, blank=True)
    f6 = models.TextField(default='',null=True, blank=True)
    f7 = models.CharField(max_length=100, default='',null=True, blank=True)
    f8 = models.TextField(default='',null=True, blank=True)
    status = models.IntegerField('状态',default=0,choices=STATUS_CHOICES,db_index=True)

    def world_level(self):
        distance_day = (datetime.datetime.now() - self.create_time).days + 1
        last_level = 0
        for k,v in self.WORLD_LEVEL.iteritems():
            if distance_day >= v :
                last_level = k if last_level < k else last_level
        return last_level if last_level else 39

    def create_time_str(self):
        return datetime_to_str(self.create_time) if self.create_time else ''

    def get_status(self):
        if self.status:
            for s in self.STATUS_CHOICES:
                if self.status == s[0]:
                    return s[1]
        return self.STATUS_CHOICES[0][1]

    class Meta:
        db_table = u'battle_list'
        app_label = get_app_label()










