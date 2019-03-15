# -*- coding: utf-8 -*-
#这里是 游戏活动的接口 逻辑


from .base import GMProtocol
from game_def import SERVER_PARAM_MAP
import json


class ActivityAbs(GMProtocol):
    '''活动抽象
    '''
    # 默认参数配置
    DEFAULT_PARAMS = {} 

    # 是否自动开启
    IS_AUTO_ON = True
    # 是否自动关闭
    IS_AUTO_OFF = False
    # 是否保存日志
    IS_SAVE_LOG = True
    # 是否检测冲突
    NOT_CONFLICT_CHECK = False 


    def __init__(self,*args,**kwargs):
        self.activity_model = kwargs.get('activity_model',None)
        if self.activity_model:
            del kwargs['activity_model']
        self.gmp = GMProtocol(*args,**kwargs)
        self.rsp_map = self.gmp.rsp_map


    @classmethod
    def get_default_msg(cls):
        if cls.DEFAULT_PARAMS:
            return json.dumps( cls.DEFAULT_PARAMS, ensure_ascii=False)
        return "{}"

    def save_log(self,*args,**kwargs):
        return self.gmp.save_log(*args,**kwargs)


    def query(self,*args,**kwargs):
        '''查询活动
        '''
        raise

    def on(self,*args,**kwargs):
        '''开启活动
        '''
        raise

    def off(self,*args,**kwargs):
        '''关闭活动
        '''
        raise

class CustomGiftActivity(ActivityAbs):
    '''自定义礼包
    '''

    def __init__(self,*args,**kwargs):
        super(CustomGiftActivity,self).__init__(*args,**kwargs)

    def query(self):
        self.gmp.req_type = 1130
        self.gmp.msg = [0]
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result)>=2  else {}

    def on(self,msg):
        self.gmp.req_type = 1131
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        msg = self.activity_model.msg_obj
        for i in msg:
            i[5] = 0
        return self.on(msg)

from models.pay import PayChannel
class PayChannelRebateActivity(ActivityAbs):
    '''充值渠道返利活动,伪GM活动类,不自动开启关闭,不保存GM日志
    '''

    AUTO_ON = False
    AUTO_OFF = False
    IS_SAVE_LOG = False

    def __init__(self,*args,**kwargs):
        self.gmp = GMProtocol(*args,**kwargs)
        self.rsp_map = rsp_map = {0:"充值渠道返利活动活动不需手动开启和关闭,只需将自动开关打开!"}

    @classmethod
    def get_default_msg(cls):
        default_paychannel_dict = {}
        for c in PayChannel.objects.all().values('id','name','link_id'):
            default_paychannel_dict[c['id']] = {"link_id":c['link_id'],"name":c['name']}
        return json.dumps( default_paychannel_dict, ensure_ascii=False)


    def query(self,*args,**kwargs):
        '''查询活动
        '''
        return self.rsp_map

    def on(self,*args,**kwargs):
        '''开启活动
        '''
        return 0

    def off(self,*args,**kwargs):
        '''关闭活动
        '''
        return 0

class SevenDaysActivity(ActivityAbs):
    '''7天乐活动
    '''
    def __init__(self,*args,**kwargs):
        super(SevenDaysActivity,self).__init__(*args,**kwargs)

    def query(self):
        kid = self.activity_model.msg_obj.get('kid','')
        self.gmp.msg = [kid]
        self.gmp.req_type = 1132
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1133
        self.rsp_map.update({

        })
        self.gmp.msg = [msg]
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        kid = self.activity_model.msg_obj.get('kid','')
        msg = {"kid":kid,"set":0}
        return self.on(msg)


