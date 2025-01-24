# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25 15:30
@Auth: Zhang Hongxing
@File: bloom_filter_news_time_range.py
@Note: 根据时间范围加载新闻表数据并添加到布隆过滤器
"""
from bitarray import bitarray
import mmh3
from datetime import datetime
from src.data_storage.database import Database
from Mysql.db_config import DB_PARAMS
from src.data_storage.models import Keywords, News


class BloomFilter:
    def __init__(self, size, hash_count):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)
        self.db = Database(DB_PARAMS)
        self.load_data_from_db()

    def add(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(item, i) % self.size
            self.bit_array[index] = 1

    def check(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(item, i) % self.size
            if self.bit_array[index] == 0:
                return False
        return True

    def load_data_from_db(self):
        with self.db.get_session() as session:
            # 获取最早和最晚的新闻时间
            min_date = session.query(News.pub_time).order_by(News.pub_time.asc()).first()[0]
            max_date = session.query(News.pub_time).order_by(News.pub_time.desc()).first()[0]
            print(f"最早新闻时间: {min_date}, 最晚新闻时间: {max_date}")

            # 加载从最早到最晚时间范围的数据
            self.load_news_keys(start_date=min_date, end_date=max_date)

    def load_news_keys(self, start_date, end_date):
        print(f"开始加载新闻表中的键（时间范围: {start_date} - {end_date}）到布隆过滤器...")
        with self.db.get_session() as session:
            news_data = (
                session.query(News.pub_time, Keywords.keywords)
                .join(Keywords, News.id == Keywords.news_id)
                .filter(
                    News.is_delete == 0,
                    News.pub_time >= start_date,
                    News.pub_time <= end_date
                )
                .all()
            )
            for pub_time, keywords in news_data:
                if pub_time and keywords:
                    year = pub_time.year
                    month = pub_time.month
                    keyword_pairs = keywords.split(',')
                    for pair in keyword_pairs:
                        keyword, _ = pair.split(':', 1)
                        key = f"news:{year}:{month:02d}:{keyword.strip()}"
                        self.add(key)

            print(f"成功将 {len(news_data)} 条新闻的键加载到布隆过滤器中。")


if __name__ == "__main__":
    # 数据库对象
    db = Database(DB_PARAMS)

    # 布隆过滤器配置
    bloom_filter_size = 1000000  # 位数组大小
    hash_count = 5  # 哈希函数数量

    # 初始化布隆过滤器，自动加载数据
    bloom_filter = BloomFilter(size=bloom_filter_size, hash_count=hash_count, db=db)

    # 测试布隆过滤器
    test_key = "news:2024:12:知识讲座"
    if bloom_filter.check(test_key):
        print(f"Key '{test_key}' 可能存在。")
    else:
        print(f"Key '{test_key}' 不存在。")
