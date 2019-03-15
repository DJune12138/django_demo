#coding:utf-8
#一堆工具


import traceback
import hashlib
import json
import decimal
import os,sys
try:
    import cStringIO as StringIO
except:
    traceback.print_exc()
    import StringIO

def mkdirs(path,mode=0755):
    try:
        os.makedirs(path, mode)
    except:
        pass
    
def get_files_from_dir(dir_path,filter_endswith=''):
        for dirpath, dirs, files in os.walk(dir_path):
            for filename in files:
                if  filename.endswith(filter_endswith):
                    yield os.path.join(dirpath,filename)
                        

class DecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, decimal.Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])
        return super(DecimalEncoder, self)._iterencode(o, markers)

def trace_msg(is_log=False):
    '''跟踪消息
    '''
    fp = StringIO.StringIO() 
    traceback.print_exc(file=fp)
    message = fp.getvalue()
    del fp
    return message

def md5(s):
    signStr = hashlib.md5() 
    signStr.update(s.encode('utf-8'))
    return signStr.hexdigest()

def i2sl(num):
    '''整形转36进制
    '''
    loop = '0123456789abcdefghijklmnopqrstuvwxyz'
    n = num
    a = []
    while n != 0:
        a.append( loop[n % 36] )
        n = n / 36
    a.reverse()
    return ''.join(a) 


def filter_sql(sql):
    import re
    p = re.compile( '(update|delete|modify|column|lock|drop|table)', re.I)
    sql = p.sub( '', sql)
    return sql

#时间类的
import time,datetime,re
TIMEFORMAT = '%H:%M:%S'
DATEFORMAT = '%Y-%m-%d'
DATETIMEFORMAT = '%Y-%m-%d %H:%M:%S'
CONVERT_FORMAT = {"datetime":DATETIMEFORMAT, "date":DATEFORMAT, "time":TIMEFORMAT}
def str_to_datetime(datetime_str):
    return datetime.datetime.strptime(datetime_str,DATETIMEFORMAT)

def datetime_to_str(_datetime):
    '''
    @_datetime 要转成字符串datetime对象
    '''
    return _datetime.strftime(DATETIMEFORMAT) 

def timestamp_to_datetime_str(timestamp, _format="datetime"):
    '''
    @timestamp 时间戳转日期时间字符串
    @_format CONVERT_FORMAT
    '''
    if _format not in CONVERT_FORMAT.keys():
        return ""
    return datetime.datetime.fromtimestamp(timestamp).strftime(CONVERT_FORMAT[_format])

def datetime_to_timestamp(datetime_or_str):
    '''
    @datetime_or_str datetime或者日期时间字符串转时间戳
    '''
    if isinstance(datetime_or_str,basestring):
        datetime_or_str = str_to_datetime(datetime_or_str)
    return int(time.mktime(datetime_or_str.timetuple()))

datetime_or_str_to_timestamp = datetime_to_timestamp

def get_now_str():
    '''获取现在时间字符串
    @
    '''
    return datetime.datetime.now().strftime(DATETIMEFORMAT)

def get_today_str():
    '''获取当天字符串
    @
    '''
    return datetime.datetime.now().strftime('%Y-%m-%d')

def get_timezone():
    '''获取当前时区
    @
    '''
    return -time.timezone / 3600

import calendar
def add_months(dt,months):
    '''月份增加
    '''
    month = dt.month - 1 + months
    year = dt.year + month / 12
    month = month % 12 + 1
    day = min(dt.day,calendar.monthrange(year,month)[1])
    return dt.replace(year=year, month=month, day=day)

_DATE_REGEX = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'(?: (?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})'
    r'(?:\.(?P<microsecond>\d{1,6}))?)?')
def convert_to_datetime(input):
    """
    Converts the given object to a datetime object, if possible.
    If an actual datetime object is passed, it is returned unmodified.
    If the input is a string, it is parsed as a datetime.

    Date strings are accepted in three different forms: date only (Y-m-d),
    date with time (Y-m-d H:M:S) or with date+time with microseconds
    (Y-m-d H:M:S.micro).

    :rtype: datetime
    """
    from datetime import date, datetime, timedelta
    if isinstance(input, datetime):
        return input
    elif isinstance(input, date):
        return datetime.fromordinal(input.toordinal())
    elif isinstance(input, basestring):
        m = _DATE_REGEX.match(input)
        if not m:
            raise ValueError('Invalid date string')
        values = [(k, int(v or 0)) for k, v in m.groupdict().items()]
        values = dict(values)
        return datetime(**values)
    raise TypeError('Unsupported input type: %s' % type(input))