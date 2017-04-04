#!/usr/bin/env python

import scrapy
import logging
from scrapy.crawler import CrawlerProcess

class AstikoSpider(scrapy.Spider):
    name = "astiko"
    start_urls = [
        "http://chaniabus.gr"
    ]

    def start_requests(self):
        yield scrapy.Request('http://localhost:8050/render.html?url=%s&timeout=30&wait=2' % self.start_urls[0], self.parse)

    def parse(self, response):
        print "Received response from %s" % response.url
        print response.css('select.form-control')[0].css('option::text').extract()


process = CrawlerProcess({'USER_AGENT':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'})
process.crawl(AstikoSpider())
process.start()
