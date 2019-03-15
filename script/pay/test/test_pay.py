#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
#

import thread
import urllib,urllib2
import json
import random
import time
from threadpoll import ThreadPool

test_address = 'http://10.21.210.120:8002/service/confirm/test/'
base_param = 'serverId=%s&openId=%s&orderId=%s&amount=%s&remark=test&orderStatus=1'


test_openids = [(177,2298),
                #(180,176),
                (177,1615),
                (177,12823),
                (177,12845),
                (177,12843),
                (177,12827),
                ]

#test_openids = [(180,3625),
         #       (180,1480),
        #        (180,1615)
      #          ]

def test_pay(i):
    try:
        now = repr(time.time()) + str(i)
        server_id_and_open_id = random.choice(test_openids)
        random_amount = 100
        #random_amount = random.randint(1,500)
        params = base_param % (server_id_and_open_id+(now,random_amount))
        url = '%s?%s' % (test_address,params)
        #print url
        rsp = urllib2.urlopen(url, timeout=17)
        json_str = rsp.read()
        if json_str == 'SUCCESS':
            print '充值成功 %s' % i
        else:
            print json_str,now
    except Exception,e:
        print '充值失败:%s' % (str(e))
    

if __name__=='__main__':
    tp = ThreadPool(20)
    stime = int(time.time())
    for i in xrange(200):
        tp.append(test_pay,(i,))
    tp.close()
    tp.join()
    print 'use sec : %s' % (int(time.time())-stime)
        
        
