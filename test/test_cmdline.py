import os
import sys

path = os.path.dirname(os.getcwd())
os.chdir(path)

from vscrapy.cmdline import execute

if __name__ == '__main__':
    execute()