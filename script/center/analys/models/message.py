# encoding=utf-8

import datetime
from django.db import models


class Message(models.Model):
    """ 后台消息系统 """
    TYPECHOICES = ((0, '系统消息'), (1, '运营消息'), (2, '其他消息'))
    type = models.IntegerField(u'消息类型', max_length=2, default=0, choices=TYPECHOICES)
    title = models.CharField(u'消息主题', max_length=32)
    content = models.CharField(u'消息内容', max_length=256)
    time = models.DateTimeField(u'时间')

    @classmethod
    def add_msg(cls, itype, title, content):
        if itype not in (0, 1, 2):
            raise Exception("Error type, please choice right one: [(0, '系统消息'), (1, '运营消息'), (2, '其他消息')]")
        cls(type=itype, title=title, content=content, time=datetime.datetime.now())
        cls.save()

    @classmethod
    def get_display_name(cls, field, val_arg):
        for item in getattr(cls, "%sCHOICES" % field.upper()):
            if item[0] == val_arg:
                return item[1]
        return "未知类型"

    def __unicode__(self):
        return "%s_%s" % (self.type, self.title)

    class Meta:
        db_table = u"message"
        app_label = "analys"


class MessageStatus(models.Model):
    """ 消息读取的状态记录 """
    msg = models.ForeignKey(Message)
    admin_id = models.IntegerField(u'用户id', max_length=32)
    read_time = models.DateTimeField(u'读取时间')

    def __unicode__(self):
        return "%s_%s" % (self.msg, self.admin_id)

    class Meta:
        db_table = u"message_status"
        app_label = "analys"