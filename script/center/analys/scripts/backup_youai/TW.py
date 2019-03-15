#!/usr/bin/env python
#coding: utf-8
#大陆后台

from models.center import Server,Channel   
from models.pay import PayChannel
from models.log import DictDefine
import os

PREFIX = 'TW'

CHANNEL_DICT = {}#渠道平台
CHANNEL_KEY_DICT = {} #渠道key 对应
EQUIPMENT_NAME_DICT = {}#道具名
EQUIPMENT_ITEM_NAME_DICT = {}#道具项目名
GOLD_ITEM_DICT = {}#金币项目名


SAVE_DIR = '/data/gl_data/'

def get_channel_agent_name():
    '''获取渠道平台名
    '''
    channel_dict = {}
    for o in Channel.objects.using('write').all().values('id','agent_name','name'):
        channel_dict[o['id']] = (o['agent_name'],o['name'])
    return channel_dict
    
def get_dict():
    '''获取id映射字典
    '''
    CHANNEL_KEY_DICT =  DictDefine.objects.get(key='channel_key').dict
    EQUIPMENT_NAME_DICT =  DictDefine.objects.get(key='equipment').dict
    EQUIPMENT_ITEM_NAME_DICT =  DictDefine.objects.get(key='protocol_type').dict
    GOLD_ITEM_DICT =  EQUIPMENT_ITEM_NAME_DICT
    return CHANNEL_KEY_DICT,EQUIPMENT_NAME_DICT,EQUIPMENT_ITEM_NAME_DICT,GOLD_ITEM_DICT
    

def update_dicts():
    global  CHANNEL_DICT,EQUIPMENT_NAME_DICT,EQUIPMENT_ITEM_NAME_DICT,GOLD_ITEM_DICT,CHANNEL_KEY_DICT
    print '*'*20,'update__dict','*'*20
    CHANNEL_DICT = get_channel_agent_name()
    CHANNEL_KEY_DICT,EQUIPMENT_NAME_DICT,EQUIPMENT_ITEM_NAME_DICT,GOLD_ITEM_DICT = get_dict()

class BaseQuery(object):
    '''
    @auto_padding_channel 自动填充渠道号和平台帐号
    @is_center 是否中心查询，分服查询
    @sql_format  sql语句
    @file_format  保存的文件格式
    @monthly  是否每月一号生成一次
    @create_tmp_player_table 是否先创建临时表
    '''
    name = ''
    auto_padding_channel = True
    is_center = False 
    is_query_server = False
    first = True
    monthly = False
    daily = True
    sql = ''''''
    create_table = True
    file_format = '{{edate}}___orders___{{plan_name}}.txt'# plan_name 计划名 首次(first) 每月(monthly) 每天(daily) 关服(closed)
    save_dir = os.path.join(SAVE_DIR,'{{edate}}')
    
    @staticmethod
    def replace_sid(sql,sid):
        return sql.replace('{{server_id}}',str(sid))
    
    @classmethod
    def create_tmp_table(cls,conn,s_obj,backup=None):
        if cls.create_table:
            sid = str(s_obj.id)
            cur = conn.cursor()
            sql = cls.replace_sid('''select DATEDIFF(NOW(),CREATE_TIME)>0 from INFORMATION_SCHEMA.TABLES where TABLE_NAME='player_{{server_id}}_tmp' AND TABLE_SCHEMA='gl{{server_id}}';''',sid)
            cur.execute(sql)
            result = cur.fetchone()
            is_create_table = False
            if result:#存在临时表
                if result[0]:#过时, 删除临时表
                    sql = cls.replace_sid('''drop table if exists player_{{server_id}}_tmp;''',sid)
                    print sql
                    cur.execute(sql)
                    is_create_table = True
            else:
                is_create_table = True
            
            if is_create_table:#创建表
                print '-' * 40
                print 'create tmp table palyer_%s_tmp' % sid
                try:
                    sql = cls.replace_sid('''create table player_{{server_id}}_tmp select * from player_{{server_id}} group by player_id;create index player_{{server_id}}_tmp_index on player_{{server_id}}_tmp(player_id);''',sid)
                    cur.execute(sql)
                    print cur.fetchall()
                except Exception,e:
                    pass

    @classmethod
    def add_agent_name_handler(cls,line):
        
        channel_id = line[1]
        if channel_id:
            _line = list(line)
            agent_name,channel_name = CHANNEL_DICT.get(int(channel_id),['',''])
            line = [agent_name,channel_name or '%s%s' % (PREFIX,channel_id)] + _line[2:]
            del _line
        return line
    
    @classmethod
    def line_handler(cls,line):
        '''行处理
        '''
        if cls.auto_padding_channel:
            line = cls.add_agent_name_handler(line)
            #print 'auto_padding_channel'
        return '\t'.join(( str(c).replace('\t','').replace('\n','') for c in line))
  
