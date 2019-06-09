import re
import os
import sys
import json
import inspect
import argparse
import traceback
import importlib
from pprint import pprint, pformat

from vscrapy.vscrapy.scrapy_redis_mod import connection

__version__ = '1.0.8'

description = '''Vscrapy ver:{}. (multi task scrapy_redis.)

Usage
  vscrapy <command> [options] [args]

Command
  run       run a vscrapy worker. (pls set redis config first.)
  crawl     use config setting. use spider_name in scrapy project like "scrapy crawl ..."
  runspider use config setting. use spider_file in local file eg. myspider.py
  stat      use taskid check task work stat.
  config    config default host,port,password,db

Command Help
  vscrapy <command>

General Options
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (means no password)
  -db,--db       ::redis db.       default: 0'''.format(__version__)



def _mk_config_path(folder='.vscrapy',filename='.vscrapy'):
    defaults_conf = {
        'host':'localhost',
        'port':6379,
        'password':None,
        'db':0,
    }
    _conf = defaults_conf.copy()
    try:
        home = os.environ.get('HOME')
        home = home if home else os.environ.get('HOMEDRIVE') + os.environ.get('HOMEPATH')
        path = os.path.join(home, folder)
        conf = os.path.join(path, filename)
        if not os.path.isdir(path): os.makedirs(path)
        if not os.path.exists(conf):
            with open(conf,'w',encoding='utf-8') as f:
                f.write(json.dumps(defaults_conf,indent=4))
        else:
            with open(conf,encoding='utf-8') as f:
                _conf = json.load(f)
        return conf, _conf, defaults_conf
    except:
        traceback.print_exc()
        print('unlocal homepath.')
        sys.exit()

def cmdline_config(args):
    confpath, _conf, _o_conf = _mk_config_path()
    clear = int(args.clear)
    loginfo = '''[options]
  type<param>
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (no password)
  -db,--db       ::redis db.       default: 0
  type<toggle>
  -cl,--clear    ::clear redis settings.
current config [use -cl/--clear clear this settings]:'''
    if args.host     == None and\
       args.port     == None and\
       args.password == None and\
       args.db       == None:
        if clear:
            with open(confpath,'w',encoding='utf-8') as f:
                f.write(json.dumps(_o_conf,indent=4))
            print('config clear')
            print(json.dumps(_o_conf,indent=4))
        else:
            print(loginfo)
            print(json.dumps(_conf,indent=4))
    else:
        _conf['host']    = _conf.get('host')      if args.host == None else args.host
        _conf['port']    = _conf.get('port')      if args.port == None else int(args.port)
        _conf['password']= _conf.get('password')  if args.password == None else args.password
        _conf['db']      = _conf.get('db')        if args.db == None else int(args.db)
        _format_defaults = json.dumps(_conf,indent=4)
        with open(confpath,'w',encoding='utf-8') as f:
            f.write(_format_defaults)
        print(loginfo)
        print(_format_defaults)


def _get_settings_and_conf(args):
    from scrapy.utils.project import get_project_settings
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    settings = get_project_settings()
    confpath, _conf, _o_conf = _mk_config_path()
    _conf['host']    = _conf.get('host')      if args.host == None else args.host
    _conf['port']    = _conf.get('port')      if args.port == None else int(args.port)
    _conf['password']= _conf.get('password')  if args.password == None else args.password
    _conf['db']      = _conf.get('db')        if args.db == None else int(args.db)
    os.chdir(cwd)
    return settings, _conf


def cmdline_run(args):
    from scrapy.crawler import CrawlerProcess
    settings, _conf = _get_settings_and_conf(args)
    settings['REDIS_PARAMS'].update(_conf)
    process = CrawlerProcess(settings)
    process.crawl('v')
    process.start()
    

