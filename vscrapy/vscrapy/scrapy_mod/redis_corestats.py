"""
Extension for collecting core stats like items scraped and start/finish times
"""

from scrapy.extensions import corestats

class RedisCoreStats(corestats.CoreStats):
    def __init__(self, stats):
        super(RedisCoreStats, self).__init__(stats)


    # 以下这两个函数只能说明爬虫打开和关闭的时间，实际上是并不能说明任务打开和关闭的时间
    # 所以这两个函数都将重载成无效函数
    def spider_opened(self, spider):
        pass
        # self.stats.set_value('start_time', datetime.datetime.utcnow(), spider=spider)

    def spider_closed(self, spider, reason):
        pass
        # self.stats.set_value('finish_time', datetime.datetime.utcnow(), spider=spider)
        # self.stats.set_value('finish_reason', reason, spider=spider)



    # 以下三个参数和原框架内相异的部分就是在这个函数中增加了一些原本能配置进来的参数
    def item_scraped(self, item, spider, response):
        self.stats.inc_value('item_scraped_count', spider=spider)

    def response_received(self, spider, request, response):
        self.stats.inc_value('response_received_count', spider=spider)

    def item_dropped(self, item, spider, exception, response):
        reason = exception.__class__.__name__
        self.stats.inc_value('item_dropped_count', spider=spider)
        self.stats.inc_value('item_dropped_reasons_count/%s' % reason, spider=spider)
