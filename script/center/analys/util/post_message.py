#!/usr/bin/env python
#coding:utf-8
#消息发送相关

import os,sys,datetime,time
import traceback
import urllib,urllib2
import hashlib
import urllib
import threading
import Queue
from optparse import OptionParser 
import select

SIGN_KEY = 'oaksodqweack123'

def md5(_str):
    return hashlib.new('md5', _str.decode('utf-8')).hexdigest()
def get_now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

MSG_ADDRESS = 'http://server.fytxonline.com:11111/msg/post/'

def post_msg(to='qq',msg='',html='',auto_time=True,merge=False):
        '''
        @to 发给谁
        @msg 消息
        @html 页面
        @auto_time 自动增加时间
        @merge msg 增加到 html
        '''
        _d = {}
        _d['to'] = to
        _d['msg'] = msg.decode('utf-8').encode('utf-8')
        _d['html'] = html.decode('utf-8').encode('utf-8')
        if auto_time:
            _d['msg'] = '[%s]\n%s' % (get_now(),_d['msg'])
        if merge:
            _d['html'] = '%s\n%s' % (_d['msg'],_d['html'])
            
        _d['timestmap'] = int(time.time())
        sign_str = md5('%s%s%s' % (_d['msg'],_d['timestmap'],SIGN_KEY))
        _d['sign'] = sign_str
        try:
            _r = urllib2.urlopen(MSG_ADDRESS,urllib.urlencode(_d),timeout=10).read()
            
        except Exception,e:
            traceback.print_exc()
            _r = str(e)
        return _r 


def main():
    MSG_USAGE = "usage: %prog -t 'title' -m msg -a" 
    parser = OptionParser(MSG_USAGE)              
    parser.add_option("-s", "--subject", dest="subject",
                        help="标题",metavar='')                
    parser.add_option("-m", "--html", dest="html",default='',
                        help="详情",metavar='')   
    parser.add_option("-t", "--to", dest="target",default='qq',
                        help="发送目标",metavar='')                                    
    parser.add_option("-a", "--add", dest="auto_add_time",action="store_true",default=False,
                        help="自动增加时间")
    (o, args) = parser.parse_args()
    
    i,_,_=select.select([sys.stdin],[],[],0.01)
    if o.target and o.subject:
        if i:
            o.html = i[0].read()
        print post_msg(o.target,o.subject,html=o.html,auto_time=o.auto_add_time)
    else:
        parser.print_help()
if __name__ == '__main__':
    main()
        
    
    
    
        