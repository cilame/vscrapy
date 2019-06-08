# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request, Selector
from lxml import etree

import re
import json
from urllib.parse import quote,unquote

class VSpider(scrapy.Spider):
    name = 'v'

    custom_settings = {
        'COOKIES_ENABLED': False,  # use my create cookie in headers
    }

    def start_requests(self):
        def mk_url_headers(num):
            def quote_val(url):
                url = unquote(url)
                for i in re.findall('=([^=&]+)',url):
                    url = url.replace(i,'{}'.format(quote(i)))
                return url
            url = (
                'https://www.baidu.com/s'
                '?ie=UTF-8'
                '&wd=123'
                '&pn={}'
            ).format(num)
            url = quote_val(url)
            headers = {
                "accept-encoding": "gzip, deflate", # auto delete br encoding. cos requests and scrapy can not decode it.
                "accept-language": "zh-CN,zh;q=0.9",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36"
            }
            return url,headers

        for i in range(3):
            url,headers = mk_url_headers(i*10)
            meta = {}
            r = Request(
                    url,
                    headers  = headers,
                    callback = self.parse,
                    meta     = meta,
                )
            yield r

    def parse(self, response):
        # If you need to parse another string in the parsing function.
        # use "etree.HTML(text)" or "Selector(text=text)" to parse it.

        class none:pass
        none.extract = lambda:None
        for x in response.xpath('//div/h3[@class="t"]/parent::*'):
            d = {}
            d["href"]       = (x.xpath('./h3/a[1][@target]/@href') or [none])[0].extract()             # [cnt:9] [len:73] http://www.baidu.com/link?url=...
            d["str_c"]      = x.xpath('string(./div[@class="c-abstract"])')[0].extract()               # [cnt:9] [len:84] 南方123是领先的互联网服务提供商,10年虚拟主机老品牌、提...
            d["str_f13"]    = x.xpath('string(./div[@class="f13"])')[0].extract()                      # [cnt:9] [len:26] www.nf123.com/ - 百度快照 - 评价
            if "str_all"    in d: d["str_all"   ] = re.sub(r'\s+',' ',d["str_all"])
            if "str_t"      in d: d["str_t"     ] = re.sub(r'\s+',' ',d["str_t"])
            if "str_None"   in d: d["str_None"  ] = re.sub(r'\s+',' ',d["str_None"])
            if "str_c"      in d: d["str_c"     ] = re.sub(r'\s+',' ',d["str_c"])
            if "str_f13"    in d: d["str_f13"   ] = re.sub(r'\s+',' ',d["str_f13"])
            if "str_c_1"    in d: d["str_c_1"   ] = re.sub(r'\s+',' ',d["str_c_1"])
            if "str_None_1" in d: d["str_None_1"] = re.sub(r'\s+',' ',d["str_None_1"])
            if "str_None_2" in d: d["str_None_2"] = re.sub(r'\s+',' ',d["str_None_2"])


            __mysql__ = {
                'host' : "47.99.126.229",
                'port' : 3306,
                'user': 'root',
                'password' : 'vilame',
            }
            d.update({'__mysql__': __mysql__})
            yield d


class QSpider(scrapy.Spider):
    name = 'vaa'

    custom_settings = {
        'COOKIES_ENABLED': False,  # use my create cookie in headers
    }

    def start_requests(self):
        def mk_url_headers(num):
            def quote_val(url):
                url = unquote(url)
                for i in re.findall('=([^=&]+)',url):
                    url = url.replace(i,'{}'.format(quote(i)))
                return url
            url = (
                'https://www.baidu.com/s'
                '?ie=UTF-8'
                '&wd=123'
                '&pn={}'
            ).format(num)
            url = quote_val(url)
            headers = {
                "accept-encoding": "gzip, deflate", # auto delete br encoding. cos requests and scrapy can not decode it.
                "accept-language": "zh-CN,zh;q=0.9",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36"
            }
            return url,headers

        for i in range(3):
            url,headers = mk_url_headers(i*10)
            meta = {}
            r = Request(
                    url,
                    headers  = headers,
                    callback = self.parse,
                    meta     = meta,
                )
            yield r

    def parse(self, response):
        # If you need to parse another string in the parsing function.
        # use "etree.HTML(text)" or "Selector(text=text)" to parse it.

        class none:pass
        none.extract = lambda:None
        for x in response.xpath('//div/h3[@class="t"]/parent::*'):
            d = {}
            d["href"]       = (x.xpath('./h3/a[1][@target]/@href') or [none])[0].extract()             # [cnt:9] [len:73] http://www.baidu.com/link?url=...
            d["str_c"]      = x.xpath('string(./div[@class="c-abstract"])')[0].extract()               # [cnt:9] [len:84] 南方123是领先的互联网服务提供商,10年虚拟主机老品牌、提...
            d["str_f13"]    = x.xpath('string(./div[@class="f13"])')[0].extract()                      # [cnt:9] [len:26] www.nf123.com/ - 百度快照 - 评价
            if "str_all"    in d: d["str_all"   ] = re.sub(r'\s+',' ',d["str_all"])
            if "str_t"      in d: d["str_t"     ] = re.sub(r'\s+',' ',d["str_t"])
            if "str_None"   in d: d["str_None"  ] = re.sub(r'\s+',' ',d["str_None"])
            if "str_c"      in d: d["str_c"     ] = re.sub(r'\s+',' ',d["str_c"])
            if "str_f13"    in d: d["str_f13"   ] = re.sub(r'\s+',' ',d["str_f13"])
            if "str_c_1"    in d: d["str_c_1"   ] = re.sub(r'\s+',' ',d["str_c_1"])
            if "str_None_1" in d: d["str_None_1"] = re.sub(r'\s+',' ',d["str_None_1"])
            if "str_None_2" in d: d["str_None_2"] = re.sub(r'\s+',' ',d["str_None_2"])


            __mysql__ = {
                'host' : "47.99.126.229",
                'port' : 3306,
                'user': 'root',
                'password' : 'vilame',
            }
            d.update({'__mysql__': __mysql__})
            yield d