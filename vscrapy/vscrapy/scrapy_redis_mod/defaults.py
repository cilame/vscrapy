import redis
import uuid

REDIS_CLS = redis.StrictRedis
REDIS_ENCODING = 'utf-8'
# Sane connection defaults.
REDIS_PARAMS = {
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'encoding': REDIS_ENCODING,
}


mac = uuid.UUID(int = uuid.getnode()).hex[-12:]
'''
后面根据需要魔改下面的关于 redis 队列配置相关的部分，
让其能够接收 spiderid 以及 taskid 的标识，并且不要将需要的配置在此处，
需要配置在 settings 里面不然初始化会存在问题，
这里的配置仅仅作为一个模板来使用
'''

SCHEDULER_QUEUE_KEY      = 'vscrapy:gqueue:%(spider)s/requests'
SCHEDULER_DUPEFILTER_KEY = 'vscrapy:gqueue:%(spider)s/taskid/{}/dupefilter'
START_URLS_KEY           = 'vscrapy:gqueue:%(name)s:start_urls'
START_URLS_AS_SET        = False
DUPEFILTER_KEY           = 'dupefilter:%(timestamp)s'
PIPELINE_KEY             = 'vscrapy:gqueue:%(spider)s:items'


# 任务停止时的清理工作，清理过滤池，清理 DEBUG_PC 任务记录
CLEAR_DUPEFILTER = True
CLEAR_DEBUG_PC = False


# 默认使用魔改后的各种类插件
SCHEDULER_DUPEFILTER_CLASS = "v.scrapy_redis_mod.dupefilter.RFPDupeFilter"
SCHEDULER_QUEUE_CLASS      = "v.scrapy_redis_mod.queue.PriorityQueue"
SCHEDULER                  = "v.scrapy_redis_mod.scheduler.Scheduler"


ITEM_PIPELINES = {
    'v.pipelines.VPipeline':                      300,
    'v.scrapy_redis_mod.pipelines.RedisPipeline': 400,
}