def cmdline_stat(args):
    settings, _conf = _get_settings_and_conf(args)
    settings['REDIS_PARAMS'].update(_conf)
    server = connection.get_redis(**settings['REDIS_PARAMS'])
    loginfo = '''[options]
  type<param>
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (no password)
  -db,--db       ::redis db.       default: 0
  -li,--limit    ::limit show num. default: 5
  -ta,--taskid   ::use taskid check taskinfo.
  type<toggle>
  -la,--latest   ::check latest
  -ls,--list     ::check latest N. default number setby -li/limit(5)
[eg.]
use -ta/--taskid tid(int) eg.   "vscrapy stat -ta 7" 
use -la/--latest          eg.   "vscrapy stat -la" 
use -ls/--list            eg.1/ "vscrapy stat -ls"
                          eg.2/ "vscrapy stat -ls -li 10" 
[tips.]
You need to choose one of the three ways to use stat cmdline.'''
    taskid = int(args.taskid) if args.taskid else None
    latest = int(args.latest) if args.latest else None
    _list_ = int(args.list)   if args.list else None
    limit  = int(args.limit)  if args.limit else None
    ls = list(filter(None,(taskid,latest,_list_)))
    if len(ls) == 0:
        print(loginfo)
        sys.exit()
    if len(ls) != 1:
        print("[ERROR]:\nYou shouldn't use multiple instructions. \nSub command must use one of -ta/-la/-ls.")
        sys.exit()
    for k,v in zip((taskid,latest,_list_),('taskid','latest','list')):
        if k: break

    def _mk_pprint_taskinfo(server, taskid, settings):
        name = settings['TASK_ID_FORMAT'].format(taskid) % {'spider':'v'}
        enco = settings['REDIS_ENCODING']
        d = {}
        for k,v in server.hgetall(name).items():
            k,v = k.decode(enco), v.decode(enco)
            k = '__'+k if k == 'start_time' else k
            k = '_'+k if k == 'finish_time' else k
            try:
                d[k] = int(v)
            except:
                d[k] = v
        return pformat(d)

    if v == 'taskid': 
        print('\n[Taskid: {}] '.format(k))
        print(_mk_pprint_taskinfo(server, k, settings))
    if v == 'latest':
        k = server.get('vscrapy:taskidx').decode(settings['REDIS_ENCODING'])
        print('\n[Taskid: {}] '.format(k))
        print(_mk_pprint_taskinfo(server, k, settings))
    if v == 'list':
        mx = int(server.get('vscrapy:taskidx').decode(settings['REDIS_ENCODING']))
        for i in range(limit):
            print('\n[Taskid: {}] '.format(mx-i))
            print(_mk_pprint_taskinfo(server, mx-i, settings))


def _send_script_start_work(spider_name, script, server):
    taskid = server.incrby('vscrapy:taskidx')
    jsondata = {
        'taskid': taskid,
        'name': spider_name,
        'script': script,
    }
    data = json.dumps(jsondata)
    server.lpush('vscrapy:gqueue:v:start_urls', data)
    return jsondata

def cmdline_crawl(args):
    from scrapy.utils.project import get_project_settings
    from scrapy.spiderloader import SpiderLoader
    settings = get_project_settings()
    spiders  = SpiderLoader.from_settings(settings)
    if not args:
        spiderlist = spiders.list()
        if spiderlist:
            print('spiders list {}'.format(spiderlist))
        sys.exit()
    spidername = args.spider
    filepath = inspect.getabsfile(spiders.load(spidername))
    os.environ.pop('SCRAPY_SETTINGS_MODULE')
    settings, _conf = _get_settings_and_conf(args)
    server = connection.get_redis(**settings['REDIS_PARAMS'])
    with open(filepath,encoding='utf-8') as f:
        script = f.read()
    jsondata = _send_script_start_work(spidername, script, server)
    jsondata.pop('script')
    print('send task:')
    print(json.dumps(jsondata,indent=4))


def cmdline_runspider(args):
    if not args:
        return
    spiderfile = args.spider
    prename = re.findall(r'\[[^\[]+\]', spiderfile)
    if prename:
        spidername = prename[0].strip('[]')
        spiderfile = spiderfile.replace(prename[0],'')
    if not os.path.isfile(spiderfile):
        print('spiderfile is not exists.')
        return
    with open(spiderfile,encoding='utf-8') as f:
        script = f.read()
    settings, _conf = _get_settings_and_conf(args)
    server = connection.get_redis(**settings['REDIS_PARAMS'])
    def load_spider_name_from_module(module_name):
        module = importlib.import_module(module_name)
        spiders = []
        for i in dir(module):
            c = getattr(module, i)
            n = getattr(c, 'name', None)
            s = getattr(c, 'start_requests', None)
            if n and s:
                spiders.append(n)
        return spiders
    env, spiderfile = os.path.split(spiderfile)
    spiderfile = spiderfile.rsplit('.',1)[0]
    sys.path.append(env)
    spiders = load_spider_name_from_module(spiderfile.replace('.py', ''))

    if len(spiders) == 0:
        print('Unfind spider.')
        return
    if len(spiders) == 1:
        spidername = spiders[0]
        jsondata = _send_script_start_work(spidername, script, server)
    if len(spiders) >= 2:
        if not prename:
            print('[error.] \n    There are more than one spider in the spider file, \n'
                  '    so the name of the spider can not be automatically selected.\n'
                  '    So you need to use [] to write the name of the crawler you need to enter.\n'
                  '    current spidername in this script: {}\n'.format(spiders) + 
                  '[eg.] \n    "vscrapy runspider test_script.py[spider_name]" .')
            return
        else:
            if spidername not in spiders:
                print("spider:'{}' is not in spiders:{}".format(spidername, spiders))
            else:
                jsondata = _send_script_start_work(spidername, script, server)
    if 'jsondata' in locals():
        jsondata.pop('script')
        print('send task:')
        print(json.dumps(jsondata,indent=4))

