# -*- coding: utf-8 -*-
#
#游戏相关字典定义
#
#跨服战参数
BATTLE_PARAM_MAP = {

}

#打折活动(id100以上的)的参数值不能大于0，其他活动(id小于100)的参数值不能小于0
#服务器参数
SERVER_PARAM_MAP = {
                    0:{"name":'经验书增加经验比率(比率)',"input_type":"int","remark":"参数值大于0","min":"0","style":"color:red"},
                    1:{"name":'洗练消耗打折(比率)',"input_type":"int","remark":"负数代表折扣减免","style":"color:red"},
                    2:{"name":'集市购买消耗减免(比率)',"input_type":"int","remark":"负数代表折扣减免","style":"color:red"},
                    3:{"name":'集市购买获得增益(比率)',"input_type":"int","remark":"参数值大于0","min":"0","style":"color:red"},
                    4:{"name":'日常任务宝箱获取增益(比率)',"input_type":"int","remark":"参数值大于0","min":"0","style":"color:red"},
                    5:{"name":'兵团红图纸获取增益(数值)',"input_type":"int","remark":"参数值大于0","min":"0","step":"1","style":"color:red"},
                    6:{"name":'兵团紫图纸获取增益(数值)',"input_type":"int","remark":"参数值大于0","min":"0","step":"1","style":"color:red"},
                    7:{"name":'在线奖励获取增益(比率)',"input_type":"int","remark":"参数值大于0","min":"0","style":"color:red"},
                    8:{"name":'军令购买消耗打折(比率)',"input_type":"int","remark":"负数代表折扣减免","style":"color:red"},
                    9:{"name":'客户端显示用获取军团掉落增益(数值)',"input_type":"int","remark":"参数值大于0","step":"1","min":"0","style":"color:red"}
                    }
#角色信息
PLAYER_INFO_MAP = {
    "pi":{"name":"角色ID"},
    "pn":{"name":"名字"},
    "plv":{"name":"等级"},
    "exp":{"name":"当前等级经验"},
    "sex":{"name":"性别"},
    "nat":{"name":"国家","dict":{-999:"全部",-1:"无",0:"魏",1:"蜀",2:"吴"}},
    "fid":{"name":"头像ID"},
    "pc":{"name":"创建角色时间"},
    "of":{"name":"军衔"},
    "rn":{"name":"改名次数"},
    "os":{"name":"领取俸禄标识"},
    "vip":{"name":"vip等级"},
    "vexp":{"name":"当前登记下vip经验"},
    "pp":{"name":"玩家流程进度ID"},
    "lut":{"name":"最后一次升级的时间"},
    "olt":{"name":"登入时间"},
}

#星盟科技名
ARMY_KEJI_DEF = {
                 1:'星徽等级',
                 2:'星盟等级',
                 3:'征收策略',
                 4:'全盟贡献',
                 5:'矿源精炼',
                 6:'私掠许可',
                 7:'财政筹划'
                }
#星盟军衔
ARMY_TITLE = {0:"会长",
              1:"副会长",
              2:"元老会员",
              3:"高阶会员",
              4:"中阶会员",
              5:"低阶会员",
              6:"普通会员"
              }

#建筑
PLAYER_BUILDING_MAP = {1:"总督府",
                       2:"星舰港",
                       3:"银河系",
                       4:"军事学院",
                       5:"军械所",
                       6:"物资中心",
                       7:"科学院",
                       8:"虚空商贸所",
                       }
KEJI_MAP = {}

#军衔职位ID
OFFICAL = {
    "24": "虎贲郎将",
    "25": "右中郎将",
    "26": "左中郎将",
    "27": "五官郎将",
    "20": "帐下督",
    "21": "门下督",
    "22": "裨将军",
    "23": "偏将军",
    "28": "绥南郎将",
    "29": "立节郎将",
    "1": "散骑",
    "0": "平民",
    "3": "都尉",
    "2": "郡尉",
    "5": "助军左校尉",
    "4": "助军右校尉",
    "7": "左军校尉",
    "6": "右军校尉",
    "9": "中军校尉",
    "8": "下军校尉",
    "11": "典军校尉",
    "10": "上军校尉",
    "13": "胡骑校尉",
    "12": "虎贲校尉",
    "15": "射声校尉",
    "14": "中垒校尉",
    "17": "越骑校尉",
    "16": "步兵校尉",
    "19": "长水校尉",
    "18": "屯骑校尉",
    "30": "立武郎将"
}


#VIP等级
VIP_PRICE = [100,500,1000,2000,5000,10000,20000,50000,100000,150000,300000,500000,1200000,2500000] #VIP等级

#水晶精炼
SJ_MAP = {
    0:"锐抓",
    1:"装甲",
    2:"护盾",
    3:"晶核",
    4:"涂层",
    5:"船饰"
}

#风云2
#角色信息字典
Player_Map ={
    'gj':{-1:"无",0:"魏",1:"蜀",2:"吴"},
    'gz':{}
}

#以下为莽荒天下游戏字典

#职业
Occupation_Map = {
  1:"月羿",
  2:"司命",
  3:"魍魉",
  4:"云君",
  5:"夸父"
}

#头衔
HEAD_TITLE = {
  1:"扬名",
  2:"英杰",
  3:"翘楚",
  4:"人魁",
  5:"天骄",
  6:"定海",
  7:"镇岳",
  8:"凌霄",
  9:"御龙",
  10:"绝圣",
  11:"逐神"
}

#部族
TRIBE_TITLE = {
  # 0:"宗长",

  1:"族长",
  2:"副族长",
  3:"长老",
  4:"部族宝贝",
  5:"部族战神",
  6:"部族护法"


}