# coding: utf-8

import time
import datetime
import calendar


def now_sec():
    return int(time.time())


# 时间戳 -> 字符串  格式输出为YYYY-MM-DD HH:MI:SS
def formatDateTime(Timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(Timestamp))


# 时间戳 -> 字符串  格式输出为YYYY-MM-DD
def formatDate(Timestamp):
    return time.strftime("%Y-%m-%d", time.localtime(Timestamp))


# 时间戳 -> 字符串 输出格式由入参format指定
def formatTimeWithDesc(Timestamp, format):
    return time.strftime(format, time.localtime(Timestamp))


# 字符串 -> 时间戳 字符串格式为YYYYMMDD
def formatDatestamp(Datetime):
    return int(time.mktime(time.strptime(Datetime, "%Y-%m-%d")))


# 字符串 -> 时间戳 字符串格式为YYYY-MM-DD HH:MI:SS
def formatTimestamp(Datetime):
    return int(time.mktime(time.strptime(Datetime, "%Y-%m-%d %H:%M:%S")))


# 字符串 -> 时间戳 字符串格式为format
def formatTimestampFormat(Datetime, format):
    return int(time.mktime(time.strptime(Datetime, format)))


# 日期加减 对形如20180101格式的日期进行天数加减
def date_add(D, Offset):
    ND = int(time.mktime(time.strptime(str(D), "%Y%m%d")) + Offset * 86400)
    return int(time.strftime("%Y%m%d", time.localtime(ND)))


# 返回本周周一0点时间戳
def Monday0():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=-1)

    m1 = calendar.MONDAY

    while True:
        weekday = today.weekday()
        if weekday == m1:
            break

        today += oneday

    PreMonday = today.strftime('%Y%m%d')
    return int(time.mktime(time.strptime(PreMonday, "%Y%m%d")))


# 返回上周从周一开始的0点时间戳
def preMonday0():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=-1)

    m1 = calendar.MONDAY
    pre = 0

    while True:
        weekday = today.weekday()
        if weekday == m1:
            if pre > 0:
                break
            else:
                pre += 1

        today += oneday

    PreMonday = today.strftime('%Y%m%d')

    return int(time.mktime(time.strptime(PreMonday, "%Y%m%d")))


# 今天零点
def today0():
    tt = datetime.datetime.now().timetuple()
    unix_ts = time.mktime(tt)
    return int(unix_ts - tt.tm_hour * 60 * 60 - tt.tm_min * 60 - tt.tm_sec)


def date_str(date):
    d = str(date)
    return d[:4] + "-" + d[4:6] + "-" + d[-2:]


def start(start_time):
    """开始时间，当天0点"""

    return formatDatestamp(start_time)


def end(end_time):
    """结束时间，下一天0点"""

    return formatDatestamp(end_time) + 86400
