import os
import sys

path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(path)

from vscrapy.cmdline import execute

if __name__ == '__main__':
    execute()