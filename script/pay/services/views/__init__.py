# -*- coding: utf-8 -*-

from models.server import Server
from settings import DATABASES
import hashlib,MySQLdb,json

def md5(sign_str):
    signStr=hashlib.md5() 
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()
        


def hash256(sign_str):
    signStr=hashlib.sha256() 
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()

conn_list = {}
server_list = {}
conn_str = {}
tmp_cfg  = DATABASES.get('read')
conn_str['host'] = tmp_cfg.get('HOST')
conn_str['user'] = tmp_cfg.get('USER')
conn_str['password'] = tmp_cfg.get('PASSWORD')
conn_str['db'] = tmp_cfg.get('NAME')
conn_str['port'] = int(tmp_cfg.get('PORT'))



def getConn(server_id=0,is_reload=0,alias='read',logic_db=None):
    the_conn = conn_list.get(server_id,None)
    the_conn_str = {}
    if the_conn == None:
        try:
            if server_id==0:
                tmp_cfg  = DATABASES.get(alias)
                conn_str['host'] = tmp_cfg.get('HOST')
                conn_str['user'] = tmp_cfg.get('USER')
                conn_str['password'] = tmp_cfg.get('PASSWORD')
                conn_str['db'] = tmp_cfg.get('NAME')
                conn_str['port'] = int(tmp_cfg.get('PORT'))

                the_conn_str = conn_str
            else:
                if server_list.get(server_id,None)==None:
                    getServer(1)
                the_conn_str = server_list[server_id]['db_config']

            db_name = the_conn_str['db']
            if logic_db:
                db_name = "ss_logic%s"%server_id

            the_conn = MySQLdb.connect(host=the_conn_str['host'],user=the_conn_str['user'],passwd=the_conn_str['password'],port=the_conn_str.get('port',3306),db=db_name,charset='utf8')
            the_conn.autocommit(1) 
            conn_list[server_id]=the_conn
        except Exception,e:
            print('mysql has error0:%d,%s'%(server_id,e))
    try:
        the_conn.ping()
    except Exception,e:
        print('mysql has error1:%d,%s'%(server_id,e))
        if is_reload==0:
            conn_list[server_id] = None
            server_list[server_id] = None
            return getConn(server_id,1)
    return the_conn

def getServer(is_reload=0):
    if len(server_list)==0 or is_reload==1:
        query_sql = 'select id,game_addr,log_db_config,json_data from servers'
        cursor = getConn().cursor()
        cursor.execute(query_sql)
        list_server = cursor.fetchall()
        for item in list_server:
            try:
                item = list(item)
                #print('server item',item)
                if item[2]=='':
                    item[2]='{}'
                item[3] = '{%s}' % item[3]
                server_list[int(item[0])] = {'game_addr':item[1],'db_config':json.loads(item[2]), 'json_data':json.loads(item[3])}
            except Exception,e:
                print('load server db_config has error %s'%item[0],e)


def filter_sql(sql):
    sql = str(sql)
    sql = sql.lower()
    sql = sql.replace('update', '')
    sql = sql.replace('delete', '')
    sql = sql.replace('modify', '')
    sql = sql.replace('column', '')
    sql = sql.replace('lock', '') 
    sql = sql.replace('drop', '')
    sql = sql.replace('table', '')
    sql = sql.replace('contains', '')
    sql = sql.replace('\'', '')
    sql = sql.replace('*', '')
    sql = sql.replace('%%', '')
    
    return sql


def query_player(user_type, openid, server_id):
    player = {'user_id':0, 'player_id':0, 'player_name':'', 'level':0, 'server_id':0}
    try: 
        player['server_id'] = server_id
        if server_id > 0 and openid != '':
            openid = filter_sql(str(openid))
            
            user_type = user_type
            
            server = Server.objects.get(id=server_id)
            the_db_config = json.loads(server.log_db_config)
            conn = MySQLdb.connect(host=the_db_config['host'], user=the_db_config['user'], passwd=the_db_config['password'], port=the_db_config.get('port',3306), db=the_db_config['db'], charset="utf8")
            cursor = conn.cursor()
            
            query_sql = 'select player_id,player_name from player_%d where user_type=%d and link_key="%s"' % (server_id, user_type, openid)
            query_exists_sql = 'SELECT COUNT(0) c FROM information_schema.TABLES WHERE TABLE_NAME="log_current_level"'
            
            cursor.execute(query_exists_sql)
            exists = int(cursor.fetchone()[0])
           
            cursor.execute(query_sql)
            player_list = cursor.fetchall() 
              
            if len(player_list) > 0:
                if exists:
                    try:
                        query_level_sql = 'SELECT log_data FROM log_current_level WHERE log_user = %s' % player_list[0][0]
                        cursor.execute(query_level_sql)
                        tmp_list = cursor.fetchall()
                        if tmp_list.__len__() >= 1:
                            level = int(tmp_list[0][0])
                            player['level'] = level
                    except Exception, ex:
                        print ex
                player['user_id'] = openid
                player['player_id'] = player_list[0][0]
                player['player_name'] = player_list[0][1]
    except Exception, ex:
        print 'query player error:'
        print ex
    
    return player