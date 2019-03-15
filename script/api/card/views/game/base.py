# -*- coding: utf-8 -*-

from django.conf import settings

from models.log import Log
from models.server import Server
from models.game import Activity
from models.server import KuaFuServer
import datetime

from util.http import http_post
from util.http import socket_post
from util.http import new_http_post

import urllib, urllib2
import json

json.encoder.FLOAT_REPR = lambda x: format(x, '.5f')

import logging
from util import trace_msg, datetime_to_timestamp

import socket


def get_index_range_tuple(start_num, step_num, max_mum):
    '''获取步骤索引元组
    '''
    sp = start_num
    while True:
        if sp >= max_mum: break
        ep = sp + step_num
        if ep > max_mum: ep = max_mum
        yield (sp, ep)
        sp = ep + 1


class GMActionType:
    '''后台自定的伪GM协议类型
    '''
    block_player = 9000001
    unblock_player = 9000002
    activi_ty_on = 9000003
    activity_off = 9000004
    import_player_template = 9000005


class GMProtocolBase(object):
    '''GM协议
    '''

    def __init__(self, gm_address, logger_name='gm', server_id=0):
        self.logger = logging.getLogger(logger_name)
        self.gm_address = gm_address
        self.post_data = ''
        self.response = ''
        self.player_ids = []
        self.rsp_map = {0: "成功!", -1: "失败!", 100: "解析url失败"}
        self.msg = {}
        self.time_out = 30
        self.server_id = server_id

    def add_player_id(self, player_id):
        '''增加玩家ID有些协议不需要
        '''
        self.player_ids.append(player_id)

    def save_log(self, log_user, log_type, result, **kwargs):
        if result == 0 or kwargs.get('force', False):  # 成功才记录
            print self.player_ids
            print "##", (log_user,
                         log_type,
                         self.req_type,
                         self.server.id,
                         self.player_ids[0] if self.player_ids else kwargs.get('player_id', 0),
                         kwargs.get('role_name', ''),
                         result,
                         '%s?%s' % (self.gm_address, self.post_data),
                         self.response,
                         kwargs.get('remark1', ''),
                         kwargs.get('remark2', ''),
                         self.master_server.id
                         )

            write_gm_log(log_user,
                         log_type,
                         self.req_type,
                         self.server.id,
                         self.player_ids[0] if self.player_ids else kwargs.get('player_id', 0),
                         kwargs.get('role_name', ''),
                         result,
                         '%s?%s' % (self.gm_address, self.post_data),
                         self.response,
                         remark1=kwargs.get('remark1', ''),
                         remark2=kwargs.get('remark2', ''),
                         master_id=self.master_server.id
                         )

    def get_result(self):
        # content = json.dumps({"msg": self.msg}, ensure_ascii=False) if self.msg else {}
        content = json.dumps([self.msg], ensure_ascii=False) if self.msg else []
        self.post_data = 'req_type=%d&content=%s' % (self.req_type, content)
        self.post_data += ''.join(['&player_id=%s' % str(p) for p in set(self.player_ids)])
        self.post_data = self.post_data.encode('utf-8')

        self.logger.info('(req(%s),%s?%s)' % (self.master_server.id, self.gm_address, self.post_data))
        try:
            if settings.DEBUG:
                print '==> post address :', self.gm_address
                print '==> post data    :', self.post_data.decode('utf-8')

            # self.response = http_post(self.gm_address, data=self.post_data, timeout_param=self.time_out)
            self.response = socket_post(self.gm_address, data=self.post_data, timeout=self.time_out)
            response = self.response
            print response
            # if not response:
            #     return -2  #未知错误
            _r = json.loads(self.response)

            if settings.DEBUG:
                print '==> post response:', json.dumps(_r, ensure_ascii=False)
                # for better read
                #  print json.dumps(_r, indent=2, ensure_ascii=False)
                print ''
            return _r['msg']

        except Exception, e:
            import traceback
            traceback.print_exc()
            response = str(e)
            if 'nonnumeric port' in response:
                response += '\n游戏服gm端口没配置!'
            if 'Connection refused' in response or not response:
                response += '\n连接不上GM地址,可能端口没开放或未允许后台访问!'
            if 'time out' in response:
                response += '\n连接GM工具(%s秒)超时,排除网络原因,可能是游戏服处理超时!' % self.time_out
            response = '%s\n%s' % (response, self.gm_address)
            # raise Exception(response)
            return response
        finally:
            self.logger.info('(rsp,%s)' % response)

    def query_white_list(self):
        '''查询白名单
        '''
        self.req_type = 1102
        result = self.get_result()
        return result[1] if result[0] == 1 and len(result) >= 2 else []

    def modify_white_list(self, ip_list):
        '''修改白名单
        '''
        self.rsp_map.update({-1: "非法格式!"})
        self.req_type = 1103
        self.msg = [ip_list]
        result = self.get_result()
        return result[0]

    def get_player_base_info(self, player_id):
        '''玩家基本信息
        '''
        # sql='''select player_id,player_name,channel_id,user_type,link_key,login_num,mobile_key,last_time,create_time,status,other
        # from player_%s p WHERE player_id = %s''' % (self.server_id, player_id )
        # conn = Server.get_conn(self.server_id)
        # cur = conn.cursor()
        # cur.execute(sql)
        # result = cur.fetchone()
        # conn.close()
        # return result if result else {}
        self.req_type = 1104
        self.add_player_id(player_id)
        result = self.get_result()
        return result if result else {}

    def get_player_resource(self, player_id):
        '''玩家资源信息
        '''
        self.req_type = 1105
        self.add_player_id(player_id)
        result = self.get_result()
        return result if result else {}

    def get_pilot_info(self, player_id):
        '''获取玩家宠物信息
        '''
        self.req_type = 1106
        self.add_player_id(player_id)
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else {}

    def get_concubine_info(self, player_id):
        '''获取玩家后宫信息
        '''
        self.req_type = 1107
        self.add_player_id(player_id)
        result = self.get_result()
        return result[1:] if result[0] == 0 and len(result) >= 2 else {}

    def get_equip_info(self, player_id, msg):
        '''获取玩家道具等信息
        '''
        self.req_type = 1108
        self.add_player_id(player_id)
        self.msg = msg
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else {}

    def player_base_info(self, player_id, msg):
        '''修改玩家基本信息
        '''
        self.req_type = 1109
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def player_resource_info(self, player_id, msg):
        '''修改玩家资源信息
        '''
        self.req_type = 1110
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def set_pilot_modify(self, player_id, msg):
        '''修改武将
        '''
        self.req_type = 1111
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def modity_concubine(self, player_id, msg):
        '''修改秀女
        '''
        self.req_type = 1112
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def add_server_time(self, add_sec):
        '''增加服务器时间
        '''
        self.req_type = 1114
        add_sec = 86400 * 10 if add_sec > 86400 * 10 else int(add_sec)
        self.msg = [add_sec]
        result = self.get_result()
        return result[0] if result[0] == 0 else [0, 0]

    def query_server_time(self):
        '''查询服务器时间
        '''
        self.req_type = 1115
        result = self.get_result()
        return result[1:] if result[0] == 0 else [0, 0]

    def add_pilot(self, player_id, msg):
        '''增加武将
        '''
        self.req_type = 1116
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def add_equip(self, player_id, msg):
        '''添加道具
        '''
        self.req_type = 1117
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def del_equip(self, player_id, msg):
        '''删除道具
        '''
        self.req_type = 1118
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def add_concubine(self, player_id, msg):
        '''添加秀女
        '''
        self.req_type = 1119
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def del_concubine(self, player_id, msg):
        '''删除秀女
        '''
        self.req_type = 1120
        self.msg = msg
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def player_pay(self, player_id, order_id, pay_gold, extra_gold, charge_type, charge_id, extra=""):
        '''充值"msg": [
        188743681,//充值玩家 "order_1",//订单号 1,//充值金币gold，实际冲的金币 1,//extra_gold额外获赠的金币,0// type(类型)//
        ]
        charge_id
        -1 直冲
        '''
        self.rsp_map.update({1: "玩家player_id有误"})
        self.req_type = 1121
        player_id = int(player_id)
        # is_card = 1 if is_card else 0
        self.msg = [player_id, order_id, pay_gold, extra_gold, charge_type, charge_id, extra]
        result = self.get_result()
        return result[0] if result else -1

    def modify_war_story_process(self, player_id, msg):
        '''修改玩家进度
            通关星级 1 ~ 5
            注意事项:
            一次请求最多50个
        '''
        self.req_type = 1122
        self.add_player_id(player_id)
        self.msg = msg[:50]
        result = self.get_result()
        return result[0]

    def send_card_resouces(self, player_ids, card_name, resources):
        '''发礼包卡资源
        '''
        self.time_out = 7
        self.req_type = 1123
        self.rsp_map.update({1: "玩家(或部分玩家)不存在", 2: "加资源失败"})
        self.msg = [player_ids, card_name, resources]
        result = self.get_result()
        return result[0]

    def roll_broadcast_query(self):
        '''滚动公告信息查询
        '''
        self.req_type = 1124
        result = self.get_result()
        # return result[1] if result[0] == 0 and len(result) >= 2 else []
        return result

    def roll_broadcast_set(self, msg):
        '''滚动公告信息设置
        '''
        self.rsp_map.update({-1: "发送的内容不合法!"})
        self.req_type = 1125
        self.msg = msg
        result = self.get_result()
        return result[0]

    def roll_broadcast_del(self, msg):
        '''滚动公告信息删除
        '''
        self.rsp_map.update({1: "没有该公告!"})
        self.req_type = 1126
        self.msg = msg
        result = self.get_result()
        return result[0]

    def post_question_status(self, player_id):
        '''客服回复后通知
        '''
        self.time_out = 4
        self.req_type = 1127
        self.rsp_map.update({-1: "非法操作"})
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def set_shop_list(self, msg):
        '''设置商城列表
        '''
        self.req_type = 1128
        self.msg = msg
        result = self.get_result()
        return result[0]

    def get_shop_list(self, page_num):
        '''获取商城列表
        '''
        self.req_type = 1129
        self.msg = [page_num - 1]
        result = self.get_result()
        shop_list = result[1] if result[0] == 0 and len(result) >= 2 else {}
        page_sum = result[2]
        return shop_list, page_sum

    def send_mail(self, msg):
        '''发送邮件 [{"ty":类型(0 个人 1 国家 2 全服), "arg":[玩家列表或国家id], "rw":奖励, "m":内容}]
        '''
        self.req_type = 102101
        self.msg = [msg]
        result = self.get_result()
        return result[0]

    def push_online(self):
        '''在线玩家推送
        '''
        self.req_type = 1137
        self.time_out = 1
        result = self.get_result()
        return result[0]

    def player_kick(self, player_id):
        '''踢玩家下线,结果码为0表示踢成功，1表示该玩家不在线
        '''
        self.rsp_map.update({1: "对方不在线"})
        self.req_type = 1101
        self.add_player_id(player_id)
        result = self.get_result()
        return result[0]

    def player_shutup(self, player_id, seconds):
        '''禁言，返回-成功次数
        '''
        #  self.rsp_map.update({1: "禁言截止时间比服务器时间晚", 2: "先解禁才能重新禁言"})
        self.req_type = 1138
        player_id = int(player_id)
        #  self.add_player_id(player_id)
        # 接口支持一次禁用多个玩家，此处未实现
        self.msg = [[player_id, seconds]]
        result = self.get_result()
        return result[0] if result[0] == 0 and len(result) >= 2 else []

    def player_unshutup(self, player_id):
        '''解禁言，返回-成功次数
        '''
        #  self.rsp_map.update({1: "玩家不是禁言状态，不能解禁"})
        self.req_type = 1139
        player_id = int(player_id)
        #  self.add_player_id(player_id)
        self.msg = [player_id]
        result = self.get_result()
        return result[0] if result[0] == 0 and len(result) >= 2 else []

    def player_shutup_list(self, page):
        '''获取禁言列表
        '''
        self.req_type = 1140
        page = int(page)
        self.msg = [page]
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else []

    def get_concubine_book(self, player_id):
        '''获取秀女图鉴
        '''
        self.req_type = 1141
        self.add_player_id(player_id)
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else []

    def change_concubine_book(self, player_id, msg):
        '''修改玩家秀女图鉴
        '''
        self.req_type = 1142
        self.add_player_id(player_id)
        self.msg = [msg]
        result = self.get_result()
        return result[0]

    def get_activity_ids(self):
        '''查询7天乐活动情况
        '''
        self.req_type = 1143
        self.msg = []
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else []

    def get_mail(self, player_id, page_num):
        '''查看邮件列表
        '''
        self.req_type = 1144
        self.msg = [player_id, page_num]
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else []

    def del_mail(self, player_id, mail_id, svr=0):
        '''删除邮件
        '''
        self.req_type = 1145
        if player_id == -1:
            # 公共邮件删除，需指明svr
            self.msg = [player_id, mail_id, svr]
        else:
            self.msg = [player_id, mail_id]
        result = self.get_result()
        return result[0]

    def modify_expedition_progress(self, player_id, msg):
        '''修改远征进度
        '''
        self.req_type = 1148
        self.add_player_id(player_id)
        self.msg = msg
        result = self.get_result()
        return result[0]

    def get_temp_activity(self):
        '''获取开服服务器模版活动
        '''
        self.req_type = 1159
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else []

    def get_flash_sale_pilot(self):
        '''限时抢购武将
        '''
        self.req_type = 1160
        result = self.get_result()
        return result[1:] if result[0] == 0 and len(result) >= 2 else []

    def modify_flash_sale_pilot(self, msg):
        '''设置限时抢购武将
        '''
        self.req_type = 1161
        self.msg = msg
        result = self.get_result()
        return result[0]

    def update_notice(self):
        '''
        更新公告-最新消息的动态
        '''
        self.req_type = 1162
        result = self.get_result()
        return result[0]

    def block_player(self, player_ids):
        # 封角色
        self.req_type = 1163
        self.msg = player_ids
        result = self.get_result()
        return result[0]

    def unblock_player(self, player_ids):
        # 解封角色
        self.req_type = 1164
        self.msg = player_ids
        result = self.get_result()
        return result[0]

    def server_offline(self):
        # 全服下线
        self.req_type = 1165
        result = self.get_result()
        return result[0]

    def player_shutup_silent(self, player_id, seconds):
        # 静默禁言
        #  self.rsp_map.update({1: "禁言截止时间比服务器时间晚", 2: "先解禁才能重新禁言"})
        self.req_type = 1166
        player_id = int(player_id)
        #  self.add_player_id(player_id)
        # 接口支持一次禁用多个玩家，此处未实现
        self.msg = [[player_id, seconds]]
        result = self.get_result()
        return result[0] if result[0] == 0 and len(result) >= 2 else []

    def server_charge_reset(self):
        self.req_type = 1167
        result = self.get_result()
        return result[0] if result[0] == 0 else []

    # def send_rebate_user(self,userlist):
    #     self.req_type = 1168
    #     self.msg = userlist
    #     result = self.get_result()
    #     return result[0] if result[0] == 0 and len(result) >= 2 else []

    def send_battle_server(self, master_server, server_list, Type=[]):
        self.req_type = 1170
        self.msg = [master_server, server_list, Type]
        result = self.get_result()
        return result[0]

    def get_battle_score(self, Type):
        self.req_type = 1171
        self.msg = [Type]
        result = self.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else []

    def modify_gang(self, msg):
        # 修改部族信息
        self.req_type = 1172
        self.msg = msg
        result = self.get_result()
        return result[0]

    def break_gang(self, msg):
        # 解散部族
        self.req_type = 1173
        self.msg = msg
        result = self.get_result()
        return result[0]

    def kick_gang_member(self, msg):
        # 踢部族成员
        self.req_type = 1174
        self.msg = msg
        result = self.get_result()
        return result[0]

    def send_battle_reward(self):
        # 发送跨服奖励
        self.req_type = 1175
        result = self.get_result()
        return result[0]

    def auto_merge_server(self, sub_ids=[]):
        # 自动合服往母服务器发
        self.req_type = 1176
        self.msg = sub_ids
        self.time_out = 180
        result = self.get_result()
        return result[0]

    def back_merge_server(self, sub_ids=[]):
        # 合服合错了回滚
        self.req_type = 1177
        self.msg = sub_ids
        self.time_out = 180
        result = self.get_result()
        return result[0]

    def deduction_jade(self, msg):
        # 扣充值灵玉或绑玉
        self.req_type = 1178
        self.msg = msg
        result = self.get_result()
        return result[0]

    def add_buffID(self, msg):
        # 增加玩家头上的buffID标识
        self.req_type = 1179
        self.msg = msg
        result = self.get_result()
        return result[0]

    def remove_buffID(self, msg):
        # 移出玩家头上的buffID标识
        self.req_type = 1180
        self.msg = msg
        result = self.get_result()
        return result[0]

    def stop_server(self, msg=None):
        # 停服协议
        self.req_type = 1181
        result = self.get_result()
        return result[0]

    def add_battle_server_time(self, add_sec):
        '''增加跨服服务器时间
        '''
        self.req_type = 21052
        add_sec = 86400 * 10 if add_sec > 86400 * 10 else int(add_sec)
        self.msg = [add_sec]
        result = self.get_result()
        return result[0] if result[0] == 0 else [0, 0]

    def query_battle_server_time(self):
        '''查询跨服服务器时间
        '''
        self.req_type = 21051
        result = self.get_result()
        return result[1:] if result[0] == 0 else [0, 0]

    def tell_all_json(self):
        """告诉服务端文件名为json"""

        self.req_type = 101101
        result = self.get_result()
        return result

    def tell_url_json(self):
        """告诉服务端渠道变更"""

        self.req_type = 101102
        result = self.get_result()
        return result

    ################################################################################

    def __get_equip_info(self, sp, ep):
        self.msg = [sp, ep]
        result = self.get_result()
        eqip_infos = result[1] if result[0] == 0 and len(result) >= 2 else {}
        tn = eqip_infos.get('tn', 0)
        eqip_infos_list = eqip_infos.get('d', [])
        print len(eqip_infos_list)
        return tn, eqip_infos_list


