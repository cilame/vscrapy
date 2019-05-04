from v.scrapy_redis_mod.spiders import RedisSpider

import re
import json
from urllib.parse import (
    unquote,
    quote,
    urlencode,
)

from scrapy import Request

class MySpider(RedisSpider):
    """Spider that reads urls from redis queue (myspider:start_urls)."""
    name = 'v'
    redis_key = 'myspider:start_urls'

    # def start_requests(self):
    #     for i in self.next_requests():
    #         yield i

    def parse(self, response):
        def mk_url_headers():
            def quote_val(url):
                url = unquote(url)
                for i in re.findall('=([^=&]+)',url):
                    url = url.replace(i,'{}'.format(quote(i)))
                return url
            url = (
                'https://www.baidu.com/s'
                '?ie=UTF-8'
                '&wd=百度'
            )
            url = quote_val(url)
            headers = {
                "accept-encoding": "gzip, deflate", # auto delete br encoding. cos requests and scrapy can not decode it.
                "accept-language": "zh-CN,zh;q=0.9",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36"
            }
            return url,headers
        url,headers = mk_url_headers()
        meta = {}
        r = Request(
                url,
                headers  = headers,
                callback = self.parse1,
                meta     = meta,
            )
        yield r


    def parse1(self, response):
        # If you need to parse another string in the parsing function.
        # use "etree.HTML(text)" or "Selector(text=text)" to parse it.

        class none:pass
        none.extract = lambda:None
        for x in response.xpath('//div/h3[@class="t"]/parent::*'):
            d = {}
            d["href_8"]      = (x.xpath('./h3/a[1][@target]/@href') or [none])[0].extract()                           # [cnt:8] [len:73] http://www.baidu.com/link?url=...
            d["str_all"]     = x.xpath('string(.)')[0].extract()                                                      # [cnt:9] [len:125] 百度网址大全百度网址大全 -- 简单可依赖的上网导航... ...
            d["str_t"]       = x.xpath('string(./h3[@class="t"])')[0].extract()                                       # [cnt:9] [len:6] 百度网址大全
            if "str_all"     in d: d["str_all"    ] = re.sub(r'\s+',' ',d["str_all"])
            if "str_t"       in d: d["str_t"      ] = re.sub(r'\s+',' ',d["str_t"])
            if "str_c"       in d: d["str_c"      ] = re.sub(r'\s+',' ',d["str_c"])
            if "str_c_1"     in d: d["str_c_1"    ] = re.sub(r'\s+',' ',d["str_c_1"])
            if "str_f13"     in d: d["str_f13"    ] = re.sub(r'\s+',' ',d["str_f13"])
            if "str_c_2"     in d: d["str_c_2"    ] = re.sub(r'\s+',' ',d["str_c_2"])
            if "str_None"    in d: d["str_None"   ] = re.sub(r'\s+',' ',d["str_None"])
            if "str_None_15" in d: d["str_None_15"] = re.sub(r'\s+',' ',d["str_None_15"])
            if "str_c_10"    in d: d["str_c_10"   ] = re.sub(r'\s+',' ',d["str_c_10"])
            if "str_f13_1"   in d: d["str_f13_1"  ] = re.sub(r'\s+',' ',d["str_f13_1"])
            if "str_c_11"    in d: d["str_c_11"   ] = re.sub(r'\s+',' ',d["str_c_11"])
            yield d