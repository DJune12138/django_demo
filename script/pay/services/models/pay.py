# coding=utf-8
'''
Created on 2011-12-19

'''
from django.db import models
from django.db import connections
import datetime,time,uuid,json
from settings import get_app_label
import traceback 

from models.game import Activity

def get_time_str(time): 
    if time == '' or time == None:
        return ''
    return time.strftime('%Y-%m-%d %H:%M:%S')


class PayAction(models.Model):
    STATUS_CHOICES = ((-4,'游戏返回失败'),(-2,'游戏服连接失败'),(0,'已提交,未支付'),(1,'已转发,未回复'),(2,'已支付,待发'),(3,'发放中'),(4,'充值成功'),(5,'充值异常'))
    query_id = models.CharField(u'查询编号',max_length=40,db_index=True,default='')
    order_id = models.CharField(u'订单编号',max_length=60,db_index=True,blank=True,null=True)
    channel_key = models.CharField(u'客户端渠道KEY',max_length=50)
    channel_id = models.IntegerField(u'渠道ID',default=0,db_index=True)
    server_id = models.IntegerField(u'服务器ID',default=1,db_index=True)
    pay_type = models.IntegerField(u'支付类型',default=0,db_index=True)
    pay_user = models.IntegerField(u'支付账号',max_length=50,db_index=True)
    pay_ip = models.CharField(u'支付IP',max_length=20)
    pay_status = models.IntegerField(u'支付状态',default=0,choices=STATUS_CHOICES,db_index=True) 
    card_no = models.CharField(u'支付账号',max_length=50)
    card_pwd = models.CharField(u'支付账号',max_length=50)
    post_time = models.DateTimeField(u'提交时间',auto_now_add=True)
    last_time = models.DateTimeField(u'支付时间',blank=True,null=True,db_index=True)
    post_amount = models.FloatField(u'提交金额',default=0.00)
    pay_amount = models.FloatField(u'实际支付金额',default=0.00)
    pay_gold = models.IntegerField(u'支付金额兑换的金币数量',default=0)
    extra = models.FloatField(u'赠送金币', default=0.00)
    remark = models.CharField(u'备注',blank=True,null=True,max_length=200)
    open_id = models.CharField(u'关联账号',max_length=100,db_index=True,null=True)
    count = models.IntegerField(u'充值次数',blank=True,default=0)
    player_name = models.CharField(u'角色名',max_length=50)
    player_create_time = models.DateTimeField(u'角色创建时间',null=True,db_index=True)
    charge_id = models.IntegerField(u'充值物品ID',max_length=20)
    charge_type = models.IntegerField(u'充值物品类型',max_length=20)
    payType = models.CharField(u"充值通道",max_length=100,null=True)
    channel_sub_key = models.CharField(u'子渠道KEY',max_length=50)
    vip_level = models.IntegerField(u'vip level',default=0)
    
    def is_sure_pay(self):
        return self.pay_status in (2,-2)
    
    def __unicode__(self):
        return '%d_%s'%(self.pay_user,self.query_id)
    
    def pay_type_name(self):
        return ''

    def total_gold(self):
        return self.pay_gold + self.extra
    
    def pay_status_name(self):
        return u'%s'%self.get_pay_status_display()
        
    def post_time_str(self):
        return get_time_str(self.post_time)

    def post_time_int(self):
        return int(time.mktime(self.post_time.timetuple()))
    
    def last_time_str(self):
        return get_time_str(self.last_time)
    
    def last_time_int(self):
        return int(time.mktime(self.last_time.timetuple()))
    
    def get_query_id(self):
        return datetime.datetime.now().strftime('%y%m%d%H%M%S%f')+str(uuid.uuid4()).split('-')[1].upper()

    def set_query_id(self):
        self.query_id = self.get_query_id()
    
    def safe_save(self,has_order_id=False):
        try:
            PayAction.lock()
            if has_order_id ==False or (has_order_id and PayAction.objects.using('write').filter(pay_type=self.pay_type, order_id=self.order_id).count() == 0):
                self.save(using='write')
        except Exception,e:
            print('save error',e)
        finally:
            PayAction.unlock()
            
    def save(self,*args,**kwargs):
        '''保存订单时增加这个角色的付款次数
        '''
        if not self.count and self.pay_user:
            self.count = PayAction.objects.using('write').filter(pay_user=self.pay_user).count() + 1
        if self.pay_user and self.server_id and not self.player_name and not self.player_create_time:
            from server import ServerPlayer
            try:
                server_player = ServerPlayer(self.pay_user)
                self.player_name = server_player.player_name
                self.open_id = server_player.link_key
                self.player_create_time = server_player.create_time
                del server_player
            except:
                pass
        super(PayAction,self).save(*args,**kwargs)
         
    @staticmethod
    def lock():
        cursor = connections['write'].cursor()
        import datetime
        print datetime.datetime.now() ,'======================'
        cursor.execute('LOCK TABLES pay_action WRITE')
        print datetime.datetime.now(), '======================'
        row = cursor.fetchone()
        #cursor.close()
        return row
    
    @staticmethod
    def unlock():
        cursor = connections['write'].cursor()
        cursor.execute('UNLOCK TABLES;')
        row = cursor.fetchone()
        #cursor.close()
        return row      
     
    class Meta: 
        db_table = u'pay_action'
        ordering = ('-id',)
        app_label = get_app_label()
        


