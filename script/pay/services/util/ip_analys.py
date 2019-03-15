# coding=utf-8


import time,json,hashlib,base64,urllib,urllib2
from xml.dom import minidom 
import threading
import functools
import traceback

def async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        my_thread.setDaemon(True)
        my_thread.start()
    return wrapper

def md5(sign_str):
    signStr=hashlib.md5() 
    signStr.update(sign_str.encode('utf-8'))
    return signStr.hexdigest()
        
        

class IpAPI(object):
    ADDRESS = ''
    def __init__(self,ip):
        self.ip = ip
        self.result = {}
        
    def input_handle(self):
        raise
    
    def output_handle(self,resutl):
        raise 
    def get_result(self):
        try:
            url,data = self.input_handle()
            #print url,data
            _r = urllib2.urlopen(url,data,timeout=self.timeout)
            return self.output_handle(_r.read())
        except:
            traceback.print_exc()
            return {}
        
class SinaIpApi(IpAPI):
    ADDRESS = 'http://int.dpool.sina.com.cn/iplookup/iplookup.php'
    timeout = 3
    
    def input_handle(self):
        return '%s?format=json&ip=%s' % (self.ADDRESS,self.ip),None
    
    def output_handle(self,data):
        return json.loads(data)

class TaoBaoIpApi(IpAPI):
    ADDRESS = 'http://ip.taobao.com/service/getIpInfo.php'
    timeout = 3
    
    def input_handle(self):
        return '%s?format=json&ip=%s' % (self.ADDRESS,self.ip),None
    
    def output_handle(self,data):
        return json.loads(data)


class IpAnalysEngine(object):pass


if __name__ == '__main__':
    ips = ['115.156.238.114','58.44.124.24','125.41.219.77','117.136.9.17','106.39.222.116','111.225.98.66','116.114.170.103']
    st = int(time.time())
    for i in xrange(1):
        for ip in ips:
            s = SinaIpApi(ip)
            print json.dumps(s.get_result(),ensure_ascii=False)
    
    print '[%s]' % (int(time.time()) - st)
    