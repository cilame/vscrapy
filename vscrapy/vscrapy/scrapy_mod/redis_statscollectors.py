"""
Scrapy extension for collecting scraping stats
"""
import redis
import pprint
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from scrapy.statscollectors import StatsCollector
from vscrapy.scrapy_redis_mod.connection import from_settings

import uuid
import time
import inspect

class RedisStatsCollector:

    # 这个日志主要是字符串
    e = (
        'finish_reason',
    )

    # 这个日志主要是时间戳
    t = (
        'finish_time',
        'start_time',
    )

    _spider_unique_id_name = 'vscrapy:spiderid/index'
    _spider_id_debg_format = 'vscrapy:spiders:mac/{}:start/{}/stat/%(spider)s'
    _spider_id_task_format = 'vscrapy:spiders:taskid/{}/stat/%(spider)s'

    def __init__(self, crawler):
        self._dump = crawler.settings.getbool('STATS_DUMP')
        self._stats = {}
        self.server     = from_settings(crawler.settings)
        mac,sid = uuid.UUID(int = uuid.getnode()).hex[-12:], self._mk_unique_spider_id()
        self.spider_fmt = self._spider_id_debg_format.format(mac, sid)
        self.encoding   = self.server.connection_pool.connection_kwargs.get('encoding')

        # 每台机器通过 mac 使用各自机器的日志空间
        # 由于这个 id 的实现本身就是用来检测机器可能出现的问题
        # 一般来说需要考虑机器影响问题，所以使用 mac 地址，需要更详细的横向对比功能

    # 对于每一个spiderid都生成一个唯一的spider处理stat信息
    def _mk_unique_spider_id(self):
        return time.strftime("%Y%m%d-%H%M%S",time.localtime())
        return self.server.incrby(self._spider_unique_id_name)


    # 该函数没有被框架使用，属于开发者使用的接口
    def get_stats(self, spider=None):
        name = self.spider_fmt % {'spider':spider.name}
        _stat = {}
        for key,val in self.server.hgetall(name).items():
            key,val = key.decode(self.encoding),val.decode(self.encoding)
            try:
                if key in self.e: 
                    _stat[key] = val # 这里需要考虑从时间字符串加载时间 datetime.strptime(val,date_fmt) # finish_time, start_time
                elif key in self.t:
                    _stat[key] = datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    _stat[key] = int(val) 
            except:
                # 当存在无法被int处理的数据的时候就直接使用原本的字符串即可
                # 防御性的代码处理
                _stat[key] = val
        return _stat










    # 该函数没有被框架使用，属于开发者自己用于增加功能修改的接口，可能在后续个人开发中的初始化时候能用到
    def set_stats(self, stats, spider=None):
        for key in stats:
            name = self.spider_fmt % {'spider':spider.name}
            self.server.hset(name, key, stats[key])

    # 该函数和 set_stats 函数一样使用的概率较低，而且使用的插件在一般情况下是默认不装的，这里防御性处理一下
    def get_value(self, key, default=None, spider=None):
        if spider:
            name = self.spider_fmt % {'spider':spider.name}
            val = self.server.hget(name, key)
            if val:
                val = val.decode(self.encoding)
                if key in self.t:
                    ret = datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    if key not in self.e:
                        try:
                            ret = int(val)
                        except:
                            ret = str(val)
                    else:
                        ret = str(val)
                return ret
            else:
                return default
        else:
            return default






    def _mod_task(self, spider):
        '''
        可以在这个函数处挂钩处理，也是我这个框架的核心魔法。
        这里的函数环境向上两级就是各种日志信号的执行，这些信号内一般都存在request和response结构体。
        因为一些信息可以通过request和response中的meta传递，
        这样的话，就给了挂钩的空间，让stat能够带有一些类似任务id信息。
        比较方便处理多任务情况下的任务处理。
        后续可能会将该处的处理放到其他带有 self.server 操作的函数里面
        实现多任务的分隔处理。
        '''
        v = inspect.stack()[2][0].f_locals
        if 'request' in v:
            taskid = v['request'].meta.get('taskid') or 0


            
            # 这里考虑的是对任务的参数各种配置的初始化的各种问题





            tname = self._spider_id_task_format.format(taskid) % {'spider':spider.name}
        elif 'response' in v:
            taskid = v['response'].meta.get('taskid') or 0
        else:
            pass

    # 该框架主要使用到的两个接口就是
    # set_value
    # inc_value
    def set_value(self, key, value, spider=None):
        name = self.spider_fmt % {'spider':spider.name}
        if type(value) == datetime: value = str(value + timedelta(hours=8)) # 将默认utc时区转到中国，方便我使用
        self.server.hset(name, key, value)

    def inc_value(self, key, count=1, start=0, spider=None):
        if spider:
            self._mod_task(spider)
            name = self.spider_fmt % {'spider':spider.name}
            self.server.hincrby(name, key, count)
        else:
            '''
            部分参数会从spider还没有加载的时候就开始记录日志了，这样不行的
            这里将主动抛弃那个日志信息，我的框架需要考虑增加对每个spider的监控，
            所以将抛弃下面的日志信息处理，
            'log_count/INFO'  # log的数量
            log数的统计在分布式当中意义不大。
            '''
            pass

    # 这里的函数用于spider的深度计算，因为该值存储在redis里面，
    # 该比较函数有可能会每次请求redis，所以经优化考虑，在本地先存储一个最大值
    # 如果超过最大值就再请求redis，比较redis内部深度，这样对redis的压力稍微小一点
    def max_value(self, key, value, spider=None):
        self._stats.setdefault(spider.name, {})
        if key not in self._stats[spider.name]:
            self._stats[spider.name][key] = value
            name = self.spider_fmt % {'spider':spider.name}
            self.server.hset(name, key, value)
        else:
            if value > self._stats[spider.name][key]:
                self._stats[spider.name][key] = value
                name = self.spider_fmt % {'spider':spider.name}
                self.server.hset(name, key, value)

    # 该函数看似有用，实际上在框架里面并没有使用到。
    # 如果后续开发需要使用，就按照max_value的格式处写一份即可
    def min_value(self, key, value, spider=None):
        pass

    # 这里需要考虑任务重启时候的初始化，目前是没有使用
    # 不过由于这个函数的特殊性，所以后续可能会考虑挂钩此处。
    def open_spider(self, spider):
        pass

    def close_spider(self, spider, reason):
        if self._dump:
            logger.info("Dumping Scrapy stats:\n" + pprint.pformat(self.get_stats(spider)),
                        extra={'spider': spider})

