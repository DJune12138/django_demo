#coding:utf-8
#django 连接数据库的东东


from django.db import transaction,connections


def reconnect_db(alias='default'):
    try:connections[alias].connection.ping()
    except:connections[alias].close()

