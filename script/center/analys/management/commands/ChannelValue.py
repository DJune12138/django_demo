#coding=utf-8

from django.core.management import BaseCommand
from models.channel import Channel
from models.pay import PayAction
import datetime,time
from django.db import connections
from views.log.statistic_module import get_center_conn



class Command(BaseCommand):
    '''定时增加渠道的价值
    '''

    def handle(self, *args, **options):
        while True:

            now=datetime.datetime.now()
            sd=now.strftime("%Y-%m-%d %H:%M:00")
            st=(now-datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:00")                     ##########每30分钟更新一次
            try:

                con = get_center_conn()  #######连接中央服的数据库
                cur = con.cursor()
                sql="SELECT channel_id,sum(pay_gold),channel_key from pay_action WHERE pay_status =4 AND post_time BETWEEN '%s' and '%s' GROUP BY channel_id"%(st,sd)
                cur.execute(sql)
                res = cur.fetchall()
                for r in res:
                    if r[0]:
                        print 'lllllllllllllllllllll'
                        ch = Channel.objects.filter(id=r[0]).first()
                        ch.allow_earn += int(r[1])
                        ch.save()

                cur.close()
                con.commit()
                con.close()

            except Exception as e:
                print e

            time.sleep(1798)

