# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from twisted.internet import defer
from twisted.enterprise import adbapi
from scrapy.exceptions import NotConfigured
from scrapy.utils.python import global_object_name

import hmac
import json
import logging
import traceback
logger = logging.getLogger(__name__)

def import_driver(drivers, preferred=None):
    if preferred:
        drivers = [preferred]

    v = None
    for d in drivers:
        try:
            v = __import__(d, None, None)
            logger.info('+ Enable Use [{}] db driver.'.format(d))
        except ImportError:
            logger.info('- Unable Use [{}] db driver.'.format(d))
    if v:
        logger.info('Use [{}] as default db driver.'.format(v.__name__))
        return v
    raise ImportError("Unable to import " + " or ".join(drivers))

class VscrapyPipeline(object):

    def __init__(self, mysql_drivers, preferred):

        # 不考虑不同的数据库的收尾工作，因为一般来说不可能会有人使用超过几千几百个数据库的连接
        # 所以这里的数据库配置将持久，直到爬虫关闭都不主动清理空间。
        # 这里对不同连接的保存以 hash key 作为存储，保证了重复度
        self.dbn = {}
        self.db = None # 默认的数据库连接方式

        try:
            self.db = import_driver(mysql_drivers, preferred)
        except ImportError as e:
            logger.debug(e)
            raise NotConfigured

    @classmethod
    def from_settings(cls, settings):

        mysql_drivers = settings.get('MYSQL_DRIVERS', None)
        preferred = settings.get('MYSQL_PREFER_DRIVER', None)

        return cls(mysql_drivers, preferred)


    @classmethod
    def from_crawler(cls, crawler):
        # 绑定状态输出
        instance = cls.from_settings(crawler.settings)
        instance.stats = crawler.stats
        return instance


    def process_item(self, item, spider):
        '''
        当你需要直接将数据传入数据库的时候只需要在 item里面加一个字段: __mysql__
        这个字段里面需要详细描述需要连接的数据库以及需要传入的表的名字

        __mysql__ = {
            'host':'127.0.0.1'  # 该字段是必须的
            'port':3306         # 该字段是必须的
            'user':'user'       # 该字段是必须的
            'passwd':'mypass'   # 该字段是必须的，不过由于不同的库函数的关键字不同
                                # 这里可以根据部署时使用连接数据库方式的关键字
                                # 所以也可以是 password
            'dbapi':'pymysql'   # 【可选】 使用的连接数据库的方式，如果有多个可以使用，可以通过该处配置
                                # 通常数据库会默认使用一个可以连接的方式，按照 ['pymysql','MySQLdb','mysql.connector'] 的顺序
                                # 自动选择一个可用链接库作为默认连接方式，而且在该框架服务端启动的时候都会显示哪些可以使用
                                # 由于 adbapi.ConnectionPool 这个函数的参数命名关系，这里也可以设置为 'dbapiName'，
                                # 不过在配置时请不要将 'dbapi' 与 'dbapiName' 重复配置。
            'db':'mydb'         # 【可选】 存储的数据库名
            'table':'mytable'   # 【可选】 存储的表格名，如不填，将会以任务id和vscrapy拼接的方式存储
                                # eg. vscrapy_7
                                # 数据库和数据库表如果不存在都会自动创建，并且一旦创建就不能修改字段名字
                                # 新增的数据也不能传入数据表中。
                                # 如果自定义表时需要使用 taskid，那么就在table字符串中增加'{taskid}'
                                # eg. 'mytable_{taskid}' 这样表名会自动添加 taskid
        }

        *另外非常需要注意的是，这个字段不能动态的放置数据，因为这里只需要配置连接方式
        这里使用的连接方式将会在第一次配置的时候以 hash key 的方式在该 pipeline 对象的存储字典里生成一个连接池对象
        主要是应对多种场合下的一次任务甚至可能存储多张表的需求
        '''

        mysql_config = item.pop('__mysql__', None)

        if mysql_config and item:
            if type(mysql_config) is dict:
                _plusmeta = item.get('b2b89079b2f7befcf4691a98a3f0a2a2')
                if _plusmeta:
                    taskid = _plusmeta.get('taskid')
                    spider = _plusmeta.get('spider')
                else:
                    raise TypeError('Unable Parse _plusmeta.')

                # 这里没有就会使用默认的数据库连接方式
                # adbapi.ConnectionPool 的第一个参数名字为 dbapiName，以此名为此处命名便于理解。
                dbapiName   = mysql_config.pop('dbapiName', None) or mysql_config.pop('dbapi', None) or self.db.__name__
                db          = mysql_config.get('db', None) or 'vscrapy'
                table       = mysql_config.pop('tablename', None) or mysql_config.pop('table', None) or 'vscrapy_{taskid}'
                table       = table.format(taskid=taskid)
                mysql_config.setdefault('charset','utf8mb4')
                mysql_config.setdefault('db', db)

                # 确保需要使用的库和表名存在
                if not(dbapiName and table and db):
                    raise TypeError('UnHandle abapiName:{} & table:{} & db:{}'.format(dbapiName, table, db))

                # 创建数据库以及数据表之后才进行对本地 dbn 连接池的绑定。
                dbk = hmac.new(b'',str(mysql_config).encode(),'md5').hexdigest()
                _item = item.copy()
                _item.pop('b2b89079b2f7befcf4691a98a3f0a2a2')
                if dbk not in self.dbn:
                    pool = adbapi.ConnectionPool(dbapiName, **mysql_config)

                    # 初始化生成数据库名以及数据库表名字的函数不能异步，所以这里使用了原始的连接执行的方式
                    # 可以通过 pool 直接使用 dbapiName 名字的连接方式。
                    self.init_database(pool, mysql_config, db, table, _item, taskid, spider)
                    self.dbn[dbk] = pool

                self.dbn[dbk].runInteraction(self.insert_item, db, table, _item, taskid, spider)
                return item
            else:
                raise TypeError('Unable Parse mysql_config type:{}'.format(type(mysql_config)))
        else:
            return item


    def _hook(self, taskid, spider_name):
        # 这里是这个框架关于日志处理的魔法部分。
        # 你需要了解，虽然你看不到，但是一些函数的空间确实是被挂钩的。挂钩了 response 的名字的对象
        # 并且 response 这个对象需要有 _plusmeta 属性为一个字典，该字典里面还有 'taskid' 字段包含的taskid
        # 该环境还挂钩了 spider 这个名字的对象，并且这个对象需要一个 name 的属性来定位服务端的 spider 名字
        class model:pass
        response = spider = model()
        response._plusmeta = {}
        response._plusmeta['taskid'] = taskid
        spider.name = spider_name
        return response, spider


    def insert_item(self, conn, db, table, item, taskid, spider_name):
        response, spider = self._hook(taskid, spider_name) # 这里有看不见的钩子

        # 使用 json 通用处理，存储时保证了数据类型，取数据时候使用 json.loads 来解析类型。
        table_sql = ""
        for k,v in item.items():
            table_sql += "'{}',".format(json.dumps(v))

        try:
            conn.execute('INSERT INTO `{}`.`{}` VALUES({})'.format(db, table, table_sql.strip(',')))
            self.stats.inc_value('item_mysql/db:{}/table:{}/count'.format(db, table), spider=spider)
        except Exception as e:
            traceback.print_exc()

            ex_class = global_object_name(e.__class__)
            self.stats.inc_value('item/exception_count', spider=spider)
            self.stats.inc_value('item/exception_type_count/%s' % ex_class, spider=spider)

    def init_database(self, pool, mysql_config, db, table, item, taskid, spider_name):
        response, spider = self._hook(taskid, spider_name) # 这里有看不见的钩子

        # 需要注意的是，在一些老版本的mysql 里面并不支持 utf8mb4。
        # 所以：这都什么时代了，赶紧使用大于 5.5 版本的 mysql !
        charset = mysql_config.get('charset')
        
        '''
        CREATE TABLE `student` (
          `s_id` MEDIUMTEXT NULL,
          `s_name` MEDIUMTEXT NULL,
          `s_age` MEDIUMTEXT NULL,
          `s_msg` MEDIUMTEXT NULL,
        );
        '''
        try:
            conn = pool.dbapi.connect(**mysql_config)
            cursor = conn.cursor()
            table_sql = ""
            for k,v in item.items():
                # 创建db，创建表名，所有字段都以 MEDIUMTEXT 存储
                # MEDIUMTEXT 最大能使用16M 的长度，所以对于一般的html文本已经足够。
                table_sql += '`{}` MEDIUMTEXT NULL,'.format(str(k))
            cursor.execute('Create Database If Not Exists {} Character Set {}'.format(db, charset))
            cursor.execute('Create Table If Not Exists `{}`.`{}` ({})'.format(db, table, table_sql.strip(',')))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            traceback.print_exc()

            ex_class = global_object_name(e.__class__)
            self.stats.inc_value('create_db/exception_count', spider=spider)
            self.stats.inc_value('create_db/exception_type_count/%s' % ex_class, spider=spider)