class CenterOrdersQuery(BaseQuery):
    name = '游戏中央服的充值明细'
    auto_padding_channel = False
    is_center = True 
    monthly = True
    daily = False
    create_table = False
    #平台名, 服名, 渠道名, 玩家账号, 玩家角色名, 角色ID, 订单号, 渠道订单号, 充值金额, 充值币种, 折合人民币, 游戏币, 充值时间,系统
    sql = '''SELECT IF(c.`agent_name` IS NULL,'youai',c.`agent_name`),
                    IF(s.`name` IS NULL,'',s.`name`),
                    CONCAT(IF(pc.`func_name` IS NULL,'youai',pc.`func_name`),'_',IF(c.`name` IS NULL,'',c.`name`)),
                    IF(pl.`link_key` IS NULL,p.`open_id`,pl.`link_key`),
                    IF(pl.`player_name` IS NULL,'',pl.`player_name`),
                    p.pay_user,
                    IF(p.`query_id` IS NULL, '', p.`query_id`), 
                    IF(p.`order_id` IS NULL, '', p.`order_id`),
                    concat(truncate(IF(pc.amount>0,pc.amount,p.pay_amount),2)) AS `R`,
                    IF(pc.currency IS NULL,'',pc.currency),
                    IF(p.`pay_amount` IS NULL,0.00, concat(truncate(p.`pay_amount`,2))) AS `CONVERT`,
                    IF(p.`pay_gold` IS NULL, 0, p.`pay_gold`) AS `pay_gold`, 
                    IF(p.`last_time` IS NULL, 0 ,UNIX_TIMESTAMP(p.`last_time`)) AS `last_time`,
                    IF(LOCATE('10',c.key)=1,'IOS','Android') 
                    FROM pay_action p
                    LEFT JOIN channel c ON p.channel_id=c.id
                    LEFT JOIN servers s ON s.id=p.server_id
                    LEFT JOIN pay_channel pc ON p.pay_type = pc.id
                    LEFT JOIN player_all pl ON p.pay_user=pl.player_id
                    WHERE p.`pay_status`=4 AND p.`pay_amount`>0 AND p.`post_time`>='{{sdate}}' AND  p.`post_time`<'{{edate}}' AND p.pay_user>0;
                '''
    file_format = '{{edate}}___orders___{{plan_name}}.txt'

  
  
