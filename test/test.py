import os

LEVEL = 'DEBUG'

try:
    os.chdir('../vscrapy')
    os.system('start powershell -NoExit scrapy crawl v -L {}'.format(LEVEL))
except:
    os.system('start cmd /k scrapy crawl v -L {}'.format(LEVEL))

try:
    os.system('start powershell -NoExit')
except:
    os.system('start cmd /k')


# 将命令写入剪贴板
import win32clipboard as w
import win32api as a
w.OpenClipboard()
w.EmptyClipboard()
w.SetClipboardData(w.CF_TEXT, b"redis-cli -h 47.99.126.229 -a vilame lpush v:start_urls http://www.baidu.com")
w.CloseClipboard()
# 等待命令行打开后模拟粘贴命令将命令粘贴入控制台
import time; time.sleep(1)
a.keybd_event(0x11,0,0,0)
a.keybd_event(0x56,0,0,0)
a.keybd_event(0x56,0,2,0)
a.keybd_event(0x11,0,2,0)

