import os
import time
import json
import re
import redis

with open('./test_script.py',encoding='utf-8') as f:
    script = f.read()

LEVEL = 'DEBUG'

try:
    os.chdir('../vscrapy')
    os.system('start powershell -NoExit vscrapy run')
    # time.sleep(1)
    os.system('start powershell -NoExit vscrapy run')
    # time.sleep(1)
    os.system('start powershell -NoExit vscrapy run')
except:
    os.system('start cmd /k scrapy vscrapy run')
    # time.sleep(1)
    os.system('start cmd /k scrapy vscrapy run')
    # time.sleep(1)
    os.system('start cmd /k scrapy vscrapy run')

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

r = redis.StrictRedis(host,port,db,password)
# r = redis.StrictRedis()

def send_work():
    taskid = r.incrby('vscrapy:taskidx')
    j = {
        'script': script, # 爬虫的scrapy脚本
        'name': 'test',  # 爬虫的名字，用于选中scrapy脚本中的名字
        'taskid': taskid # 任务的id，用于多任务的处理
    }
    d = json.dumps(j)
    r.lpush('vscrapy:gqueue:v:start_urls', d)

send_work()
send_work()