class SingleOrdersQuery(BaseQuery):
    name = '单服充值记录'
    auto_padding_channel = False
    is_center = True
    is_query_server = True
    monthly = False
    daily = True
    create_table = False
    #平台名,充值平台,充值通道,下载渠道,玩家账号,玩家角色名,角色ID,订单号,渠道订单号,充值金额,充值币种,游戏币,充值time,是否首充
    sql = '''SELECT IF(c.`agent_name` IS NULL,'youai',c.`agent_name`),
        IFNULL(pc.`func_name`,'youai'),
        IFNULL(pc.`name`,''),
        IFNULL(c.`name`,''),
        IF(pl.`link_key` IS NULL,p.`open_id`,pl.`link_key`),
        IF(pl.`player_name` IS NULL,'',pl.`player_name`),
        p.pay_user,
        IF(p.`query_id` IS NULL, '', p.`query_id`), 
        IF(p.`order_id` IS NULL, '', p.`order_id`),
        concat(truncate(IF(pc.`amount`>0,pc.`amount`,p.`pay_amount`),2)) AS `R`,
        IF(pc.currency IS NULL,'',pc.currency),
        IF(p.`pay_gold` IS NULL, 0, p.`pay_gold`) AS `pay_gold`, 
        IF(p.`last_time`,UNIX_TIMESTAMP(p.`last_time`),0) AS `last_time`,
        IF((SELECT pay_user FROM pay_action WHERE p.id>id AND pay_user=p.`pay_user` AND `server_id`=p.`server_id` AND `pay_status`=4 AND `pay_amount`>0 LIMIT 1),0,1),
        IF(LOCATE('10',c.key)=1,'IOS','Android') 
        FROM pay_action p
        LEFT JOIN channel c ON p.channel_id=c.id
        LEFT JOIN pay_channel pc ON p.pay_type = pc.id
        LEFT JOIN player_all pl ON p.pay_user=pl.player_id
        WHERE p.`pay_status`=4 AND p.`pay_amount`>0 AND p.`post_time`>='{{sdate}}' AND p.`post_time`<'{{edate}}'  AND p.`server_id`={{server_id}}  AND p.pay_user>0;
        '''
    file_format = 'mixed___{{prefix}}{{server_id}}___{{edate}}___orders___{{plan_name}}.txt'
    
class  SingleServerGold(BaseQuery):
    name = '单服游戏币流水'
    auto_padding_channel = True
    is_center = False 
    is_query_server = True
    monthly = False
    daily = True
    #平台名,渠道名,玩家账号,玩家角色名,角色ID,操作类型,操作项目,发生游戏币,剩余游戏币,发生time
    sql = '''SELECT if(p.user_type is NULL,'',p.user_type),
            if(p.channel_id is NULL,'',p.channel_id),
            if(p.link_key is NULL,'',p.link_key),
            if(p.player_name IS NULL ,'',p.player_name)  as player_name,
            g.log_user,
            if((ROUND(log_now-log_previous)+IFNULL(f2-f1,0))>0,1,0),
            g.log_type,
            ABS( CONVERT((log_now-log_previous)+IFNULL(f2-f1,0),SIGNED)  ),
            CONVERT(ROUND(log_now)+ROUND(f2),SIGNED),
            IF(g.log_time ,UNIX_TIMESTAMP(g.log_time),0)
            FROM gl{{master_id}}.`log_gold` g
            LEFT JOIN 
            gl{{server_id}}.`player_{{server_id}}_tmp` p ON p.player_id=g.log_user
            WHERE g.log_time >= '{{sdate}}' AND  g.log_time<'{{edate}}' AND p.player_name!='';
          '''
    file_format = 'mixed___{{prefix}}{{server_id}}___{{edate}}___coinslog___{{plan_name}}.txt'

    @classmethod
    def line_handler(cls,line):
        '''单据流水处理,替换道具项目列表，和道具名称
        '''
        line = list(line)
        line[6] = GOLD_ITEM_DICT.get(unicode(line[6]),GOLD_ITEM_DICT.get(line[6],line[6]))
        return super(SingleServerGold,cls).line_handler(line)

