# -*- coding: utf-8 -*-

import httplib
import traceback
import socket
import urllib,urllib2

def urldecode(query_str):
    d = {}
    a = query_str.split('&')
    for s in a:
        if s.find('='):
            k,v = map(urllib.unquote, s.split('='))
            try:
                d[k].append(v)
            except KeyError:
                d[k] = [v]
    return d



class HttpTimeOut(Exception):pass

def http_post(url, data=None, data_type = 'x-www-form-urlencoded',user_agent='', timeout_param=5):
    res = None
    urlInfo = httplib.urlsplit(url)
    uri = '%s?%s' % (urlInfo.path,urlInfo.query)
    if url.find('https://')>-1:
        conn = httplib.HTTPSConnection(urlInfo.netloc,timeout=timeout_param)
    else:
        conn = httplib.HTTPConnection(urlInfo.netloc,timeout=timeout_param)
    try:
        conn.connect()
        
        if data:
            if isinstance(data,unicode):
                data = data.encode('utf-8')
            conn.putrequest("POST", uri)
            conn.putheader("Content-Length", len(data))
            conn.putheader("Content-Type", "application/%s"%data_type)
            if user_agent!='':
                conn.putheader("User-Agent",user_agent)
        else:
            conn.putrequest("GET", uri)
            conn.putheader("Content-Length", 0)
            conn.putheader("Content-Type", "application/x-www-form-urlencoded")
            
        conn.putheader("Connection", "close")
        conn.endheaders()

        if data:
            conn.send(data)

        response = conn.getresponse()
        if response:
            res = response.read()
            response.close()
        
        return res
    
    except socket.timeout:
        raise HttpTimeOut('Connect %s time out' % url)
    except Exception, ex:
        raise ex
    
    conn.close()
    
    
if __name__ == '__main__':
    http_post('http://10.20.201.103',timeout_param=2)
