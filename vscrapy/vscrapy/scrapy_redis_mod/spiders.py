from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import Spider, CrawlSpider

from . import connection, defaults
from .utils import bytes_to_str

from twisted.internet import task

import os
import sys
import json
import hmac
import pprint
import importlib
import traceback
from datetime import datetime, timedelta

def mk_work_home(path='.vscrapy_temp'):
    home = os.environ.get('HOME')
    home = home if home else os.environ.get('HOMEDRIVE') + os.environ.get('HOMEPATH')
    path = os.path.join(home, path)
    if not os.path.isdir(path): os.makedirs(path)
    if path not in sys.path: sys.path.append(path)
    return path

# 创建脚本存放环境空间
mk_work_home()


def save_script_as_a_module_file(script):
    try:
        path = mk_work_home()
        filename = '_' + hmac.new(b'',script.encode(),'md5').hexdigest() + '.py'
        filepath = os.path.join(path, filename)
        if not os.path.isfile(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(script)
        return filename.replace('.py', '')
    except:
        traceback.print_exc()

def load_spider_from_module(name, module_name):
    module = importlib.import_module(module_name)
    for i in dir(module):
        c = getattr(module, i)
        n = getattr(c, 'name', None)
        s = getattr(c, 'start_requests', None)
        if s and n == name:
            return c

class RedisMixin(object):
    """Mixin class to implement reading urls from a redis queue."""
    redis_key = None
    redis_batch_size = None
    redis_encoding = None

    # Redis client placeholder.
    server = None

    spider_objs = {}
    spider_tids = {}

    def start_requests(self):
        """Returns a batch of start requests from redis."""
        return self.next_requests()

    def setup_redis(self, crawler=None):
        """Setup redis connection and idle signal.

        This should be called after the spider has set its crawler object.
        """
        if self.server is not None:
            return

        if crawler is None:
            # We allow optional crawler argument to keep backwards
            # compatibility.
            # XXX: Raise a deprecation warning.
            crawler = getattr(self, 'crawler', None)

        if crawler is None:
            raise ValueError("crawler is required")

        settings = crawler.settings

        if self.redis_key is None:
            self.redis_key = settings.get(
                'REDIS_START_URLS_KEY', defaults.START_URLS_KEY,
            )

        self.redis_key = self.redis_key % {'name': self.name}

        if not self.redis_key.strip():
            raise ValueError("redis_key must not be empty")

        if self.redis_batch_size is None:
            # TODO: Deprecate this setting (REDIS_START_URLS_BATCH_SIZE).
            self.redis_batch_size = settings.getint(
                'REDIS_START_URLS_BATCH_SIZE',
                settings.getint('CONCURRENT_REQUESTS'),
            )

        try:
            self.redis_batch_size = int(self.redis_batch_size)
        except (TypeError, ValueError):
            raise ValueError("redis_batch_size must be an integer")

        if self.redis_encoding is None:
            self.redis_encoding = settings.get('REDIS_ENCODING', defaults.REDIS_ENCODING)

        self.logger.info("Reading start URLs from redis key '%(redis_key)s' "
                         "(batch size: %(redis_batch_size)s, encoding: %(redis_encoding)s",
                         self.__dict__)

        self.server = connection.from_settings(crawler.settings)
        # 在后续的处理中，任务不再是在爬虫空闲的时候才进行任务的分配，而是一直都会执行（为了适配多任务）
        # 这样不会让一些任务得不到启动。因此 spider_idle 函数将不在负责执行 schedule_next_requests
        # 而只会抛出 DontCloseSpider 异常，
        # 并且新开一个 schedule_next_requests 函数轮询任务，用于获取启动任务
        # 并且新开一个 _stop_clear 函数轮询任务，用于检测函数停止任务
        crawler.signals.connect(self.spider_idle, signal=signals.spider_idle)



        # 将日志的模板拿到这个对象中，后续函数需要用到
        self._clear_debug_pc   = crawler.settings.getbool('CLEAR_DEBUG_PC')
        self._clear_dupefilter = crawler.settings.getbool('CLEAR_DUPEFILTER')
        self._spider_id_debg_format = crawler.settings.get('DEBUG_PC_FORMAT')
        self._spider_id_task_format = crawler.settings.get('TASK_ID_FORMAT')
        self._spider_id_dupk_format = crawler.settings.get('SCHEDULER_DUPEFILTER_KEY')
        # 这里是将该任务开启绑定两个定时执行，永不停止的函数
        # 1/ 为了检查已经停止的任务并且清理任务的空间。
        # 2/ 为了获取到新的 start_url 开启新的任务脚本进行任务的初始化并且处理任务空间的问题。
        self.limit_check = 0 # 这个参数是想让不同的任务的检查时机稍微错开一点，不要都挤在 _stop_clear 一次迭代中
        self.limit_same  = 2 # 日志快照连续相同的次数
        self.interval    = 5 # 多少秒执行一次 检测关闭任务
        # (理论上平均检测关闭的时间大概为 (limit_check+1) * (limit_same+1) * interval )
        # 测试时可以适量调整小一些方便查看框架的问题
        self.interval_s  = 2 # 多少秒执行一次 检测启动任务
        self.limit_log   = 8 # 额外的配置，check stoping 限制显示任务数，防止出现如有几百个任务每次都要全部打印的情况。
        crawler.signals.connect(self.spider_opened, signal=signals.spider_opened)


    def spider_opened(self):
        # 1/ 启动清理函数
        # 2/ 启动任务加载函数
        task.LoopingCall(self._stop_clear).start(self.interval)
        task.LoopingCall(self.schedule_next_requests).start(self.interval_s)

    def _get_snapshot(self, stat_key):
        _snapshot = self.server.hgetall(stat_key)
        enqueue, dequeue = 0, 0
        snapshot = {}
        for k,v in _snapshot.items():
            if k.decode() == 'scheduler/enqueued/redis': enqueue += int(v.decode())
            if k.decode() == 'scheduler/dequeued/redis': dequeue += int(v.decode())
            snapshot[k.decode()] = v.decode()
        return snapshot, enqueue, dequeue

    def _stop_clear(self):
        taskids = []
        spider_tids_shot = self.spider_tids.copy()
        for taskid in spider_tids_shot:
            taskids.append(taskid)
            # 在一定时间后对统计信息的快照进行处理，如果快照相同，则计数
            # 相似数超过N次，则代表任务已经收集不到数据了，遂停止任务，并写入任务停止时间，（设置的时间越长越准，十分钟内差不多了）
            if self.spider_tids[taskid]['check_times'] != self.limit_check:
                self.spider_tids[taskid]['check_times'] += 1
            else:
                self.spider_tids[taskid]['check_times'] = 0
                stat_key = self._spider_id_task_format.format(taskid) % {'spider': self.name}

                snapshot, enqueue, dequeue = self._get_snapshot(stat_key)
                snapshot_e2d = enqueue == dequeue
                snapshot_md5 = hmac.new(b'',str(snapshot).encode(),'md5').hexdigest()
                if snapshot_md5 != self.spider_tids[taskid]['stat_snapshot'] or not snapshot_e2d:
                    self.spider_tids[taskid]['stat_snapshot'] = snapshot_md5
                    self.spider_tids[taskid]['same_snapshot_times'] = 0
                else:
                    self.spider_tids[taskid]['same_snapshot_times'] += 1
                    if self.spider_tids[taskid]['same_snapshot_times'] >= self.limit_same:
                        # 这里主要就是直接对任务结束进行收尾处理
                        # 后续需要各种删除 redis 中各种不需要的 key 来清理空间
                        # 另外再清理程序启动时生成的检测停止标签
                        if self._clear_debug_pc:
                            stat_pckey = self._spider_id_debg_format % {'spider': self.name}
                            self.server.delete(stat_pckey)
                        if self._clear_dupefilter:
                            dupefilter = self._spider_id_dupk_format.format(taskid) % {'spider': self.name}
                            self.server.delete(dupefilter)
                        module_name = self.spider_tids[taskid]['module_name']
                        # 在 redis 里面必须常驻的就是任务脚本
                        # 因为任务脚本会经过 hash 处理，以名字的 hash 作为 redis 的 key 进行存储
                        # 这样一个好处就是即便是存在大量重复的任务也只会存放一个任务脚本
                        # 同时 spider 对象也用的是脚本的 hash 作为 key 存放在执行程序的一个字典里面
                        # 为了考虑重复任务的可能，在任务结束时，删除[可能别的任务也在用的]对象的风险和开发难度很大，
                        # 实际上这种对象资源的消耗本身也比较小，所以对象也考虑常驻内存，
                        # 并且程序重启后，如果没有遇到需要用到之前任务的脚本也不会主动去实例化。节省开支。
                        # 另外还有一种恶性情况，就是还没有检查到任务停止的时候程序就意外关闭了
                        # 可能的影响：没有清理过滤池、没有写入finish_time、少数几条正在执行的任务丢失，
                        # 对其他正在执行的任务影响基本没有。所以不考虑了。
                        del self.spider_tids[taskid]
                        self.log_stat(taskid, 'finish_time')
                        snapshot,_,_ = self._get_snapshot(stat_key)
                        self.logger.info('Task {} is Stoped.\n'.format(taskid) + pprint.pformat(snapshot))
                        taskids.remove(taskid)

        if len(taskids) == 0:
            self.logger.info("Spider Task is Empty.")
        else:
            if len(taskids) > self.limit_log:
                fmt_log = '{}'.format(taskids[:self.limit_log]).replace(']',', ...][num:{}]'.format(len(taskids)))
            else:
                fmt_log = '{}'.format(taskids)
            self.logger.info("Check Task Stoping {}.".format(fmt_log))

    def schedule_next_requests(self):
        """Schedules a request if available"""
        # TODO: While there is capacity, schedule a batch of redis requests.
        for req in self.next_requests():
            self.crawler.engine.crawl(req, spider=self)


    # 下面的部分主要是处理 start_url 的部分，这里的处理是永久打开直至程序关闭的
    # 所以可以将此处魔改成对传递过来的参数各种初始化的地方，在发送端生成id后传入这边进行处理
    # 这里可以传过来一个简单的 json 数据来装脚本的代码部分，方便脚本的传递以及实例化
    def next_requests(self):
        """Returns a request to be scheduled or none."""
        use_set = self.settings.getbool('REDIS_START_URLS_AS_SET', defaults.START_URLS_AS_SET)
        fetch_one = self.server.spop if use_set else self.server.lpop
        # XXX: Do we need to use a timeout here?
        found = 0
        # TODO: Use redis pipeline execution.

        while found < self.redis_batch_size:
            data = fetch_one(self.redis_key)
            if not data:
                # Queue empty.
                break
            data = json.loads(data)

            # 这里需要生成最初的请求,基本上就是需要通过传过来的data进行最初的脚本运行
            # 通过生成对象来调配该对象的 start_requests 函数来生成最开始的请求
            # 需要传递的最初的json结构需要包含三个关键字参数
            # 1/ 'taskid'  # 任务id
            # 2/ 'name'    # 爬虫的名字
            # 3/ 'script'  # 脚本字符串

            # 这里暂时还没有处理异常情况，是因为异常信息的处理这时还没有决定
            # 不过比较符合心理预期的很可能是挂钩所有日志一并传入带 taskid 分配处理的管道
            module_name = save_script_as_a_module_file(data['script'])
            spider_obj  = load_spider_from_module(data['name'], module_name)
            taskid      = None
            for i in spider_obj().start_requests():
                if taskid is None: # 确认执行任务后再写入script到redis，防止浪费redis中的脚本存放空间
                    taskid = data['taskid']
                    self.server.set('vscrapy:script:{}'.format(module_name), json.dumps(data))
                    self.log_stat(taskid, 'start_time')
                    self.spider_tids[taskid] = {
                        'check_times': 0, 
                        'stat_snapshot': None, 
                        'same_snapshot_times': 0,
                        'module_name': module_name
                    }
                # 这里的重点就是 _plusmeta 的内容一定要是可以被序列化的数据，否则任务无法启动
                # 所以后续的开发这里需要注意，因为后续可能会增加其他的参数进去
                i._plusmeta = {}
                i._plusmeta.update({
                    'taskid': taskid, 
                    'module_name': module_name, 
                    'spider_name': data['name'],
                })
                yield i
                found += 1
            break

        if found:
            self.logger.debug("Read %s requests(start_requests) from new task %s.", found, taskid)


    def log_stat(self, taskid, key):
        # 由于默认的任务开启和关闭日志不是真实的任务开关闭时间
        # 所以这里需要使用自己设定的任务开启和关闭的的时间来处理任务状态
        tname = self._spider_id_task_format.format(taskid) % {'spider': self.name}
        value = str(datetime.utcnow() + timedelta(hours=8)) # 使用中国时区，方便我自己使用
        self.server.hsetnx(tname, key, value)


    def spider_idle(self):
        """Schedules a request if available, otherwise waits."""
        # XXX: Handle a sentinel to close the spider.
        raise DontCloseSpider


class RedisSpider(RedisMixin, Spider):
    """Spider that reads urls from redis queue when idle.

    Attributes
    ----------
    redis_key : str (default: REDIS_START_URLS_KEY)
        Redis key where to fetch start URLs from..
    redis_batch_size : int (default: CONCURRENT_REQUESTS)
        Number of messages to fetch from redis on each attempt.
    redis_encoding : str (default: REDIS_ENCODING)
        Encoding to use when decoding messages from redis queue.

    Settings
    --------
    REDIS_START_URLS_KEY : str (default: "<spider.name>:start_urls")
        Default Redis key where to fetch start URLs from..
    REDIS_START_URLS_BATCH_SIZE : int (deprecated by CONCURRENT_REQUESTS)
        Default number of messages to fetch from redis on each attempt.
    REDIS_START_URLS_AS_SET : bool (default: False)
        Use SET operations to retrieve messages from the redis queue. If False,
        the messages are retrieve using the LPOP command.
    REDIS_ENCODING : str (default: "utf-8")
        Default encoding to use when decoding messages from redis queue.

    """

    @classmethod
    def from_crawler(self, crawler, *args, **kwargs):
        obj = super(RedisSpider, self).from_crawler(crawler, *args, **kwargs)
        obj.setup_redis(crawler)
        return obj


class RedisCrawlSpider(RedisMixin, CrawlSpider):
    """Spider that reads urls from redis queue when idle.

    Attributes
    ----------
    redis_key : str (default: REDIS_START_URLS_KEY)
        Redis key where to fetch start URLs from..
    redis_batch_size : int (default: CONCURRENT_REQUESTS)
        Number of messages to fetch from redis on each attempt.
    redis_encoding : str (default: REDIS_ENCODING)
        Encoding to use when decoding messages from redis queue.

    Settings
    --------
    REDIS_START_URLS_KEY : str (default: "<spider.name>:start_urls")
        Default Redis key where to fetch start URLs from..
    REDIS_START_URLS_BATCH_SIZE : int (deprecated by CONCURRENT_REQUESTS)
        Default number of messages to fetch from redis on each attempt.
    REDIS_START_URLS_AS_SET : bool (default: True)
        Use SET operations to retrieve messages from the redis queue.
    REDIS_ENCODING : str (default: "utf-8")
        Default encoding to use when decoding messages from redis queue.

    """

    @classmethod
    def from_crawler(self, crawler, *args, **kwargs):
        obj = super(RedisCrawlSpider, self).from_crawler(crawler, *args, **kwargs)
        obj.setup_redis(crawler)
        return obj
