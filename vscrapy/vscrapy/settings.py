# Scrapy settings for example project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
import uuid, time





SPIDER_MODULES = ['vscrapy.spiders']
NEWSPIDER_MODULE = 'vscrapy.spiders'
LOG_LEVEL = 'DEBUG'





# 一定不能开启就尝试清空任务管道了，不然测试脚本会由于提交任务太快导致部分任务被抛弃
# SCHEDULER_FLUSH_ON_START = False




# 1/ scrapy 的魔改处理
EXTENSIONS = {
    'scrapy.extensions.logstats.LogStats':   None, # 关闭这个日志输出，因为无法获取当前任务id，遂放弃
    'scrapy.extensions.corestats.CoreStats': None, # 关闭这个日志处理，使用魔改的日志处理
    'vscrapy.scrapy_mod.redis_corestats.RedisCoreStats': True,
}
STATS_CLASS = 'vscrapy.scrapy_mod.redis_statscollectors.RedisStatsCollector'




# 2/ scrapy_redis 的魔改配置
SCHEDULER_DUPEFILTER_CLASS = "vscrapy.scrapy_redis_mod.dupefilter.RFPDupeFilter"
SCHEDULER_QUEUE_CLASS      = "vscrapy.scrapy_redis_mod.queue.PriorityQueue" #PriorityQueue
SCHEDULER                  = "vscrapy.scrapy_redis_mod.scheduler.Scheduler"

ITEM_PIPELINES = {
    'vscrapy.pipelines.VscrapyPipeline':                300, # 后续需要考虑数据存储的插件部分
    'vscrapy.scrapy_redis_mod.pipelines.RedisPipeline': 400,
}

# 至少需要魔改四个 scrapy_redis 源码中的四个文件，目的是要让这几个任务都能识别到任务id
# 1/ dupefilter
# 2/ queue
# 3/ scheduler
# 4/ pipelines

# 配置redis链接配置的一些方法
# REDIS_HOST = '47.99.126.229'
# REDIS_PORT = 6379
REDIS_ENCODING = 'utf-8'
REDIS_PARAMS = {
    'host':'47.99.126.229',
    'port':6379,
    'password':'vilame',
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'encoding': REDIS_ENCODING,
}



# DEBUG_PC 将用于 DEBUG 不同的 pc 间执行的情况。
# True:将会额外通过 pc 的 mac 标签生成一个统计key信息来统计单个PC的执行数量
DEBUG_PC = False

mac,sid = uuid.UUID(int = uuid.getnode()).hex[-12:], str(uuid.uuid4())[:5]
DEBUG_PC_FORMAT  = 'vscrapy:stats:pc/{}:rdkey/{}/stat/%(spider)s'.format(mac, sid)
TASK_ID_FORMAT   = 'vscrapy:stats:%(spider)s/taskid/{}/stat'
DEPTH_MAX_FORMAT = 'taskid:{}:%(spider)s'



SCHEDULER_QUEUE_KEY      = 'vscrapy:gqueue:%(spider)s/requests'
SCHEDULER_DUPEFILTER_KEY = 'vscrapy:gqueue:%(spider)s/taskid/{}/dupefilter'
START_URLS_KEY           = 'vscrapy:gqueue:%(name)s:start_urls'
PIPELINE_KEY             = 'vscrapy:gqueue:%(spider)s:items'



# 在任务执行结束的时候
# 将部分的的redis key删除，清空内容，节省空间
# 该参数默认为True，默认清除的有该任务使用的过滤池，其他任务的过滤池不影响
CLEAR_DUPEFILTER = True
# 该参数默认为False，默认不清理该关键词，如果DEBUG_PC没有开启，该关键词直接就不会生成。
# 主要用于个人测试，一般线上环境不需要修改该参数。
CLEAR_DEBUG_PC = False






# 必要的中间件，主要是 VDownloaderMiddleware 这个中间件
# VSpiderMiddleware 暂时还没有使用到，因为这里没有挂钩就已经运行很好了。
SPIDER_MIDDLEWARES = {
    'vscrapy.middlewares.VSpiderMiddleware': 0,
}

DOWNLOADER_MIDDLEWARES = { 
    'vscrapy.middlewares.VDownloaderMiddleware': 0, 
}




# Default requests serializer is pickle, but it can be changed to any module
# with loads and dumps functions. Note that pickle is not compatible between
# python versions.
# Caveat: In python 3.x, the serializer must return strings keys and support
# bytes as values. Because of this reason the json or msgpack module will not
# work by default. In python 2.x there is no such issue and you can use
# 'json' or 'msgpack' as serializers.
#SCHEDULER_SERIALIZER = "scrapy_redis.picklecompat"

# Don't cleanup redis queues, allows to pause/resume crawls.
# SCHEDULER_PERSIST = True

# Schedule requests using a priority queue. (default)
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

# Alternative queues.
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.FifoQueue'
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.LifoQueue'

# Max idle time to prevent the spider from being closed when distributed crawling.
# This only works if queue class is SpiderQueue or SpiderStack,
# and may also block the same time when your spider start at the first time (because the queue is empty).
#SCHEDULER_IDLE_BEFORE_CLOSE = 10

# The item pipeline serializes and stores the items in this redis key.
#REDIS_ITEMS_KEY = '%(spider)s:items'

# The items serializer is by default ScrapyJSONEncoder. You can use any
# importable path to a callable object.
#REDIS_ITEMS_SERIALIZER = 'json.dumps'

# Specify the host and port to use when connecting to Redis (optional).
# REDIS_HOST = 'localhost'
# REDIS_PORT = 6379

# Specify the full Redis URL for connecting (optional).
# If set, this takes precedence over the REDIS_HOST and REDIS_PORT settings.
#REDIS_URL = 'redis://user:pass@hostname:9001'

# Custom redis client parameters (i.e.: socket timeout, etc.)
#REDIS_PARAMS  = {}
# Use custom redis client class.
#REDIS_PARAMS['redis_cls'] = 'myproject.RedisClient'

# If True, it uses redis' ``SPOP`` operation. You have to use the ``SADD``
# command to add URLs to the redis queue. This could be useful if you
# want to avoid duplicates in your start urls list and the order of
# processing does not matter.
#REDIS_START_URLS_AS_SET = False

# Default start urls key for RedisSpider and RedisCrawlSpider.
#REDIS_START_URLS_KEY = '%(name)s:start_urls'

# Use other encoding than utf-8 for redis.
#REDIS_ENCODING = 'latin1'


