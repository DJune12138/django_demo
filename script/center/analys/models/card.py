#coding=utf-8


from django.db import models
from django.db import connection
from .channel import Channel
from .server import Server
import re,json,random
import traceback
from settings import get_app_label


letter = 'abcdefghjkmnpqrstuvwxyz'
_letter_len = len(letter)
digit = '23456789'
char = '%s%s'%(letter,digit)

def get_next_letter_char(c):
    _c = ''
    c = c.lower()
    index = letter.index(c)
    next_index = index + 1
    if next_index < _letter_len:
        _c = letter[next_index]
        has_carry = False
    else:
        _c = 'a'
        has_carry = True
    return has_carry,_c

def get_next_card_key(the_key):
        assert re.match('[%s]{3}$' % letter,the_key),'礼包卡标示必须符合3个小写字母!'
        a,b,c = the_key
        has_carry,c = get_next_letter_char(c)
        if has_carry:
            has_carry,b = get_next_letter_char(b)
            if has_carry:
                _,a = get_next_letter_char(a)
        return ''.join([a,b,c])


class CardPrize(models.Model):
    '''奖励
    '''
    STATUS_CHOICES = ((0,u'禁用'),(1,u'启用'))
    name = models.CharField(u'名称',max_length=32,db_index=True)
    code = models.CharField(u'随机密钥', max_length = 32, default = '',db_index=True)
    start_time = models.DateTimeField(u'生效时间',blank=True,db_index=True)
    end_time = models.DateTimeField(u'失效时间',blank=True,db_index=True)
    config = models.CharField(u'奖励配置', max_length = 2000)
    remark = models.CharField(u'备注',max_length=255,default='')
    status = models.IntegerField(u'状态',default=0,choices=STATUS_CHOICES)

    class Meta:
        db_table = u'card_prize'
        app_label = get_app_label()

class CardBatch(models.Model):
    '''礼包
    '''
    CONDITION_DEF = {"level":{"name":"等级限制","value":0,"type":"int"},
                     #"create_time":{"name":"注册时间","value":0,"type":"time"}
                     }
    STATUS_CHOICES = ((0,u'禁用'),(1,u'启用'))

    server = models.CharField(u'服务器',max_length=1000)
    channels = models.CharField(u'渠道',max_length=1000)
    key = models.CharField(u'标识',max_length=10) #标识
    name = models.CharField(u'名称',max_length=32)
    level = models.IntegerField(u'主城等级', default = 0)
    remark = models.CharField(u'备注',max_length=255,default='')
    total_count = models.IntegerField(u'总数量',default=0)
    used_count = models.IntegerField(u'已使用数量',default=0)
    limit_count = models.IntegerField(u'每用户限制使用次数',default=1)
    card_limit_count = models.IntegerField(u'每张卡限制使用次数',default=1)
    prize = models.CharField(u'奖励内容',max_length=8192, default='[]')
    start_time = models.DateTimeField(u'生效时间',blank=True)
    end_time = models.DateTimeField(u'失效时间',blank=True)
    code = models.CharField(u'随机密钥', max_length = 32, default = '')
    show = models.IntegerField(u'领卡页面服务器显示', default = 0)
    status = models.IntegerField(u'状态',default=1,choices=STATUS_CHOICES)
    other_condition = models.CharField(u'其他条件',max_length=3000,default=json.dumps(CONDITION_DEF))
    create_user = models.IntegerField(u'创建者',default = 0)

    __other_condition_cache = None

    def get_tol_count_num(self):
        return self.total_count * self.card_limit_count  #张数乘以每张次数

    def get_surplus_rate(self):
        rate_str = ''
        tol_count_num = self.get_tol_count_num()
        if tol_count_num :
            surplus_count = tol_count_num - self.used_count
            rate_str = '%.2f%%' % (float(surplus_count) / tol_count_num *100)
        return  rate_str

    @staticmethod
    def check_card_key(key):
        return re.match('[%s]{3}$' % letter,key)

    def make_card_key(self,previous_key=''):
        '''生成礼包的key
        '''
        previous_key = previous_key.lower()
        if not previous_key:
            self.key = 'aaa'
        else:
            self.key = get_next_card_key(previous_key)

    def get_condition_for_key(self,key_name,default_value=''):
        contdition_dict = self.get_other_condition()
        return contdition_dict.get(key_name,{}).get('value',default_value)

    def get_other_condition(self):
        '''其他条件判断
        '''
        if self.__other_condition_cache == None:
            self.__other_condition_cache = json.loads(self.other_condition)
            if not self.__other_condition_cache:
                self.__other_condition_cache = self.CONDITION_DEF
        return  self.__other_condition_cache

    def __unicode__(self):
        return "id:%d,name:%s" % (self.id,self.name)

    def get_status_name(self):
        return self.STATUS_CHOICES[self.status][1]




    def get_server_ids(self):
        return [ int(s) for s in self.server.split(',') if s and str(s).isdigit()]

    def get_channels_ids(self):
        return [ int(c) for c in self.channels.split(',') if c and str(c).isdigit()]

    def get_server_content(self):
        if self.server != '':
            server_list = [int(i) for i in self.server.split(',')]
            server_content = []
            for item in Server.objects.filter(id__in = server_list):
                server_content.append(item.name)
            return ', '.join(server_content)
        else:
            return '所有服务器'

    def get_channel_content(self):
        if self.channels != '':
            channel_list = [i for i in self.channels.split(',')]
            channel_content = []
            for item in Channel.objects.filter(id__in = channel_list):
                channel_content.append(item.name)
            return ', '.join(channel_content)
        else:
            return '所有渠道'

    class Meta:
        db_table = u'card_batch'
        app_label = get_app_label()


