"""
Extension for collecting core stats like items scraped and start/finish times
"""

from scrapy.extensions import corestats

class RedisCoreStats(corestats.CoreStats):
    def __init__(self, stats):
        super(RedisCoreStats, self).__init__(stats)

    # 以下两个参数和原框架内相异的部分就是在这个函数中增加了一些原本能配置进来的参数
    def item_scraped(self, item, spider, response):
        self.stats.inc_value('item_scraped_count', spider=spider)

    def response_received(self, spider, request, response):
        self.stats.inc_value('response_received_count', spider=spider)