#coding=utf-8

import sys, csv, traceback
from django.core.management import BaseCommand
from models.channel import Agent,Channel
from models.log import LogDefine
import random
import os,json
from django.utils.datastructures import SortedDict 
import ConfigParser  
import string  


class Command(BaseCommand):
    '''按 base_table.ini创建基本日志类定义
    '''

    def handle(self, *args, **options):
        if len(args) == 0:
            sys.stdout.write('缺少参数: 请输入菜需要创建的菜单数据文件.')
            return
        else:
            ini_file = args[0]
            if not os.path.isfile(ini_file):
                sys.stdout.write('错误: 无效的文件路径.')
                return
            config = ConfigParser.ConfigParser(dict_type=SortedDict)  
            
            config.read(ini_file)
            print config.sections()
            for section in config.sections():
                opt = dict(config.items(section))
                log_def,created = LogDefine.objects.get_or_create(key=section)
                log_def.key = section.strip()
                log_def.name = opt.get('name')
                log_def.remark = opt.get('remark','')
                log_def.status = LogDefine.Status.CENTER if opt.get('center','') else LogDefine.Status.NORMAL
                field_config = opt.get("config")
                try:
                    log_def.config = json.loads(field_config)
                except:
                    pass
                log_def.save()
                print 'create log_def: %s %s is_center:%s ' % (log_def.key,
                                                                  log_def.name,
                                                                  log_def.status
                                                                    )