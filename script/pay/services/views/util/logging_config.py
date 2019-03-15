# -*- coding: utf-8 -*-
#
#django logging的配置
#

import os
from settings import PROJECT_ROOT
from  logging.handlers import TimedRotatingFileHandler
import logging

LOGS_DIR = os.path.join(PROJECT_ROOT,'logs')

def TimedRotatingLogger(name):
    '''返回定时的日志记录
    '''
    log_format = '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    logging.basicConfig(format=log_format)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    file_ha = TimedRotatingFileHandler(os.path.join(LOGS_DIR,'%s.log' % name),when='h',interval=24,encoding='utf-8')
    file_ha.setLevel(logging.INFO)
    file_ha.setFormatter(formatter)
    logger.addHandler(file_ha)
    return logger


def _get_FileHandler_config(dir,filename):
    '''返回一个以日切割的循环日志配置
    '''
    log_dir_path = os.path.join(LOGS_DIR,dir)
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path,0766)
    return {
            'level'    :'DEBUG',
            'class'    :'logging.FileHandler',
            'formatter':'format01',
            'filename' :os.path.join(log_dir_path,filename),
            'encoding' :'utf-8'
            }

def _get_TimedRotatingFile_config(dir,filename):
    '''返回一个以日切割的循环日志配置
    '''
    log_dir_path = os.path.join(LOGS_DIR,dir)
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path,0766)
    return {
            'level'    :'DEBUG',
            'class'    :'logging.handlers.TimedRotatingFileHandler',
            'formatter':'format01',
            'filename' :os.path.join(log_dir_path,filename),
            'when'     :'H',
            'interval' :24,
            'encoding' :'utf-8',
            'backupCount':60,#指定保留的备份文件的个数 
            }


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
         'require_debug_false': {
         '()': 'django.utils.log.RequireDebugFalse'
        }
    },
#=========== handlers start =================
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
             'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'format01'
        },
        'root_handler' : _get_TimedRotatingFile_config('','root.log'),
        'gm_handler'   : _get_FileHandler_config('gm','gm.log'),
        'pay_handler'   : _get_TimedRotatingFile_config('pay','pay.log'),
        'card_handler'   : _get_TimedRotatingFile_config('card','card.log'),
        'statistic_handler'  : _get_TimedRotatingFile_config('statistic','statistic.log'),
    },
#=========== loggers start =================
    'loggers': {
        'django.request': {
            'handlers': ['root_handler'],
            'level': 'ERROR',
            'propagate': True,
        },
        'root':{
            'qualname':'root',
            'level':'DEBUG',
            'handlers':['root_handler','console']
        },
        'gm':{
            'qualname':'gm',
            'level':'DEBUG',
            'handlers':['gm_handler']
        },
        'pay':{
            'qualname':'pay',
            'level':'DEBUG',
            'handlers':['pay_handler']
        },
        'card':{
            'qualname':'card',
            'level':'DEBUG',
            'handlers':['card_handler']
        },
        'cache':{
            'qualname':'cache',
            'level':'DEBUG',
            'handlers':['console']
        },
        'statistic':{# 统计日志
            'qualname':'statistic',
            'level':'DEBUG',
            'handlers':['console','statistic_handler']
        }
    },
           
#=========== formatters start =================
    'formatters':{
        'format01':{
                    'format':'%(asctime)s  %(levelname)s %(name)s pid:%(process)d %(filename)s:%(lineno)d  %(message)s',
                    'datefmt':'[%Y-%m-%d %H:%M:%S]'
                    },
        'format02':{
                    'format':'%(asctime)s  %(levelname)s %(name)s pid:%(process)d %(pathname)s:%(lineno)d  %(message)s',
                    'datefmt':'[%Y-%m-%d %H:%M:%S]'
                    }
                  
    }
}