class AccumulatedPayActivity(ActivityAbs):
    '''累计充值活动
    '''
    def __init__(self,*args,**kwargs):
        super(AccumulatedPayActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [type]
        self.gmp.req_type = 1136
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1135
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        ac_type = self.activity_model.msg_obj.get('type')
        msg = {"type": ac_type, "rm": True}
        return self.on(msg)


class AccumulatedConsumeActivity(AccumulatedPayActivity):
    '''累计消费活动
    '''
    def __init__(self,*args,**kwargs):
        super(AccumulatedConsumeActivity,self).__init__(*args,**kwargs)

class DiscountActivity(ActivityAbs):
    '''活动参数打折
    '''

    DEFAULT_PARAMS = SERVER_PARAM_MAP

    def __init__(self,*args,**kwargs):
        super(DiscountActivity,self).__init__(*args,**kwargs)

    def query(self):
        '''查询服务器参数
        '''
        self.gmp.req_type = 1146
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else {}

    def on(self,msg):
        '''配置服务器参数
        '''
        self.gmp.req_type = 1147
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg={}):
        '''关闭参数打折活动
        '''
        msg_obj = self.activity_model.msg_obj
        if msg_obj:
            for i in msg_obj:
                i[2] = 0
                i[3] = 0

        return self.on(msg_obj)



class QQqunActivity(ActivityAbs):
    '''入群领红包
    '''


    def __init__(self,*args,**kwargs):
        super(QQqunActivity,self).__init__(*args,**kwargs)

    def query(self):
        '''查询服务器参数
        '''
        self.gmp.req_type = 1149
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else {}

    def on(self,msg):
        '''配置服务器参数
        '''
        self.gmp.req_type = 1150
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg={}):
        '''关闭
        '''
        msg = [0,0,'',[]]
        return self.on(msg)

class FestivalActivity(ActivityAbs):
    '''节日活动
    '''

    def __init__(self,*args,**kwargs):
        super(FestivalActivity,self).__init__(*args,**kwargs)

    def query(self):
        '''查询服务器参数
        '''
        kid = self.activity_model.msg_obj.get('kid','')
        self.gmp.msg = [kid]
        self.gmp.req_type = 1154
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else {}

    def on(self,msg):
        '''配置服务器参数
        '''
        self.gmp.req_type = 1155
        self.gmp.msg = [msg]
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg={}):
        '''关闭
        '''
        kid = self.activity_model.msg_obj.get('kid','')
        msg = {'kid':kid,'et':0}
        return self.on(msg)


class DailySinglePayActivity(ActivityAbs):
    '''每日单笔充值
    '''
    def __init__(self,*args,**kwargs):
        super(DailySinglePayActivity,self).__init__(*args,**kwargs)

    def query(self):
        '''查询活动参数
        '''
        self.gmp.req_type = 1152
        self.gmp.msg = [self.activity_model.msg_obj[0]]
        result = self.gmp.get_result()
        return result

    def on(self, msg, off=False):
        '''配置活动参数
        '''
        if not off:
            self.force_on(msg[0])
            msg.insert(0, 2)

        self.gmp.req_type = 1153
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[1] if len(result) >= 2 else result[0]

    def off(self,msg={}):
        '''关闭活动
        '''
        # [0, 活动ID]
        msg = [0, msg[0]]
        return self.on(msg, True)

    def exist(self, activity_id):
        '''检查活动是否存在
        '''
        self.gmp.req_type = 1151
        self.gmp.msg = [activity_id]
        result = self.gmp.get_result()
        return True if activity_id == result[0] or activity_id in result[1] else False

    def force_on(self, activity_id):
        '''开启活动
        '''
        exist = self.exist(activity_id)
        if exist:
            self.gmp.req_type = 1153
            self.gmp.msg = [1, activity_id]
            self.gmp.get_result()

class RankingActivity(ActivityAbs):
    '''战力/充值/消费排行榜
    '''

    NOT_CONFLICT_CHECK = True

    def __init__(self,*args,**kwargs):
        super(RankingActivity,self).__init__(*args,**kwargs)

    def query(self):
        '''查询服务器参数
        '''
        ty = self.activity_model.msg_obj.get('key','')
        self.gmp.msg = {'key':ty}
        self.gmp.req_type = 1157
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 else {}

    def on(self,msg):
        '''配置服务器参数
        '''
        self.gmp.req_type = 1158
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg={}):
        '''关闭
        '''
        ty = self.activity_model.msg_obj.get('key','')
        msg = {
            'id':0,
            'key':ty,
            'time':[0,0,0,0],
            'part':[],
            'rank':[],
            'reach':[]
        }
        return self.on(msg)

