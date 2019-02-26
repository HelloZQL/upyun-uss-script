#!/usr/bin/env python
# -*- coding: utf8 -*-
# -----------------------
bucket = ''  # 服务名
username = ''  # 操作员名
password = ''  # 操作员密码
path = ''  # 需要列文件列表的起始目录
# -----------------------

from base64 import b64encode
import requests
try:
    import urllib.parse
    # from urllib.parse import quote
    import queue
except ImportError:
    # from urllib import quote
    import Queue as queue
    import urllib
    import sys
    reload(sys)
    sys.setdefaultencoding("utf-8")

queue = queue.LifoQueue()

def record_request(url, status):
    if status:
        with open('file_list.txt', 'a') as f:
            f.write(url + '\n')
    else:
        with open('list_faild_path.txt', 'a') as faied:
            faied.write(url + '\n')


def do_http_request(method, key, upyun_iter):
    uri = '/' + bucket + (lambda x: x[0] == '/' and x or '/' + x)(key)
    try:
        uri = urllib.parse.quote(uri)
    except Exception as e:
        if isinstance(uri, unicode):
            uri = uri.encode('utf8')
        uri = urllib.quote(uri)
    # uri = quote(uri)
    headers = {
        'Authorization': 'Basic ' + b64encode((username + ':' + password).encode()).decode(),
        'User-Agent': "upyun-python-script",
        'X-List-Limit': '300'}

    if upyun_iter is not None or upyun_iter is not 'g2gCZAAEbmV4dGQAA2VvZg':
        headers['x-list-iter'] = upyun_iter  # 'x-list-iter' Change 'x-upyun-list-iter'

    url = 'http://v0.api.upyun.com' + uri
    requests.adapters.DEFAULT_RETRIES = 5
    session = requests.session()
    try:
        response = session.request(method, url, headers=headers, timeout=30)
        status = response.status_code
        if status == 200:
            try:
                content = response.content.decode()
            except Exception as e:
                content = response.content
            try:
                iter_header = response.headers['x-upyun-list-iter']
            except Exception as e:
                iter_header = 'g2gCZAAEbmV4dGQAA2VvZg'
            data = {
                'content': content,
                'iter_header': iter_header
            }
            return data
        else:
            record_request(url, False)
            return None
    except Exception as e:
        record_request(uri, False)
        return None


def getlist(key, upyun_iter):
    result = do_http_request('GET', key, upyun_iter)
    if not result:
        return None
    content = result['content']
    items = content.split('\n')
    content = [dict(zip(['name', 'type', 'size', 'time'], x.split('\t'))) for x in items] + \
              result['iter_header'].split()

    return content

def print_file_with_iter(path):
    upyun_iter = None
    while True:
        while upyun_iter != 'g2gCZAAEbmV4dGQAA2VvZg':
            res = getlist(path, upyun_iter)
            if res:
                upyun_iter = res[-1]
                for i in res[:-1]:
                    try:
                        if not i['name']:
                            continue
                        new_path = path + i['name'] if path == '/' else path + '/' + i['name']
                        if i['type'] == 'F':
                            queue.put(new_path)
                        elif i['type'] == 'N':
                            print(new_path)
                            record_request(new_path, True)
                    except Exception as e:
                        print(e)
            else:
                if not queue.empty():
                    path = queue.get()
                    upyun_iter = None
                    queue.task_done()
        else:
            if not queue.empty():
                path = queue.get()
                upyun_iter = None
                queue.task_done()
            else:
                break

if __name__ == "__main__":
    print_file_with_iter(path)
    print("Job's Done!")