class PayChannel(models.Model):
    STATUS_CHOICES = ((-1,'隐藏'),(0,'正常'),(1,'推荐'),)
    server_id = models.IntegerField(u'专属服务器',default=0,db_index=True)#大于0则表示该支付通道只在某服务器可用
    channel_key = models.CharField(u'渠道限制',max_length=200)
    name = models.CharField(u'通道名称',max_length=100)
    link_id = models.CharField(u'关联第三方标识',max_length=50,db_index=True)
    icon = models.CharField(u'充值通道图标',max_length=20,default='')
    func_name =  models.CharField(u'使用支付函数',max_length=20,default='downjoy')
    pay_type = models.IntegerField(u'支付类型',default=1)
    post_url =  models.CharField(u'通道请求地址',max_length=100)
    notice_url = models.CharField(u'通知我们支付接口成功的地址',max_length=100)
    pay_config = models.CharField(u'支付接口的参数配置',max_length=1000)
    remark =  models.CharField(u'通道描述',max_length=200)
    exchange_rate = models.FloatField(u'兑换汇率',default=0.00)
    status = models.IntegerField(u'通道状态',default=0,choices=STATUS_CHOICES)
    order = models.IntegerField(default=0)
    unit = models.CharField(u'单元',max_length=10,default='元')
    currency = models.CharField(u'币种',max_length=10,default = 'RMB')
    amount = models.FloatField(u'固定金额',default=0.00)
    card_key = models.CharField(u'月卡标示',max_length=200,default='')
    gold = models.IntegerField(u'客户端显示用的',default=0)

    
    def __unicode__(self):
        return '%s_%s'%(self.func_name,self.name)
    
    
    def get_gold(self,pay_amount):
        return self.exchange_rate * float(pay_amount)
    
    
    def is_extra(self):
        extra_list = self.get_config_value('extra', [])
        try:
            if extra_list.__len__() > 0 or  self.get_config_value('extra_rebate',0) > 0:
                _now = time.time()
                sdate = int(self.get_config_value('sdate', 0))
                edate = int(self.get_config_value('edate', 0))
                return (edate > int(_now) > sdate)
            else:
                return False
        except Exception,e:
            return False
    
    @classmethod
    def count_extra_gold(cls,pay_gold,extra_list):
        '''计算返利
        '''
        result = 0
        for extra in extra_list:
                conditions = extra.get('conditions', '')
                if conditions.__len__() >= 2:
                    if pay_gold >= float(conditions[0]) and pay_gold <= float(conditions[1]):
                        amount_rate = float(extra.get('amount', '0'))
                        if amount_rate <= 1:
                            result = amount_rate * pay_gold
        return result                
        
    @classmethod
    def get_activity_rebate(cls,the_action,pay_channel_str):
        '''渠道充值返利活动
        '''
        result = 0
        now = datetime.datetime.now()

        pay_channel_rebate_configs = Activity.objects.filter(type='充值渠道返利',sdate__lte=now,edate__gte=now,server__in=[the_action.server_id],is_auto=1).values_list('msg',flat=True)
        for json_config in pay_channel_rebate_configs:
            try:
                rebate_config = json.loads(json_config)
                extra_list = rebate_config.get(pay_channel_str,[])
                result += cls.count_extra_gold(the_action.pay_gold,extra_list)
            except:
                pass
        return result
    
    def is_month_card(self,the_action):
        return self.card_key and the_action.pay_gold>=self.gold
    
    def get_month_card_gold(self,the_action):
        '''如果是月卡,计算额外需要减去月卡标识的游戏币
        '''
        if self.is_month_card(the_action):
            return int(the_action.pay_gold) - int(self.gold)
        return the_action.pay_gold
    
    # 获取返利额
    def get_extra(self, the_action,pay_channel_str=''):
        extra_gold = 0
        pay_gold = self.get_month_card_gold(the_action)
        server_id = the_action.server_id
        player_id = the_action.pay_user
        
        try:
            
            pay_config_dict = self.get_config_dict()

            first_rebate = pay_config_dict.get('first_rebate',0) #首冲奖励倍数
            if first_rebate and  player_id:
                is_already_pay = PayAction.objects.using('write').filter(pay_user=player_id,pay_type=self.id,server_id=server_id,pay_gold__gt=0).exists()
                if not is_already_pay:
                    extra_gold += int( pay_gold * first_rebate)
                    #首冲就不计算额外的了
                    return extra_gold
                
            if pay_channel_str: #充值渠道活动设置的返利
                try:
                    activity_extra_gold = self.get_activity_rebate(the_action,pay_channel_str)
                    extra_gold += activity_extra_gold
                    #如果有活动覆盖掉固定的 
                    if activity_extra_gold > 0:
                        return extra_gold
                except:
                    traceback.print_exc()
            '''
            #固定返利不需要限制
            extra_rebate = pay_config_dict.get('extra_rebate',0) #额外奖励倍数     
            if extra_rebate:
                extra_gold += int( pay_gold * extra_rebate )
            '''
            #阶段返利开关
            extra_list = pay_config_dict.get('extra', [])
            if not extra_list:
                return extra_gold

            #阶段返利的时间限制
            sdate = int(pay_config_dict.get('sdate', 0))
            edate = int(pay_config_dict.get('edate', 0))

            if sdate and edate:
                _now = time.time()
                if not (edate > int(_now) > sdate): #不在时间范围内
                    print 'not in time!!'
                    return extra_gold

                
            server_list = pay_config_dict.get('server_list', [])
            if type(server_list) == dict:
                try:
                    server_list = [server_list.get(key, '') for key in server_list]
                except Exception, ex:
                    print 'get_extra dict convert list error:', ex

            try:
                server_list = [int(item) for item in server_list]
            except Exception, ex:
                print 'get_extra list convert int value error:', ex

            if server_id > 0 and server_list.__len__() > 0:
                if not server_id in server_list:
                    return extra_gold
            extra_gold += self.count_extra_gold(pay_gold, extra_list)
            
                
        except Exception,e:
            print('extra_gold has error',e)
            traceback.print_exc()
        return extra_gold
    
    __cache_pay_config = None
    
    def get_config_dict(self):
        try:
            if self.__cache_pay_config == None:
                self.__cache_pay_config =  json.loads(self.pay_config)
        except Exception,e:
            print 'get_config_value error:::::::::::::::'
            print 'pay_channel_id is ', self.id
            self.__cache_pay_config = {}
        return self.__cache_pay_config
        
    def set_config_value(self,key,value):
        try:
            self.__cache_pay_config = self.__cache_pay_config or self.get_config_dict()
            self.__cache_pay_config[key] = value
            self.pay_config = json.dumps(self.__cache_pay_config, ensure_ascii=False)
            return True
        except Exception,e:
            return False
        
    def get_config_value(self,key_name,default_value):
        if self.pay_config.__len__() == 0:
            return default_value;
        pay_config = self.get_config_dict()
        return pay_config.get(key_name, default_value)
    
    class Meta: 
        db_table = u'pay_channel'
        ordering = ('order',)
        app_label = get_app_label()
        

