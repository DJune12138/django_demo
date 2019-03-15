#encoding:utf-8

import datetime
from django.db import models

class Calevents(models.Model):
    '''日历事件模型 calandar events'''
    creator = models.CharField(u"创建者", max_length=32)
    editor = models.CharField(u"编辑者", max_length=32)
    event = models.CharField(u"事件标题", max_length=100)
    descript = models.CharField(u"时间内容", max_length=500)
    class_name = models.CharField(max_length=32, blank=True, null=True)
    all_day = models.IntegerField(u"是否全天", max_length=2, default=0, choices=((0, "否"), (1, "是")))
    start = models.DateTimeField(u"开始时间")
    end = models.DateTimeField(u"结束时间")
    update_time = models.DateTimeField()

    @classmethod
    def create_event(cls, event_name, desc, operator, start, end, class_name=None):
        """ 增加日历事件接口 """
        class_name = class_name if class_name else "label-info"
        try:
            event = event_name
            c_obj = cls.objects.filter(event=event)
            if len(c_obj) > 0:
                opt_obj = c_obj[0]
                opt_obj.event = event
                opt_obj.descript = desc
                opt_obj.class_name = class_name
                opt_obj.start = start
                opt_obj.end = end
                opt_obj.editor = operator
                opt_obj.save()
            else:
                opt_obj = cls(event=event, creator=operator, descript=desc, start=start, end=end, editor='',
                                    class_name=class_name, update_time=datetime.datetime.now())
                opt_obj.save()
        except Exception,e:
            print ("calevent save error", e)

    def __unicode__(self):
        return "%s_%s" % (self.id, self.admin_id)

    class Meta:
        db_table = u"calendar_events"
        app_label = ""
