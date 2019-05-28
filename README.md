# vscrapy 多任务分布式爬虫框架

**vscrapy 是一个依赖于 scrapy 的分布式爬虫框架**

vscrapy 只需一次部署。可以像是 scrapy 启动项目一样快速将一般的 scrapy 的爬虫项目脚本快速传到分布式执行。针对不同的任务，都会分配一个唯一的任务空间，空间中包含了该任务的过滤池，包含了该任务的统计日志，该任务的item管道。并且该工具带有一个简便的命令行工具，方便于提交任务，检查任务日志。

## vscrapy 项目是基于对 scrapy_redis 的修改

*在开发该框架的过程中，由于为了多任务不冲突，里面的代码需要非常耦合的处理，加之 scrapy_redis 本身项目并不是很重，所以我这里就将其大部分代码包含其中，当然其中有一定非常必要的修改。由于已包含了 scrapy_redis 的增强版代码，所以并不会额外下载 scrapy_redis。*

> 在代码中，所有涉及到重要修改的部分我都有注释，里面详细说明了为什么修改的原因。

vscrapy 源于 scrapy_redis 项目，开源地址 [scrapy_redis](https://github.com/rmax/scrapy-redis "scrapy_redis")，并在开源协议的许可范围内进行了优化，感谢代码的贡献者提供的最原始的框架让这个项目得以实现。


## 安装方式

`pip install vscrapy`

*如果有安装 git 还可以用下面的安装方式*

`pip install git+https://github.com/cilame/vscrapy.git`

## 使用方式

*vscrapy 提供了一个便捷的命令行工具，基本上所有的功能都依赖于该命令行工具，你可以通过直接在命令行中输入 `vscrapy` 便可查询命令所的帮助内容。以下便是 `1.0.1` 版本所显示的帮助内容*

```bash
C:\Users\Administrator>vscrapy
Vscrapy ver:1.0.1. (multi task scrapy_redis.)

Usage
  vscrapy <command> [options] [args]

Command
  run       run a vscrapy worker. (pls set redis config first.)
  crawl     use config setting connect redis send spider script start crawl
  stat      use taskid check task work stat.
  config    config default host,port,password,db

Command Help
  vscrapy <command>

General Options
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (means no password)
  -db,--db       ::redis db.       default: 0
```

#### 1 连接 redis

- 在执行命令前，请首先配置好 redis 并且能够在需要部署的分布式机器上能够连接上 redis. 你可以用 `vscrapy config` 来配置默认设置，当然你也可以通过在命令行里面直接添加连接配置 `vscrapy stat -ho 192.168.0.7 -po 6666 -pa vilame` 也可以实现当前配置，这取决于你的喜好。

> *注意，当你不设定命令行的配置时，不设定的配置会使用 config 中的配置。*

#### 2 配置config
- 直接输入 `vscrapy config` 将显示当前配置以及有哪些可选配置参数。配置时只需添加参数即可。

```
C:\Users\Administrator>vscrapy config -ho 192.168.1.7 -po 6666 -pa vilame
[options]
  type<param>
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (no password)
  -db,--db       ::redis db.       default: 0
  type<toggle>
  -cl,--clear    ::clear redis settings.
current config [use -cl/--clear clear this settings]:
{
    "host": "192.168.1.7",
    "port": 6666,
    "password": "vilame",
    "db": 0
}
```

#### 3 启动分布式

- 当你已经配置好 `config` 之后，你不在命令行配置的参数将只用默认配置里面的参数。启动方式也非常简单。`vscrapy run` 这样便能开启一个分布式。

```bash
C:\Users\Administrator>vscrapy run
2019-05-28 22:51:08 [scrapy.utils.log] INFO: Scrapy 1.5.1 started (bot: scrapybot)
2019-05-28 22:51:08 [scrapy.utils.log] INFO: Versions: lxml 4.3.0.0, libxml2 2.9.7, cssselect 1.0.3, parsel 1.5.1, w3lib 1.19.0, Twisted 18.9.0, Python 3.6.7 (v3.6.7:6ec5cf24b7, Oct 20 2018, 13:35:33) [MSC v.1900 64 bit (AMD64)], pyOpenSSL 18.0.0 (OpenSSL 1.1.0i  14 Aug 2018), cryptography 2.3.1, Platform Windows-10-10.0.17763-SP0
2019-05-28 22:51:08 [scrapy.crawler] INFO: Overridden settings: {'NEWSPIDER_MODULE': 'vscrapy.vscrapy.spiders', 'SCHEDULER': 'vscrapy.vscrapy.scrapy_redis_mod.scheduler.Scheduler', 'SPIDER_MODULES': ['vscrapy.vscrapy.spiders'], 'STATS_CLASS': 'vscrapy.vscrapy.scrapy_mod.redis_statscollectors.RedisStatsCollector'}
2019-05-28 22:51:08 [scrapy.middleware] INFO: Enabled extensions:
['vscrapy.vscrapy.scrapy_mod.redis_corestats.RedisCoreStats']
2019-05-28 22:51:08 [v] INFO: Reading start URLs from redis key 'vscrapy:gqueue:v:start_urls' (batch size: 16, encoding: utf-8
2019-05-28 22:51:08 [scrapy.middleware] INFO: Enabled downloader middlewares:
['vscrapy.vscrapy.middlewares.VDownloaderMiddleware',
 'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware',
 'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware',
 'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware',
 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware',
 'vscrapy.vscrapy.scrapy_mod._retry.RetryMiddleware',
 'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware',
 'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware',
 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware',
 'scrapy.downloadermiddlewares.cookies.CookiesMiddleware',
 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware',
 'scrapy.downloadermiddlewares.stats.DownloaderStats']
2019-05-28 22:51:08 [scrapy.middleware] INFO: Enabled spider middlewares:
['vscrapy.vscrapy.middlewares.VSpiderMiddleware',
 'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware',
 'scrapy.spidermiddlewares.offsite.OffsiteMiddleware',
 'scrapy.spidermiddlewares.referer.RefererMiddleware',
 'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware',
 'scrapy.spidermiddlewares.depth.DepthMiddleware']
2019-05-28 22:51:08 [vscrapy.vscrapy.pipelines] INFO: - Unable Use [MySQLdb] db driver.
2019-05-28 22:51:08 [vscrapy.vscrapy.pipelines] INFO: + Enable Use [pymysql] db driver.
2019-05-28 22:51:08 [vscrapy.vscrapy.pipelines] INFO: - Unable Use [mysql.connector] db driver.
2019-05-28 22:51:08 [vscrapy.vscrapy.pipelines] INFO: Use [pymysql] as default db driver.
2019-05-28 22:51:08 [scrapy.middleware] INFO: Enabled item pipelines:
['vscrapy.vscrapy.pipelines.VscrapyPipeline',
 'vscrapy.vscrapy.scrapy_redis_mod.pipelines.RedisPipeline']
2019-05-28 22:51:08 [scrapy.core.engine] INFO: Spider opened
2019-05-18 12:14:09 [v] INFO: Spider Task is Empty.
2019-05-18 12:14:14 [v] INFO: Spider Task is Empty.
2019-05-18 12:14:19 [v] INFO: Spider Task is Empty.
```

#### 3 提交你的任务

- 在一个普通的 scrapy 项目中如果只是执行 `vscrapy crawl` 也会显示当前能找到的所有 spider_name 。如果该路径下面找不到 spider 那么下面的示例将不会显示最后一样 spider list 的相关信息。

```bash
PS C:\Users\Administrator\Desktop\baidu> vscrapy crawl
[options]
  type<param>
  spider         ::spider_name
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (no password)
  -db,--db       ::redis db.       default: 0
[eg.]
use spider eg. "vscrapy crawl myspider".
Used to locate scripts that need to be sent.
spiders list ['baidukey']
```

- 提交任务时很简单，只需要你在一个普通的 scrapy 项目里面像是执行 `scrapy crawl myspider` 一样去执行任务即可。因为该项目寻找 spider 脚本以及通过 spider_name 定位 spider 的方式是一样的。你只需要将 scrapy 改成 vscrapy 即可。

```bash
PS C:\Users\Administrator\Desktop\baidu> vscrapy crawl baidukey
send task:
{
    "taskid": 7,
    "name": "baidukey"
}
```

#### 4 检查任务执行的状态

- 检查任务的功能都在命令行的 stat 功能中。通过 `vscrapy stat` 可以简单查看所有支持的命令。

```bash
PS C:\Users\Administrator\Desktop\baidu> vscrapy stat
[options]
  type<param>
  -ho,--host     ::redis host.     default: localhost
  -po,--port     ::redis port.     default: 6379
  -pa,--password ::redis password. default: None (no password)
  -db,--db       ::redis db.       default: 0
  -li,--limit    ::limit show num. default: 5
  -ta,--taskid   ::use taskid check taskinfo.
  type<toggle>
  -la,--latest   ::check latest
  -ls,--list     ::check latest N. default number setby -li/limit(5)
[eg.]
use -ta/--taskid tid(int) eg.   "vscrapy stat -ta 7"
use -la/--latest          eg.   "vscrapy stat -la"
use -ls/--list            eg.1/ "vscrapy stat -ls"
                          eg.2/ "vscrapy stat -ls -li 10"
[tips.]
You need to choose one of the three ways to use stat cmdline.
```

- 你可以通过配置 taskid 的方式去查询你的任务执行状态。`vscrapy stat -ta 7` 也可以用 `vscrapy stat -la` 查看最新一条任务执行的状态，也可以用 `vscrapy stat -ls -li 10` 查看最新十条任务的状态。其中显示的内容基本和 scrapy 的统计信息内容是一样。不同的任务都有各自不同的任务统计日志存放空间。

```bash
PS C:\Users\Administrator\Desktop\baidu> vscrapy stat -la

[Taskid: 5]
{'__start_time': '2019-05-17 18:46:01.448365',
 '_finish_time': '2019-05-17 18:46:41.444817',
 'downloader/request_bytes': 292382,
 'downloader/request_count': 500,
 'downloader/request_method_count/GET': 500,
 'downloader/response_bytes': 43052657,
 'downloader/response_count': 500,
 'downloader/response_status_count/200': 500,
 'item_scraped_count': 3275,
 'response_received_count': 500,
 'scheduler/dequeued/redis': 500,
 'scheduler/enqueued/redis': 500}
```

#### 4 数据的动态存储方式

- 目前增加了 mysql 的动态存储的方式，简单的来说就是在上传的 spider 的脚本中，处理item的这里，只要返回的数据字段里面增加 __mysql__ 这样一个字段进行对需要存储的数据库进行配置即可。并且连接数据库的方式使用了 twisted 框架的数据库连接处理，所以效率上也能满足需求。下面是一个非常简单的样例，是一个提交的脚本。

示例1

```python
# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request, Selector
from lxml import etree

import re
import json
from urllib.parse import quote,unquote

class VSpider(scrapy.Spider):
    name = 'v'
    def start_requests(self):
        headers = {"user-agent": "Chrome/68.0.3440.75 Safari/537.36"}
        url = 'https://www.baidu.com/s?ie=UTF-8&wd=123'
        r = Request( url, headers=headers, callback=self.parse )
        yield r

    def parse(self, response):
        for x in response.xpath('//div/h3[@class="t"]/parent::*'):
            d = {}
            d["href"]   = x.xpath('./h3/a[1][@target]/@href').extract()[0]
            d["string"] = re.sub(r'\s+',' ',x.xpath('string(.)').extract()[0])

            # 只需要你在输出数据的字段中增加连接数据库的配置，那么框架就会非常容易地将数据存储到对应数据库中
            # 之所以这么开发是考虑到不同地数据有可能在一次任务中存储到不同的数据库或数据库表中
            # 当你需要在一次任务中存储 “不同的表格” 或 “不同的数据库” 的数据的时候你只需要在 __mysql__ 增加 table 或 db 的配置即可。
            # 这里的数据库开发使用了，twisted 数据库连接的 api ，并且连接池常驻内存的配置方式使用了 hashkey 处理，
            # 也就是说，相同的 __mysql__ 连接配置都会共用一个连接池进行数据的存储工作，
            # eg.
            __mysql__ = {
                'host' : '127.0.0.1',
                'port' : 3306,
                'user' : 'root',
                'password' : 'vilame',
            }
            d.update({'__mysql__': __mysql__})
            yield d
```

示例2

```python
# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request, Selector
from lxml import etree

import re
import json
from urllib.parse import quote,unquote

class VSpider(scrapy.Spider):
    name = 'v'

    # 配置只要在该脚本里面拿得到，甚至放在类的外面的全局空间都可以。
    mysql = {'__mysql__': { 'host' : '127.0.0.1', 'port' : 3306, 'user' : 'root', 'password' : 'vilame', }}

    def start_requests(self):
        headers = {"user-agent": "Chrome/68.0.3440.75 Safari/537.36"}
        url = 'https://www.baidu.com/s?ie=UTF-8&wd=123'
        r = Request( url, headers=headers, callback=self.parse )
        yield r

    def parse(self, response):
        for x in response.xpath('//div/h3[@class="t"]/parent::*'):
            d = {}
            d["href"]   = x.xpath('./h3/a[1][@target]/@href').extract()[0]
            d["string"] = re.sub(r'\s+',' ',x.xpath('string(.)').extract()[0])

            # 参数的详细说明
            # __mysql__ = {
            #     'host':'127.0.0.1'  # 该字段是必须的
            #     'port':3306         # 该字段是必须的
            #     'user':'user'       # 该字段是必须的
            #     'passwd':'mypass'   # 该字段是必须的，不过由于不同的库函数的关键字不同
            #                         # 这里可以根据部署时使用连接数据库方式的关键字
            #                         # 所以也可以是 password
            #     'dbapi':'pymysql'   # 【可选】 使用的连接数据库的方式，如果有多个可以使用，可以通过该处配置
            #                         # 通常数据库会默认使用一个可以连接的方式，按照 ['pymysql','MySQLdb','mysql.connector'] 的顺序
            #                         # 自动选择一个可用链接库作为默认连接方式，而且在该框架服务端启动的时候都会显示哪些可以使用
            #                         # 由于 adbapi.ConnectionPool 这个函数的参数命名关系，这里也可以设置为 'dbapiName'，
            #                         # 不过在配置时请不要将 'dbapi' 与 'dbapiName' 重复配置。
            #     'db':'mydb'         # 【可选】 存储的数据库名 {{{ 默认使用的数据库为 vscrapy }}}，如果不存在则会创建数据库。
            #     'table':'mytable'   # 【可选】 存储的表格名，如不填，将会以任务id和vscrapy拼接的方式存储
            #                         # eg. vscrapy_7 [第七个任务的存储数据表名]
            #                         # 数据库和数据库表如果不存在都会自动创建，并且一旦创建就不能修改字段名字
            #                         # 新增的数据也不能传入数据表中。
            #                         # 如果自定义表时需要使用 taskid，那么就在table字符串中增加'{taskid}'
            #                         # eg. 'mytable_{taskid}' 这样表名会自动添加任务id
            # }
            
            d.update(self.mysql)
            yield d
```


#### 补充

- 目前该工具 README 的版本尚在 vscrapy 的 1.0.1 版本。里面的功能暂时还没有考虑更好的处理收集数据的方式。目前收集的数据都放在 redis 当中以 taskid 进行分管道存储，可以在 gqueue 管道下的 items 处看到。不过将数据持久放入 redis 是一个非常不好的选择，后续会再考虑更好的存储数据的方式。或许通过 redis 作为一个数据存储的中转站也未尝不可。

- 目前已经到了 1.0.4 版本。增加了对 mysql 存储的支持，并且该功能能适应单任务同时存储多张表格。
