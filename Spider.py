#!/usr/bin/env python
# coding=utf-8


import scrapy
import logging
from scrapy.crawler import CrawlerProcess

splash_url = 'http://localhost:8050/render.html?url=%s&timeout=30&wait=2'

class AstikoSpider(scrapy.Spider):
    name = "astiko"
    start_urls = {
        "http://chaniabus.gr" : "form-control",
        "http://oasth.gr/" : "busNumSelectForRoutesWidget",
        # "http://astiko-ioannina.gr/": "busNumSelectForRoutesWidget",
        "http://astiko-irakleiou.gr/" : "form-control"
    }

    def start_requests(self):
        for url, css_class in self.start_urls.iteritems():
            request = scrapy.Request(splash_url % url, self.parse)
            request.meta['css_class'] = css_class
            yield request

    def parse(self, response):
        print "\n\nReceived response from %s" % response.url
        print "Looking for select element with class: %s" % response.meta['css_class']

        # Bus line info
        bus_line_select = response.css('select.%s' % response.meta['css_class'])[0].css('option::text').extract()

        print "\n## Πληροφορίες διαθέσιμες για τις γραμμές"
        for option in bus_line_select[1:]:
            print option.encode('utf-8').strip()

        # Bus stop info
        bus_stop_select = response.css('select.%s' % response.meta['css_class'])[1].css('option::text').extract()
        print "\n## Πληροφορίες διαθέσιμες για τις στάσεις"
        for option in bus_stop_select[1:]:
            print option.encode('utf-8').strip()

process = CrawlerProcess({'USER_AGENT':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'})
process.crawl(AstikoSpider())
process.start()