class Card(models.Model):
    STATUS_CHOICES = ((-1,u'已删除'),(0,u'未使用'),(1,u'已领取'),(2,u'已使用'))
    batch = models.ForeignKey(CardBatch)
    number = models.CharField(u'新手卡号',max_length=32,unique=True,db_index=True) #format：1001 + 5数字 ＋　5字母 + 1校验位
    password = models.CharField(u'领取标识',max_length=32,blank=True,null=True)
    add_time = models.DateTimeField(u'添加时间',blank=True,auto_now_add=True)
    use_time = models.DateTimeField(u'使用时间',blank=True,null=True)
    server_id = models.IntegerField(u'服务器标识',default=0,db_index=True,null=True)
    player_id = models.IntegerField(u'用户标识',default=0,db_index=True,null=True)
    channel_key = models.CharField(u'渠道key',max_length=20,null=True)
    status = models.IntegerField(u'状态',default=0,choices=STATUS_CHOICES,null=True)
    use_count = models.IntegerField(u'使用次数',default=0,null=True)


    def get_use_count(self):
        return self.use_count or 0

    @classmethod
    def get_card_number(cls,key):
        pre_number = '%s%s'%(key,''.join(random.sample(letter,6)))
        number = '%s%s'%(pre_number,Card.get_verifCode(pre_number))
        return number

    @classmethod
    def get_verifCode(cls,card_part):
        sum_value = 0
        for i in range(card_part.__len__()):
            if (i+1) % 2 == 0:
                    sum_value += ord(card_part[i]) * 2 % 23
            else:
                    sum_value += ord(card_part[i]) % 23
        result_char = letter[sum_value % 23]
        return result_char

    @classmethod
    def check_card(cls,card_no):
        if cls.get_verifCode(card_no[:-1]) == card_no[-1]:
            return True
        else:
            return False


    @staticmethod
    def get_card_table_name(key):
        return 'cards_%s' % key

    def __unicode__(self):
        return 'status:%s'%(self.status)

    def get_status_name(self):
        return self.STATUS_CHOICES[self.status+1][1]

    def safe_save(self):
        self.lock()
        try:
            self.save()
        except Exception,e:
            print('save error',e)
        self.unlock()

    def lock(self):
        cursor = connection.cursor()
        cursor.execute('LOCK TABLES card_card WRITE;')

    def unlock(self):
        cursor = connection.cursor()
        cursor.execute('UNLOCK TABLES;')

    class Meta:
        db_table = u'card_0'  #format: create table card_%s like card_0;
        app_label = get_app_label()

class CardLog(models.Model):

    STATUS_CHOICES = ((0,u'待发奖励'),(1,u'已发奖励'),(2,u'发送中'),(3,u'发送失败'))

    server_id = models.IntegerField(u'服务器标识',default=0,db_index=True,null=True)
    player_id = models.IntegerField(u'用户标识',default=0,db_index=True,null=True)
    number = models.CharField(u'新手卡号',max_length=32,db_index=True)
    channel_key = models.CharField(u'渠道key',max_length=20,null=True)
    card_key = models.CharField(u'标识',max_length=10) #标识
    card_name = models.CharField(u'卡类名称',max_length=30,default='')
    prize = models.CharField(u'奖励内容',max_length=8192,default='')
    create_time = models.DateTimeField(u'添加时间',blank=True,auto_now_add=True,db_index=True)
    status = models.IntegerField(u'状态',default=0,choices=STATUS_CHOICES)



    def get_status_name(self):
        return self.STATUS_CHOICES[self.status][1]

    def create_time_str(self):
        return self.create_time.strftime("%Y-%m-%d %H:%M:%S")

    def server_name(self):
        try:
            the_server = Server.objects.get(id = self.server_id)
            return the_server.name
        except:
            return ''
    class Meta:
        db_table = u'card_log'  #
        app_label = get_app_label()



class WorkLog(models.Model):
    '''工作日志,保证唯一时使用
    '''

    work_number = models.CharField(u'新手卡号',max_length=50,db_index=True,unique=True)
    add_time = models.DateTimeField(u'添加时间',blank=True,auto_now_add=True)

    class Meta:
        db_table = u'work_log'  #
        app_label = get_app_label()