def _parse_crawl(args):
    parse = argparse.ArgumentParser(
        usage           = None,
        epilog          = None,
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description     = description,
        add_help        = False)
    parse.add_argument('spider',           help=argparse.SUPPRESS)
    parse.add_argument('-ho','--host',     default=None,  help=argparse.SUPPRESS)
    parse.add_argument('-po','--port',     default=None,  help=argparse.SUPPRESS)
    parse.add_argument('-pa','--password', default=None,  help=argparse.SUPPRESS)
    parse.add_argument('-db','--db',       default=None,  help=argparse.SUPPRESS)
    loginfo = '''[options]
  type<param>
  spider         ::spider_name
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (no password)
  -db,--db       ::redis db.       default: 0
[eg.]
use spider_name eg. "vscrapy crawl myspider".
send task with scrapy project.
this cmdline will auto find spider_script_file and send.'''
    if len(args) == 2:
        print(loginfo)
        return 
    args = parse.parse_args(args[2:])
    return args

def _parse_runspider(args):
    parse = argparse.ArgumentParser(
        usage           = None,
        epilog          = None,
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description     = description,
        add_help        = False)
    parse.add_argument('spider',           help=argparse.SUPPRESS)
    parse.add_argument('-ho','--host',     default=None,  help=argparse.SUPPRESS)
    parse.add_argument('-po','--port',     default=None,  help=argparse.SUPPRESS)
    parse.add_argument('-pa','--password', default=None,  help=argparse.SUPPRESS)
    parse.add_argument('-db','--db',       default=None,  help=argparse.SUPPRESS)
    loginfo = '''[options]
  type<param>
  spider         ::spider_file
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (no password)
  -db,--db       ::redis db.       default: 0
[eg.]
use spider_file eg. "vscrapy runspider myspider.py".
send task with local file.
this cmdline will auto find spider_name and send.'''
    if len(args) == 2:
        print(loginfo)
        return 
    args = parse.parse_args(args[2:])
    return args


def execute(argv=None):
    if argv is None: argv = sys.argv
    if len(argv)>=2 and argv[1] == 'crawl':
        args = _parse_crawl(argv)
        cmdline_crawl(args)
        return
    if len(argv)>=2 and argv[1] == 'runspider':
        args = _parse_runspider(argv)
        cmdline_runspider(args)
        return

    parse = argparse.ArgumentParser(
        usage           = None,
        epilog          = None,
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description     = description,
        add_help        = False)
    vct = ['stat','run','config','crawl','runspider']
    parse.add_argument('command',          choices=vct,        help=argparse.SUPPRESS)
    parse.add_argument('-ho','--host',     default=None,       help=argparse.SUPPRESS)
    parse.add_argument('-po','--port',     default=None,       help=argparse.SUPPRESS)
    parse.add_argument('-pa','--password', default=None,       help=argparse.SUPPRESS)
    parse.add_argument('-db','--db',       default=None,       help=argparse.SUPPRESS)
    parse.add_argument('-cl','--clear',    action='store_true',help=argparse.SUPPRESS)

    parse.add_argument('-ta','--taskid',   default=None,       help=argparse.SUPPRESS)
    parse.add_argument('-la','--latest',   action='store_true',help=argparse.SUPPRESS)
    parse.add_argument('-ls','--list',     action='store_true',help=argparse.SUPPRESS)
    parse.add_argument('-li','--limit',    default=5,          help=argparse.SUPPRESS)
    
    if len(argv) == 1:
        print(description)
        sys.exit()

    args = parse.parse_args(argv[1:])
    if   args.command == 'run':       cmdline_run(args)
    elif args.command == 'stat':      cmdline_stat(args)
    elif args.command == 'config':    cmdline_config(args)
    elif args.command == 'crawl':     cmdline_crawl(args) # 该处不会被使用到
    elif args.command == 'runspider': cmdline_crawl(args) # 该处不会被使用到

if __name__ == '__main__':
    execute()