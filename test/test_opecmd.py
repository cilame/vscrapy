import os
import sys

path = os.getcwd()
cmd = 'python3 {}'.format(os.path.join(path, 'test_cmdline.py'))

try:
    os.system('start powershell -NoExit')
except:
    os.system('start cmd /k')

# 将命令写入剪贴板
import win32clipboard as w
import win32api as a
w.OpenClipboard()
w.EmptyClipboard()
w.SetClipboardData(w.CF_TEXT, cmd.encode())
w.CloseClipboard()
# 等待命令行打开后模拟粘贴命令将命令粘贴入控制台
import time; time.sleep(1)
a.keybd_event(0x11,0,0,0)
a.keybd_event(0x56,0,0,0)
a.keybd_event(0x56,0,2,0)
a.keybd_event(0x11,0,2,0)