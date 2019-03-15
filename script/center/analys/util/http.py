# -*- coding: utf-8 -*-

import httplib
import traceback
import socket
import urllib
import urllib2
import json
import urlparse
import requests


def urldecode(query_str):
    d = {}
    a = query_str.split('&')
    for s in a:
        if s.find('='):
            k, v = map(urllib.unquote, s.split('='))
            try:
                d[k].append(v)
            except KeyError:
                d[k] = [v]
    return d


class HttpTimeOut(Exception): pass


def http_post(url, data='', data_type='x-www-form-urlencoded', user_agent='', timeout_param=5, timeout=5, headers=[],
              cookie=''):
    res = None
    urlInfo = httplib.urlsplit(url)
    uri = ('%s?%s' % (urlInfo.path, urlInfo.query)) if urlInfo.query else urlInfo.path
    if url.find('https://') > -1:
        conn = httplib.HTTPSConnection(urlInfo.netloc, timeout=timeout or timeout_param)
    else:
        conn = httplib.HTTPConnection(urlInfo.netloc, timeout=timeout or timeout_param)
    try:
        conn.connect()

        if data:
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            conn.putrequest("POST", uri)
        else:
            conn.putrequest("GET", uri)

        for k, v in headers:
            conn.putheader(k, v)

        if cookie:
            if isinstance(cookie, dict):
                cookie = ' '.join(
                    ['%s=%s;' % (urllib2.quote(str(k)), urllib2.quote(str(v))) for k, v in cookie.iteritems()])
            conn.putheader("Cookie", cookie)

        conn.putheader("Content-Length", len(data))
        conn.putheader("Content-Type", "application/%s" % data_type)
        if user_agent != '':
            conn.putheader("User-Agent", user_agent)

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


class SocketTimeOut(Exception): pass


def socket_post(url, data='', timeout_param=5, timeout=5, bufsize=8192):
    # {
    #     "req_type": 5000,
    #     "content": [0],
    #     "player_ids": []
    # }

    conn = res = None
    try:
        urlInfo = httplib.urlsplit(url)
        host, port = urlInfo.netloc.split(':')
        port = int(port)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(timeout or timeout_param)
        conn.connect((host, port))

        # qs = urlparse.parse_qs(data)  # 由于未知原因（有可能是长度限制），导致长度长的时候后面的内容被切割，所以换方法

        qs = {}
        for one in data.split('&'):
            lis = one.split('=')
            qs[lis[0]] = eval(lis[1])

        data = {}
        data['player_ids'] = qs.get('player_id', [])
        # data['req_type'] = int(qs.get('req_type', [0])[0])
        # data['content'] = json.loads(qs.get('content')[0])
        data['req_type'] = qs.get('req_type', [0])
        data['content'] = qs.get('content')

        data = json.dumps(data)
        data = data + '\n'
        print '==> send data: ', repr(data)

        conn.send(data)
        res = ""
        for i in range(50):
            if res and res[-1] == "\n":
                break
            _res = conn.recv(bufsize)
            res += _res
        return res
    except socket.timeout:
        raise SocketTimeOut('Connect %s time out' % url)
    except Exception, ex:
        print ex
        raise ex
    finally:
        conn.close()


def new_http_post(url, data='', timeout_param=5, timeout=5):
    qs = urlparse.parse_qs(data)
    data = {}
    data['player_ids'] = qs.get('player_id', [])
    data['req_type'] = int(qs.get('req_type', [0])[0])
    data['content'] = json.loads(qs.get('content')[0])

    data = json.dumps(data)
    try:
        response = requests.post(url, data, timeout=timeout)
        if response.status_code == 200:
            print response.json()
            return response.json()
        else:
            return response.json()
    except Exception as e:
        print "http post failed,detail is:%s" % e
        return


if __name__ == '__main__':
    # http_post('http://10.20.201.103',timeout_param=2)
    print socket_post('http://10.17.176.180:8009/service', 'req_type=5000&content=["111"]', timeout=1)
