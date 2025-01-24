# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 21:55
@Auth: Zhang Hongxing
@File: crawl_service.py
@Note:   
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import desc
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ..data_storage.models import News
from scrapy_project.spiders.news_spider import NewsSpider


class CrawlService:
    def __init__(self, db):
        self.db = db

    def get_existing_times(self):
        try:
            with self.db.get_session() as session:
                existing_times = session.query(News.pub_time).distinct().all()
                unique_times = set(time.strftime("%Y-%m") for time, in existing_times)
                return sorted(list(unique_times), reverse=True)
        except Exception as e:
            print(f"Error during database connection: {e}")
            return []

    def get_last_record_pub_time(self):
        default_pub_time = datetime.now() - relativedelta(months=1)
        default_pub_time = default_pub_time.replace(year=2021, month=1, day=1)
        try:
            with self.db.get_session() as session:
                last_record = session.query(News).order_by(desc(News.pub_time)).first()
                print(f"最新的一条新闻时间为: {last_record.pub_time}")
                return last_record.pub_time if last_record else default_pub_time
        except Exception as e:
            print(f"Error during database connection: {e}")
            return default_pub_time

    def start_crawler(self, new_start_time, new_end_time):
        try:
            process = CrawlerProcess(get_project_settings())
            spider_args = {'new_start_time': new_start_time, 'new_end_time': new_end_time}
            process.crawl(NewsSpider, **spider_args)
            process.start()
        except Exception as e:
            print(f"Exception in start_crawler: {e}")
            raise
        finally:
            self.db.dispose_connection()