class RedpackActivity(ActivityAbs):
    '''红包系统活动
    '''


    def __init__(self,*args,**kwargs):
        super(RedpackActivity,self).__init__(*args,**kwargs)

    def query(self):
        '''查询服务器参数
        '''
        self.gmp.req_type = 1163
        msg_obj = self.activity_model.msg_obj
        aid = msg_obj[1]
        self.gmp.msg = [aid]
        self.rsp_map.update({
            284 : "红包ID无效"
        })
        result = self.gmp.get_result()
        return result[1:] if result[0] == 0 and len(result) >= 2 else {}

    def on(self,msg):
        '''配置服务器参数
        '''
        self.gmp.req_type = 1164
        self.gmp.msg = msg
        self.rsp_map.update({
            267 : "无效ID",
            277 : "开始时间必须严格小于结束时间",
            284 : "红包ID无效",
            -100 : "数据难失败"
        })
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg={}):
        '''关闭
        '''
        msg_obj = self.activity_model.msg_obj
        aid = msg_obj[1]
        msg = [1,aid]
        return self.on(msg)


class DailyLimitPayActivity(ActivityAbs):
    '''每日限购活动
    '''
    def __init__(self, *args, **kwargs):
        super(DailyLimitPayActivity, self).__init__(*args,**kwargs)

    def query(self):
        self.gmp.req_type = 1129
        self.gmp.msg = [0]
        result = self.gmp.get_result()

        page = 1
        page_num = result[2]
        _shop_list = []
        while result[0] == 0 and page <= page_num:
            _shop_list.extend(result[1])
            self.gmp.msg = [page]
            result = self.gmp.get_result()
            page += 1

        shop_list = []
        for i in _shop_list:
            if 0 <= i[0] - self.activity_model.id * 10000 < 100:
                shop_list.append(i)
        return shop_list

    def on(self,msg):
        self.gmp.req_type = 1128
        self.gmp.msg = msg
        result = self.gmp.get_result()
        self.rsp_map.update({
            1 : "无效ID",
        })

        err_code = 0 
        for i in result:
            if not i[1]:
                err_code = 1
                break
        return err_code

    def off(self,msg=[]):
        msg = self.activity_model.msg_obj
        for i in msg:
            i[1] = True
        return self.on(msg)


class ReturnActivity(ActivityAbs):
    '''老玩家回归活动
    '''
    # 与原充值活动不冲突
    NOT_CONFLICT_CHECK = True

    def __init__(self, *args, **kwargs):
        super(ReturnActivity, self).__init__(*args,**kwargs)

    def query(self):
        self.gmp.req_type = 1166
        self.gmp.msg = [self.activity_model.msg_obj[0]]
        result = self.gmp.get_result()
        return result


    def on(self, msg, off=False):
        if not off:
            msg.insert(0, 2)

        self.gmp.req_type = 1167
        self.gmp.msg = msg
        self.rsp_map.update({
            1    : "失败",
            -100 : "数据格式异常",
            267  : "天数与元宝大小异常"
        })
        result = self.gmp.get_result()
        return result[0]

    def off(self, msg=[]):
        msg_obj = self.activity_model.msg_obj
        aid = msg_obj[0]
        msg = [1, aid]
        return self.on(msg, off=True)


