# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 17:48
@Auth: Zhang Hongxing
@File: items.py
@Note:   
"""
import scrapy


class NewsItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    category = scrapy.Field()
    title = scrapy.Field()
    pub_time = scrapy.Field()
    body = scrapy.Field()
    pass
