# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request, Selector
from lxml import etree

import re
import json
from urllib.parse import quote,unquote

class VSpider(scrapy.Spider):
    name = 'test'

    custom_settings = {
        'COOKIES_ENABLED': False,  # use my create cookie in headers
    }

    def start_requests(self):
        import scrapy
        from scrapy import Request, Selector
        from lxml import etree

        import re
        import json
        from urllib.parse import quote,unquote
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
                callback = self.parse,
                meta     = meta,
            )
        yield r

    def parse(self, response):
        # If you need to parse another string in the parsing function.
        # use "etree.HTML(text)" or "Selector(text=text)" to parse it.

        print('============================== start ==============================')
        print('status:',response.status)
        print('decode type: utf-8')
        print('response length: {}'.format(len(response.body)))
        print('response content[:1000]:\n {}'.format(response.body[:1000]))
        print('==============================  end  ==============================')