class OneMorePayActivity(ActivityAbs):
    '''累计/单笔充值活动
    '''

    def __init__(self,*args,**kwargs):
        super(OneMorePayActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class SevenDayHotSellActivity(ActivityAbs):
    '''7天热卖活动
    '''

    def __init__(self,*args,**kwargs):
        super(SevenDayHotSellActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        id = self.activity_model.msg_obj.get('id')
        self.gmp.msg = [7]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class DailyPayMoreActivity(ActivityAbs):
    '''每日累充
    '''

    def __init__(self,*args,**kwargs):
        super(DailyPayMoreActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.msg_obj.get('id')]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class LoginActivity(ActivityAbs):
    '''累计登陆礼包
    '''

    def __init__(self,*args,**kwargs):
        super(LoginActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class TribeRedpacketActivity(ActivityAbs):
    '''部族大红包礼包
    '''

    def __init__(self,*args,**kwargs):
        super(TribeRedpacketActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class MagicWeaponActivity(ActivityAbs):
    '''抽法宝排行
    '''

    def __init__(self,*args,**kwargs):
        super(MagicWeaponActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class FestivalRedpacketActivity(ActivityAbs):
    '''节日红包
    '''

    def __init__(self,*args,**kwargs):
        super(FestivalRedpacketActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class BattleMallActivity(ActivityAbs):
    '''跨服竞拍
    '''

    def __init__(self,*args,**kwargs):
        super(BattleMallActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class WeekLimitBuyActivity(ActivityAbs):
    '''每周限购
    '''

    def __init__(self,*args,**kwargs):
        super(WeekLimitBuyActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class TimeLimitBuyActivity(ActivityAbs):
    '''限时特卖
    '''

    def __init__(self,*args,**kwargs):
        super(TimeLimitBuyActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class TribeListActivity(ActivityAbs):
    '''部族排行
    '''

    def __init__(self,*args,**kwargs):
        super(TribeListActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class LevelListActivity(ActivityAbs):
    '''等级排行
    '''

    def __init__(self,*args,**kwargs):
        super(LevelListActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class PowerActivity(ActivityAbs):
    '''战力排行
    '''

    def __init__(self,*args,**kwargs):
        super(PowerActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class LimitActivity(ActivityAbs):
    '''限时礼包
    '''

    def __init__(self,*args,**kwargs):
        super(LimitActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class TribePrivilegeActivity(ActivityAbs):
    '''部族名门
    '''

    def __init__(self,*args,**kwargs):
        super(TribePrivilegeActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class TribeManagerActivity(ActivityAbs):
    '''部族管理排行
    '''

    def __init__(self,*args,**kwargs):
        super(TribeManagerActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class PetActivity(ActivityAbs):
    '''宠物排行榜
    '''

    def __init__(self,*args,**kwargs):
        super(PetActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class PayScoreActivity(ActivityAbs):
    '''充值积分活动
    '''

    def __init__(self,*args,**kwargs):
        super(PayScoreActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class exchangeActivity(ActivityAbs):
    '''充值积分活动
    '''

    def __init__(self,*args,**kwargs):
        super(exchangeActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class activeActivity(ActivityAbs):
    '''充值积分活动
    '''

    def __init__(self,*args,**kwargs):
        super(activeActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class limitSellActivity(ActivityAbs):
    '''超值特卖
    '''

    def __init__(self,*args,**kwargs):
        super(limitSellActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class legendActivity(ActivityAbs):
    '''轩辕传奇
    '''

    def __init__(self,*args,**kwargs):
        super(legendActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class immortalityActivity(ActivityAbs):
    '''羽化登仙
    '''

    def __init__(self,*args,**kwargs):
        super(immortalityActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class RedPacketActivity(ActivityAbs):
    '''福气红包
    '''

    def __init__(self,*args,**kwargs):
        super(RedPacketActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class EggActivity(ActivityAbs):
    '''福气砸蛋
    '''

    def __init__(self,*args,**kwargs):
        super(EggActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class FireworksActivity(ActivityAbs):
    '''福气烟花
    '''

    def __init__(self,*args,**kwargs):
        super(FireworksActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class DreamlandActivity(ActivityAbs):
    '''幻境副本
    '''

    def __init__(self,*args,**kwargs):
        super(DreamlandActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class MonsterCarnivalActivity(ActivityAbs):
    #怪物嘉年华
    def __init__(self,*args,**kwargs):
        super(MonsterCarnivalActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class BOOSCarnivalActivity(ActivityAbs):
    #boos嘉年华
    def __init__(self,*args,**kwargs):
        super(BOOSCarnivalActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class TopUpRebateActivity(ActivityAbs):
    #充值大返利
    def __init__(self,*args,**kwargs):
        super(TopUpRebateActivity,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)


class Lucky_wheel(ActivityAbs):
    #幸运转盘
    def __init__(self,*args,**kwargs):
        super(Lucky_wheel,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class All_lottery(ActivityAbs):
    #全民抽奖
    def __init__(self,*args,**kwargs):
        super(All_lottery,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class accumulate_charge(ActivityAbs):
    #累计豪礼
    def __init__(self,*args,**kwargs):
        super(accumulate_charge,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class lucky_charge(ActivityAbs):
    #累计充值
    def __init__(self,*args,**kwargs):
        super(lucky_charge,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

class fortune_cat(ActivityAbs):
    #招财猫
    def __init__(self,*args,**kwargs):
        super(fortune_cat,self).__init__(*args,**kwargs)

    def query(self):
        type = self.activity_model.msg_obj.get('type')
        self.gmp.msg = [self.activity_model.id+1000]
        self.gmp.req_type = 1168
        result = self.gmp.get_result()
        return result[1] if result[0] == 0 and len(result) >= 2 and result[1] else {}

    def on(self,msg):
        self.gmp.req_type = 1169
        self.rsp_map.update({
        })
        self.gmp.msg = msg
        result = self.gmp.get_result()
        return result[0]

    def off(self,msg=[]):
        activeId = self.activity_model.msg_obj.get('id')
        msg = {"rm": True,"id":activeId}
        return self.on(msg)

from models.game import Activity
# Activity.register('自定义礼包', CustomGiftActivity)
# Activity.register('充值渠道返利', PayChannelRebateActivity)
# Activity.register('7天乐活动', SevenDaysActivity)
# Activity.register('累计充值', AccumulatedPayActivity)
# Activity.register('累计消费', AccumulatedConsumeActivity)
# Activity.register('参数打折', DiscountActivity)
# Activity.register('入群领红包', QQqunActivity)
# Activity.register('节日活动', FestivalActivity)
# Activity.register('每日单笔充值', DailySinglePayActivity)
# Activity.register('排行榜', RankingActivity)
# Activity.register('红包活动', RedpackActivity)
# Activity.register('每日限购', DailyLimitPayActivity)
# Activity.register('老玩家回归', ReturnActivity)
Activity.register('累积单笔充值', OneMorePayActivity)
Activity.register('七天热卖', SevenDayHotSellActivity)
Activity.register('每日累充', DailyPayMoreActivity)
Activity.register('累积登陆', LoginActivity)
Activity.register('部族大红包', TribeRedpacketActivity)
Activity.register('抽法宝排行', MagicWeaponActivity)
Activity.register('节日红包', FestivalRedpacketActivity)
Activity.register('跨服竞拍', BattleMallActivity)
Activity.register('每周限购', WeekLimitBuyActivity)
Activity.register('部族排行', TribeListActivity)
Activity.register('等级排行', LevelListActivity)
Activity.register('战力排行', PowerActivity)
Activity.register('限时礼包', LimitActivity)
Activity.register('部族名门', TribePrivilegeActivity)
Activity.register('部族管理排行', TribeManagerActivity)
Activity.register('宠物排行榜', PetActivity)
Activity.register('充值积分活动', PayScoreActivity)
Activity.register('兑换活动', exchangeActivity)
Activity.register('活跃活动', activeActivity)
Activity.register('超值特卖', limitSellActivity)
Activity.register('轩辕传奇', legendActivity)
Activity.register('羽化登仙', immortalityActivity)
Activity.register('福气红包', RedPacketActivity)
Activity.register('福气砸蛋', EggActivity)
Activity.register('福气烟花', FireworksActivity)
Activity.register('幻境副本', DreamlandActivity)
Activity.register('怪物嘉年华', MonsterCarnivalActivity)
Activity.register('BOOS嘉年华', BOOSCarnivalActivity)
Activity.register('充值大返利', TopUpRebateActivity)
Activity.register('幸运转盘', Lucky_wheel)
Activity.register('全民抽奖', All_lottery)
Activity.register('累充豪礼', accumulate_charge)
Activity.register('累计充值', lucky_charge)
Activity.register('招财猫', fortune_cat)
