from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import Spider, CrawlSpider

from . import connection, defaults
from .utils import bytes_to_str

import json


import os
import sys
import hmac
import importlib
import traceback

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
        # The idle signal is called when the spider has no requests left,
        # that's when we will schedule new requests from redis queue
        crawler.signals.connect(self.spider_idle, signal=signals.spider_idle)









    # 下面的部分主要是处理 start_url 的部分，这里的处理是永久打开直至程序关闭的
    # 所以可以将此处魔改成对传递过来的参数各种初始化的地方，在这里也将是生成任务id的最佳地方。
    # 这里可以传过来一个简单的 json 数据来装脚本的代码部分，方便脚本的传递以及实例化
    def next_requests(self):
        """Returns a request to be scheduled or none."""
        use_set = self.settings.getbool('REDIS_START_URLS_AS_SET', defaults.START_URLS_AS_SET)
        fetch_one = self.server.spop if use_set else self.server.lpop
        # XXX: Do we need to use a timeout here?
        found = 0
        # TODO: Use redis pipeline execution.

        def get_unique_task_id():
            return self.server.incrby('vscrapy:taskidx')

        while found < self.redis_batch_size:
            data = fetch_one(self.redis_key)
            if not data:
                # Queue empty.
                break
            data = json.loads(data)

            # 这里需要生成最初的请求,基本上就是需要通过传过来的data进行最初的脚本对象,
            # 通过生成对象来调配该对象的 start_requests 函数来生成最开始的请求
            module_name = save_script_as_a_module_file(data['script'])
            spider_obj  = load_spider_from_module(data['name'], module_name)
            tid = None
            for i in spider_obj().start_requests():
                if tid is None:
                    tid = get_unique_task_id()
                    self.server.set('vscrapy:script:{}'.format(module_name), json.dumps(data))
                i._plusmeta = {}
                i._plusmeta.update({'taskid': tid, 'module_name': module_name, 'spider_name': data['name']})
                yield i
                found += 1
            break

        if found:
            self.logger.debug("Read %s requests from new task '%s'", found, tid)

    def schedule_next_requests(self):
        """Schedules a request if available"""
        # TODO: While there is capacity, schedule a batch of redis requests.
        for req in self.next_requests():
            self.crawler.engine.crawl(req, spider=self)

    def spider_idle(self):
        """Schedules a request if available, otherwise waits."""
        # XXX: Handle a sentinel to close the spider.
        self.schedule_next_requests()
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
