import os

try:
    os.system('start powershell -NoExit redis-cli lpush myspider:start_urls http://www.baidu.com')
except:
    os.system('start cmd /k redis-cli lpush myspider:start_urls http://www.baidu.com')


try:
    os.chdir('../vscrapy')
    os.system('start powershell -NoExit scrapy crawl v')
except:
    os.system('start cmd /k scrapy crawl v')





#redis-cli lpush myspider:start_urls http://www.baidu.com