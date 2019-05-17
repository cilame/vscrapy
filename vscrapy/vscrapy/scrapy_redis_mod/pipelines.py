from scrapy.utils.misc import load_object
from scrapy.utils.serialize import ScrapyJSONEncoder
from twisted.internet.threads import deferToThread

from . import connection, defaults


default_serialize = ScrapyJSONEncoder().encode


class RedisPipeline(object):
    """Pushes serialized item into a redis list/queue

    Settings
    --------
    REDIS_ITEMS_KEY : str
        Redis key where to store items.
    REDIS_ITEMS_SERIALIZER : str
        Object path to serializer function.

    """

    def __init__(self, server,
                 key=defaults.PIPELINE_KEY,
                 serialize_func=default_serialize):
        """Initialize pipeline.

        Parameters
        ----------
        server : StrictRedis
            Redis client instance.
        key : str
            Redis key where to store items.
        serialize_func : callable
            Items serializer function.

        """
        self.server = server
        self.key = key
        self.serialize = serialize_func

    @classmethod
    def from_settings(cls, settings):
        params = {
            'server': connection.from_settings(settings),
        }
        if settings.get('REDIS_ITEMS_KEY'):
            params['key'] = settings['REDIS_ITEMS_KEY']
        if settings.get('REDIS_ITEMS_SERIALIZER'):
            params['serialize_func'] = load_object(
                settings['REDIS_ITEMS_SERIALIZER']
            )

        return cls(**params)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def process_item(self, item, spider):
        return deferToThread(self._process_item, item, spider)

    def _process_item(self, item, spider):
        # 若是不想存入redis的管道，直接在前面的管道删除掉 b2b89079b2f7befcf4691a98a3f0a2a2 key 即可
        _item = item.copy()
        if _item.pop('b2b89079b2f7befcf4691a98a3f0a2a2', None):
            key = self.item_key(item, spider)
            data = self.serialize(_item)
            self.server.lpushx(key, data)
            return item

    def item_key(self, item, spider):
        """Returns redis key based on given spider.

        Override this function to use a different key depending on the item
        and/or spider.

        """
        # 将数据管道绑定taskid，对数据进行分管道存储，方便后续取出数据，之所以不用 taskid 作为key
        # 而使用 b2b89079b2f7befcf4691a98a3f0a2a2 这个key是保证不与用户的可能会设置 taskid 作为key 冲突。
        return self.key.format(item.get('b2b89079b2f7befcf4691a98a3f0a2a2')) % {'spider': spider.name}