class GMProtocol(GMProtocolBase):
    '''GM协议
    '''

    def __init__(self, server_id, logger_name='gm', server_model=None):
        self.server = server_model if server_model != None else Server.objects.get(id=server_id)
        self.master_server = self.server.master_server
        gm_address = self.master_server.gm_address
        super(GMProtocol, self).__init__(gm_address, logger_name, server_id)


class GM_battleProtocol(GMProtocolBase):
    '''GM跨服协议
    '''

    def __init__(self, server_id, logger_name='gm', server_model=None):
        self.server = server_model if server_model != None else KuaFuServer.objects.get(id=server_id)
        self.master_server = self.server.master_server
        gm_address = self.master_server.gm_address
        super(GM_battleProtocol, self).__init__(gm_address, logger_name)


def write_gm_log(log_user, log_type, protocol, server_id, role_id, role_name, log_result, params, return_params,
                 remark1, remark2='', master_id=0):
    '''写GM日志
    @param log_user:操作的管理员ID
    '''
    log = Log()
    log.log_user = log_user  # 操作管理员ID
    log.log_type = log_type  # 操作类型
    log.log_server = server_id  # 服务器ID
    log.log_tag = master_id
    log.log_channel = protocol  # 协议号
    log.log_name = role_name  # 角色名
    try:
        role_id = int(role_id)
        log.log_data = role_id  # 角色ID
    except:
        pass
    finally:
        log.log_relate = role_id

    log.log_result = log_result  # 操作结果
    remark1 = unicode(remark1)
    remark2 = unicode(remark2)
    log.log_previous = remark1[:200]  # 赠送原因

    log.log_now = remark2[:200] or remark1[200:]  # 其他描述

    return_params = unicode(return_params)  # 返回参数

    log.f1 = return_params[0:100]
    log.f2 = return_params[100:200]
    log.f3 = return_params[300:400]
    log.f4 = return_params[500:600]
    log.f5 = return_params[700:800]
    log.f6 = unicode(params)  # 提交参数
    log.log_time = datetime.datetime.now()
    Log._meta.db_table = 'log_gm'
    log.save(using='write')
