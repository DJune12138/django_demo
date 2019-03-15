#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 打印常用命令
import sys
import os
import imp
import json
import socket 
from urlparse import urlparse

import MySQLdb


MYSQL_CMD = 'mysql'
MYSQLDUMP_CMD = 'mysqldump'


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
settings_path = os.path.join(BASE_DIR, 'center/analys/settings')



def _import(raw_path):
    path, name = os.path.split(raw_path)
    if path:
        fp, path, desc = imp.find_module(name, [path,])
    else:
        fp, path, desc = imp.find_module(name)

    try:
        return imp.load_module(name, fp, path, desc)
    finally:
        if fp:
            fp.close()


def get_manage_mysql():
    tables = 'def_log def_dict query_new statistic_new menu_new def_gm'

    result = []
    for database in ['default', 'read', 'write', 'card']:
        db = settings.DATABASES[database]
        db_connect_cmd = "game {database}\t: {mysql} -u{user} -p'{password}' -P{port} -h{host} {name}".format(
                mysql=MYSQL_CMD,
                user=db['USER'],
                password=db['PASSWORD'],
                port=db['PORT'], 
                host=db['HOST'],
                name=db['NAME'],
                database=database
                )
        result.append(db_connect_cmd)

    db = settings.DATABASES['default']
    db_export_cmd = "update dump\t: {mysqldump} -u{user} -p'{password}' -P{port} -h{host} {name} {table} > {name}_update.sql".format(
            mysqldump=MYSQLDUMP_CMD,
            user=db['USER'], 
            password=db['PASSWORD'],
            port=db['PORT'], 
            host=db['HOST'],
            name=db['NAME'],
            table=tables)

    result.append(db_export_cmd)

    db = settings.DATABASES['default']
    conn = MySQLdb.connect(
        host    = db['HOST'],
        port    = int(db['PORT']),
        user    = db['USER'],
        passwd  = db['PASSWORD'],
        db      = db['NAME'],
        charset = "utf8"
    )

    try:
        cursor = conn.cursor()
        query_sql = 'select id, f1, f2 from log_backstage'
        cursor.execute(query_sql)
        result.append('update sync  :')
        for s in cursor.fetchall():
            server = s[-2]
            if u'内网' in server:
                continue
            hostname = urlparse(s[-1]).hostname
            ip = socket.gethostbyname(hostname)
            update_sync_cmd = "  {server}\t: rsync -v -e 'ssh -p22' {name}_update.sql  {ip}:/data/www/update/".format(name=db['NAME'], ip=ip, server=s[-2])
            result.append(update_sync_cmd)
    except:
        pass

    return result


def get_game_mysql():
    db = settings.DATABASES['default']
    conn = MySQLdb.connect(
        host    = db['HOST'],
        port    = int(db['PORT']),
        user    = db['USER'],
        passwd  = db['PASSWORD'],
        db      = db['NAME'],
        charset = "utf8"
    )
    cursor = conn.cursor()
    query_sql = 'select id, name, log_db_config from servers'
    cursor.execute(query_sql)
    for s in cursor.fetchall():
        log_db_config = json.loads(s[2])
        # print json.dumps(log_db_config, indent=2)
        yield "{server}[{id}] : {mysql} -u{user} -p'{password}' -P{port} -h{host} {name}".format(
            id=s[0],
            server=s[1],
            sep=':',
            mysql=MYSQL_CMD,
            user=log_db_config['user'],
            password=log_db_config['password'],
            port=log_db_config['port'],
            host=log_db_config['host'],
            name=log_db_config['db'])



def print_sep():
    print '-' * 64 + '\n'


def main():
    manage_cmd_list = get_manage_mysql()
    print_sep()
    for cmd in manage_cmd_list:
        print cmd
    print_sep()

    for i in get_game_mysql():
        print i

settings = _import(settings_path)
if __name__ == '__main__':
    main()
