# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 17:48
@Auth: Zhang Hongxing
@File: pipelines.py
@Note:   
"""
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src.data_storage.models import News


class NewsPipeline:
    def __init__(self, db_params):
        self.db_params = db_params
        self.db = None

    # 获取数据库参数，创建数据库连接
    @classmethod
    def from_crawler(cls, crawler):
        db_params = crawler.settings.getdict("DB_PARAMS")
        return cls(db_params)

    def open_spider(self, spider):
        self.db = scoped_session(sessionmaker(bind=create_engine(
            f"mysql+pymysql://{self.db_params['user']}:{self.db_params['password']}@{self.db_params['host']}:{self.db_params['port']}/{self.db_params['database']}")))

    def close_spider(self, spider):
        self.db.close()

    def process_item(self, item, spider):
        news = News(
            url=item['url'],
            category=item['category'],
            title=item['title'],
            pub_time=item['pub_time'],
            body=item['body']
        )
        self.db.add(news)
        self.db.commit()
        return item


class ScrapyProjectPipeline:
    def process_item(self, item, spider):
        return item