class SingleServerMembers(BaseQuery):
    name = '单服玩家爱列表'
    auto_padding_channel = True
    is_center = False 
    is_query_server = True
    monthly = False
    daily = True
    
    #平台名,渠道名,玩家账号,玩家角色名,角色ID,注册时间,当天在线时长,最后登录时间,最后登录IP,登录MAC地址,玩家等级,剩余游戏币,系统
    sql = '''SELECT p.user_type,
            p.channel_id,
            p.link_key,
            p.player_name,
            '' AS sex,
            '' AS job,
            p.player_id,
            UNIX_TIMESTAMP(p.create_time),
            if(o.log_result  IS NULL,0,o.log_result),
            if(cc.log_time IS NULL,0,UNIX_TIMESTAMP(cc.log_time)),
            if(cc.f1 IS NULL,'',cc.f1),
            if(cc.f2 IS NULL,'',substring_index(substring_index(cc.f2,'|',5),'|',-1)) as mac,
            IFNULL(ll.log_level,0) as level,
            if(g.last_gold IS NULL,0,g.last_gold),
            'Android'
            FROM gl{{server_id}}.player_{{server_id}}_tmp p 
            LEFT JOIN 
            (SELECT log_user,SUM(CONVERT(log_now-log_previous,SIGNED)) AS log_result FROM gl{{master_id}}.log_online 
                WHERE log_time>='{{sdate}}' AND  log_time<'{{edate}}' GROUP BY log_user
            ) o ON o.log_user=p.player_id 
            LEFT JOIN (
                SELECT ac.log_user,ac.f1,ac.f2,ac.log_time FROM gl{{server_id}}.log_check_user AS ac INNER  JOIN 
                    (SELECT log_user,MAX(id) AS mid FROM gl{{server_id}}.log_check_user  WHERE log_time>='{{sdate}}' AND log_time<'{{edate}}' GROUP BY log_user) AS bc
                    on ac.log_user=bc.log_user and ac.id=bc.mid
                    GROUP BY log_user
            ) cc ON cc.log_user=p.player_id
            LEFT JOIN gl{{master_id}}.log_player AS ll  ON ll.log_user=p.player_id  
            LEFT JOIN gl{{server_id}}.log_last_gold_{{server_id}}_tmp  g ON g.log_user=p.player_id 
            WHERE  p.player_name!='' AND p.create_time<='{{edate}}';
          '''
    file_format = 'mixed___{{prefix}}{{server_id}}___{{edate}}___members___{{plan_name}}.txt'

    @classmethod
    def line_handler(cls,line):
        '''单服玩家爱列表,根据渠道key判断系统 开头01为IOS 00为Android
        '''
        line = list(line)
        try:
            channel_id = line[1]
            if channel_id:
                channel_key = CHANNEL_KEY_DICT.get(int(channel_id),'00')[:2]
                the_system = 'IOS' if channel_key == '10' else 'Android'
                line[14] = the_system
        except:
            pass
        return super(SingleServerMembers,cls).line_handler(line)

    @classmethod
    def create_tmp_table(cls,conn,s_obj,backup=None):
        '''创建金币临时表
        '''
        super(SingleServerMembers,cls).create_tmp_table(conn,s_obj,backup)
        sid = str(s_obj.id)
        cur = conn.cursor()
        sql = '''drop table if exists log_last_gold_%s_tmp;'''%sid
        print '-' * 40
        print sql
        try:
            cur.execute(sql)
        except:
            pass
        create_tmp_last_gold_sql = '''
            CREATE TABLE log_last_gold_{{server_id}}_tmp 
            SELECT g.log_user,
            g.log_now AS last_gold,
            g.log_time AS last_time,c.expend,c.pay_gold,c.give_gold 
            FROM gl{{master_id}}.log_gold AS g INNER  JOIN 
            (SELECT log_user,MAX(id) AS mid ,sum(if(ROUND(log_now-log_previous)<0 ,ROUND(log_now-log_previous),0)) expend,sum(if( ROUND(log_now-log_previous)>0 ,ROUND(log_now-log_previous),0)) as pay_gold,sum(if(log_type!=3108,ROUND(log_now-log_previous),0)) give_gold 
              FROM gl{{master_id}}.log_gold   WHERE log_time<'{{edate}}' GROUP BY log_user) AS c
            ON g.log_user=c.log_user AND g.id=c.mid
            GROUP BY log_user;
            CREATE INDEX log_last_gold_{{server_id}}_tmp_index  on log_last_gold_{{server_id}}_tmp (log_user);
        '''.replace('{{server_id}}',sid).replace('{{master_id}}',str(s_obj.get_master_id())).replace('{{edate}}',backup.file_edate or backup.edate.strftime(backup.DAY_FORMAT))
        
        cur.execute(create_tmp_last_gold_sql)
        
