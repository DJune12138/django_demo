#coding:utf-8
#日志类
#


import time,os,sys
from settings import PROJECT_ROOT,LOGGING


#_PATH = os.path.dirname(__file__)
#_LogConfingFileName = os.path.join(PROJECT_ROOT,'logging.ini')
#logging.config.fileConfig(_LogConfingFileName)
import logging
from logging.handlers import TimedRotatingFileHandler
if sys.version_info < (2,7):
    import dictConfig
    dictConfig.dictConfig(LOGGING)
else:
    import logging.config
    logging.config.dictConfig(LOGGING)

#使用django 的logging
class Logger(object):
    '''#使用django 的logging
    @name 记录的名字 需在setting里设置
    '''
    def __new__(cls,name='root'):
         logger = logging.getLogger(name)
         return logger

def TimedRotatingLogger(name):
    log_format = '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    logging.basicConfig(format=log_format)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    file_ha = TimedRotatingFileHandler('%s.log' % name,when='h',interval=24,encoding='utf-8')
    file_ha.setLevel(logging.DEBUG)
    file_ha.setFormatter(formatter)
    logger.addHandler(file_ha)
    return logger
                    

if __name__ == '__main__':
    log = Logger('cache')
    log.info('info')
    log.critical('critical')
    log.warn('warn')
    log.error('error')


