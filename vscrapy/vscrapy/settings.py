# Scrapy settings for example project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

SPIDER_MODULES = ['vscrapy.spiders']
NEWSPIDER_MODULE = 'vscrapy.spiders'
LOG_LEVEL = 'DEBUG'





# 4 test
SCHEDULER_FLUSH_ON_START = True




# 1/ scrapy 的魔改处理
EXTENSIONS = {
    'scrapy.extensions.corestats.CoreStats': None, # 关闭这个日志处理，使用魔改的日志处理
    'vscrapy.scrapy_mod.redis_corestats.RedisCoreStats': True,
}
STATS_CLASS = 'vscrapy.scrapy_mod.redis_statscollectors.RedisStatsCollector'





# 2/ scrapy_redis 的魔改配置
SCHEDULER_DUPEFILTER_CLASS = "vscrapy.scrapy_redis_mod.dupefilter.RFPDupeFilter"
SCHEDULER_QUEUE_CLASS      = "vscrapy.scrapy_redis_mod.queue.PriorityQueue"
SCHEDULER                  = "vscrapy.scrapy_redis_mod.scheduler.Scheduler"

ITEM_PIPELINES = {
    'vscrapy.pipelines.VscrapyPipeline':                300,
    'vscrapy.scrapy_redis_mod.pipelines.RedisPipeline': 400,
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


