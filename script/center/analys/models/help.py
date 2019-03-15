#coding=utf-8
from django.db import models
from settings import get_app_label
class Help(models.Model):
    parent_id =models.IntegerField( max_length = 12)
    order = models.IntegerField(u'排序', max_length = 10)
    filename = models.CharField(u'标题',max_length=20)
    title = models.CharField(u'标题',max_length=100)
    content = models.TextField(u'内容')

    def __unicode__(self):
        return 'id:%,parent_id:%' % (self.id,self.parent_id)

    def get_parent_id_name(self):
        catgory = HelpCategory.objects.get(id=self.parent_id)
        return catgory.name
        
    class Meta:
        db_table = 'help'
        app_label = get_app_label()
        ordering = ('order',)

#类别表
class HelpCategory(models.Model):
    order = models.IntegerField(u'排序', max_length = 10)
    name = models.CharField(u'名称', max_length = 50)

    def __unicode__(self):
        return 'id:%,name:%' % (self.id,self.name)

    class Meta:
        db_table = 'help_category'
        app_label = get_app_label()
        ordering = ('order',)