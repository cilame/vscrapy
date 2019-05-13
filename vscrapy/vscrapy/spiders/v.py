from vscrapy.scrapy_redis_mod.spiders import (
    RedisSpider,
    load_spider_from_module,
    save_script_as_a_module_file,
)

import json
from scrapy import Request

class VSpider(RedisSpider):
    """Spider that reads urls from redis queue (myspider:start_urls)."""
    name = 'v'

    def parse(self, response):

        spider_name = response._plusmeta.get('spider_name')
        module_name = response._plusmeta.get('module_name')
        __callerr__ = response._plusmeta.get('__callerr__')

        # 在传递脚本的 start_requests 执行时会执行一次将脚本加载成对象放入
        # 如果是非 start_requests 执行的任务则需要在 parse 函数里面确认加载进框架
        # 并且不同的机器也需要考虑脚本的分配获取，所以脚本也需要上传。
        if module_name not in self.spider_objs:
            try:
                self.spider_objs[module_name] = load_spider_from_module(spider_name, module_name)
            except:
                data = self.server.get('vscrapy:script:{}'.format(module_name))
                data = json.loads(data)
                module_name = save_script_as_a_module_file(data['script'])
                self.spider_objs[module_name] = load_spider_from_module(spider_name, module_name)

        spider = self.spider_objs[module_name]
        parsefunc = getattr(spider, __callerr__.get('callback'))
        parsedata = parsefunc(spider, response)
        if parsedata:
            if getattr(parsedata, '__iter__') and type(parsedata) != str:
                for r in parsedata:
                    if isinstance(r, (Request,)):
                        r._plusmeta = response._plusmeta
                        yield r
                    else:
                        # 这里大概就是 item对象或者是字典
                        yield r
            elif isinstance(parsedata, (Request,)):
                r = parsedata
                r._plusmeta = response._plusmeta
                yield r
            else:
                # 这里大概就是 item对象或者是字典
                yield parsedata

        # 后面可以考虑在这里对item的输出进行挂钩，让输出数据能带有一些额外的信息