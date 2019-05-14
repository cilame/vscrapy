import os
import time
import json
import re

LEVEL = 'DEBUG'

try:
    os.chdir('../vscrapy')
    os.system('start powershell -NoExit scrapy crawl v -L {}'.format(LEVEL))
    # time.sleep(1)
    os.system('start powershell -NoExit scrapy crawl v -L {}'.format(LEVEL))
    # time.sleep(1)
    os.system('start powershell -NoExit scrapy crawl v -L {}'.format(LEVEL))
except:
    os.system('start cmd /k scrapy crawl v -L {}'.format(LEVEL))
    # time.sleep(1)
    os.system('start cmd /k scrapy crawl v -L {}'.format(LEVEL))
    # time.sleep(1)
    os.system('start cmd /k scrapy crawl v -L {}'.format(LEVEL))



# 直接写入内容DEBUG
os.chdir(os.path.dirname(os.getcwd())+r'\vscrapy\vscrapy')

with open('settings.py',encoding='utf-8') as f:
    s = re.findall(r'REDIS_PARAMS *= *\{[^\{\}]+\}', f.read(), re.M)[0]
    host     = re.findall(r"'host' *: *'([^']+)'",s )
    port     = re.findall(r"'port' *: *(\d+)", s)
    password = re.findall(r"'password' *: *'([^']+)'", s)
    db       = re.findall(r"'db' *: *'([^']+)'", s)
    host     = host[0]      if host else 'localhost'
    port     = int(port[0]) if port else 6379
    password = password[0]  if password else None
    db       = db[0]        if db else 0

import redis
# r = redis.StrictRedis(host,port,db,password)
r = redis.StrictRedis()
with open('./spiders/test_script.py',encoding='utf-8') as f:
    script = f.read()

taskid = r.incrby('vscrapy:taskidx')
j = {'nihao':123, 'script':script, 'name': 'test', 'taskid': taskid}
d = json.dumps(j)
r.lpush('vscrapy:gqueue:v:start_urls', d)
# r.lpush('vscrapy:gqueue:v:start_urls', d)