class SingleServerLogin(BaseQuery):
    name = '单服登录日志'
    auto_padding_channel = True
    is_center = False 
    is_query_server = True
    monthly = False
    daily = True
    #平台名 渠道名 玩家账号 玩家角色名 角色ID 登录时间  登出时间  登录IP  登录设备标识码
    sql = '''SELECT l.platform,l.channel,l.user_id,l.player_name,l.player_id,l.login_time,l.logout_time,
            substring_index(l.ip_mac,'|',1) as ip,if(length(substring_index(l.ip_mac,'|',-1))>=12,substring_index(l.ip_mac,'|',-1),'') as mac
            FROM 
            (
            SELECT 
            IF(p.user_type IS NULL, '', p.user_type) AS platform, 
            IF(p.channel_id IS NULL, '', p.channel_id) AS channel, 
            IF(p.link_key IS NULL, '', p.link_key) AS user_id, 
            IF(p.player_name IS NULL, '', p.player_name) AS player_name, 
            IF(p.player_id IS NULL, 0, p.player_id) AS player_id, 
            IF(o.log_previous IS NULL, 0, o.log_previous) AS login_time, 
            IF(o.log_now IS NULL, 0, o.log_now) AS logout_time, 
            IFNULL((SELECT CONCAT(f1,'|',f2) FROM gl{{server_id}}.log_check_user WHERE log_time<o.log_time AND log_user=o.log_user LIMIT 1),CONCAT('','|','')) AS ip_mac 
            FROM gl{{master_id}}.log_online AS o 
            LEFT JOIN gl{{server_id}}.player_{{server_id}}_tmp AS p ON p.player_id=o.log_user
            WHERE o.log_time >= '{{sdate}}' AND o.log_time<'{{edate}}'  AND player_name!=''
            ) l
          '''
    file_format = 'mixed___{{prefix}}{{server_id}}___{{edate}}___loginlog___{{plan_name}}.txt'

   
class SingleServerOnlines(BaseQuery):
    name = '单服在线人数统计'
    auto_padding_channel = False
    is_center = False 
    is_query_server = True
    monthly = False
    daily = True
    #在线人数,采样时间点
    sql = '''SELECT log_now,DATE_FORMAT(log_time,'%Y-%m-%d %H:%i') AS time 
            FROM gl{{master_id}}.log_playing 
            WHERE log_time >= '{{sdate}}' AND log_time< '{{edate}}' ORDER BY log_time
          '''
    file_format = 'mixed___{{prefix}}{{server_id}}___{{edate}}___onlines___{{plan_name}}.txt'
   


class SingleServerItemslog(BaseQuery):
    name = '单服道具流水'
    auto_padding_channel = True
    is_center = False 
    is_query_server = True
    monthly = False
    daily = True
    #平台名,渠道名,玩家账户,玩家角色名,角色ID,操作类型,项目名称,物品名称,发生数量,发生时间
    sql = '''SELECT 
            IF(p.user_type IS NULL, '', p.user_type) AS platform, 
            IF(p.channel_id IS NULL, '', p.channel_id)  AS channel, 
            IF(p.link_key IS NULL, '', p.link_key) AS user_id, 
            IF(p.player_name IS NULL, '', p.player_name) AS player_name, 
            IF(p.player_id IS NULL, '', p.player_id) AS player_id,
            IF(e.log_tag=1,0,1),
            e.log_type AS item_name, 
            CONVERT(e.log_previous/1000,SIGNED) AS goods_name, 
            e.f2, 
            IF(e.log_time IS NULL,0, UNIX_TIMESTAMP(e.log_time)) AS time
            FROM gl{{master_id}}.log_item_track AS e LEFT JOIN gl{{server_id}}.player_{{server_id}}_tmp AS p ON e.log_user = p.player_id
            WHERE log_time>='{{sdate}}' AND log_time<'{{edate}}'  AND player_name!=''
            '''
    file_format = 'mixed___{{prefix}}{{server_id}}___{{edate}}___itemslog___{{plan_name}}.txt'

    
    @classmethod
    def line_handler(cls,line):
        '''单据流水处理,替换道具项目列表，和道具名称
        '''
        line = list(line)
        line[6] = EQUIPMENT_ITEM_NAME_DICT.get(unicode(line[6]),EQUIPMENT_ITEM_NAME_DICT.get(line[6],line[6]))
        line[7] = EQUIPMENT_NAME_DICT.get(unicode(line[7]),EQUIPMENT_NAME_DICT.get(line[7],line[7]))
        return super(SingleServerItemslog,cls).line_handler(line)





