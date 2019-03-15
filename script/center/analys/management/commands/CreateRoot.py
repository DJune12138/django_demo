#coding:utf-8
#创建root管理员命令



from django.core.management.base import BaseCommand, CommandError

from models.admin import Admin
from django.forms import ModelForm  

import pprint
from django.db.models.base import ModelBase
    
class Command(BaseCommand):
    help = '创建root管理员'

    def handle(self, *args, **options):
        Admin.create_root()