SQL = {
       #创建中央服角色表sql
       'create_center_player':'''CREATE TABLE if not exists `player_all` (
                                `server_id` integer NOT NULL,
                                `player_id` integer NOT NULL unique ,
                                `player_name` varchar(50) NOT NULL,
                                `user_type` integer NOT NULL,
                                `link_key` varchar(50) NOT NULL,
                                `create_time` datetime NOT NULL,
                                `last_time` datetime NOT NULL,
                                `last_ip` varchar(32) NOT NULL,
                                `last_key` varchar(50),
                                `login_num` integer NOT NULL,
                                `status` integer NOT NULL,
                                `channel_id` varchar(20) NOT NULL,
                                `mobile_key` varchar(50),
                                `roll_num` integer default 0 NULL,
                                key `user_type_link_key_index`(link_key,user_type)
                                );
                              ''',
                              
       #获取分服的角色表的sql            
       'get_player':         '''SELECT {{server_id}},player_id,player_name,user_type,link_key,create_time,last_time,last_ip,last_key,login_num,status,channel_id,mobile_key
                                FROM player_{{server_id}}_tmp 
                                WHERE last_time BETWEEN '{{sdate}}' AND '{{edate}}';
                             ''',
                             
       #插入或者更新中央角色表sql                 
       'insert_center_player':'''INSERT INTO 
                                 player_all(server_id,player_id,player_name,user_type,link_key,create_time,last_time,last_ip,last_key,login_num,status,channel_id,mobile_key)
                                 VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                                on duplicate key update 
                                create_time=VALUES(create_time),
                                player_name=VALUES(player_name),
                                user_type=VALUES(user_type),
                                link_key=VALUES(link_key),
                                create_time=VALUES(create_time),
                                last_time=VALUES(last_time),
                                last_ip=VALUES(last_ip),
                                last_key=VALUES(last_key),
                                login_num=VALUES(login_num),
                                status=VALUES(status),
                                channel_id=VALUES(channel_id),
                                mobile_key=VALUES(mobile_key)
                            '''
       }


#创建滚服角色表SQL
SQL['create_roll_player'] = SQL['create_center_player'].replace('player_all','player_roll')


#获取滚服sql 
SQL['get_roll_player'] = '''
SELECT p.player_id ,p.link_key,p.user_type,p.create_time
FROM player_{{server_id}}_tmp p
LEFT JOIN 
player_roll p1
ON p.player_id = p1.player_id
WHERE p1.player_id IS NULL
'''

#获取滚服的角色信息
SQL['get_center_roll_player'] = '''
SELECT server_id,player_id,player_name,user_type,link_key,create_time,last_time,last_ip,last_key,login_num,status,channel_id,mobile_key
FROM player_all
WHERE link_key='%s' AND user_type=%d
AND create_time<='%s'
'''

#更新中央角色表滚服数字
SQL['update_center_roll_num'] = '''
update player_all set roll_num=%s
WHERE player_id=%s
'''

#插入分服滚服表
SQL['insert_player_roll'] = '''
INSERT INTO  
player_roll(server_id,player_id,player_name,user_type,link_key,create_time,last_time,last_ip,last_key,login_num,status,channel_id,mobile_key,roll_num)
VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
on duplicate key update 
create_time=VALUES(create_time),
player_name=VALUES(player_name),
user_type=VALUES(user_type),
link_key=VALUES(link_key),
create_time=VALUES(create_time),
last_time=VALUES(last_time),
last_ip=VALUES(last_ip),
last_key=VALUES(last_key),
login_num=VALUES(login_num),
status=VALUES(status),
channel_id=VALUES(channel_id),
mobile_key=VALUES(mobile_key),
roll_num=VALUES(roll_num)
'''

   
Query_Types = [CenterOrdersQuery,
               SingleOrdersQuery,
               SingleServerGold,
               SingleServerMembers,
               SingleServerLogin,
               SingleServerOnlines,
               SingleServerItemslog,
               ] 


