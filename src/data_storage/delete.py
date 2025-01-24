# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25 13:39
@Auth: Zhang Hongxing
@File: delete.py
@Note:   
"""
from Mysql.db_config import DB_PARAMS
from Mysql.delete_data import DataDeleterWithDatabase
from Redis.delete_key import DataDeleterWithCache


class DataDeleter:
    def __init__(self, db_params):
        self.cache_deleter = DataDeleterWithCache()
        self.db_deleter = DataDeleterWithDatabase(db_params)

    def delete_data(self, year, month, category=None, keyword=None, algorithm=None, keywords_num=None):
        try:
            # 删除数据库中的数据
            if self.db_deleter.mark_news_as_deleted(year, month, category, keyword):
                print(f"数据库中新闻数据删除成功。")
            if self.db_deleter.mark_keywords_as_deleted(year, month, algorithm, keywords_num):
                print(f"数据库中关键词数据删除成功。")
            if self.db_deleter.mark_cloud_as_deleted(year, month, category, keywords_num, algorithm):
                print(f"数据库中词云数据删除成功。")
            if self.db_deleter.mark_summary_as_deleted(year, month, category, keywords_num, keyword, algorithm):
                print(f"数据库中摘要数据删除成功。")
            # 删除缓存中的数据
            self.cache_deleter.delete_news_from_cache(year, month, category, keyword)
            self.cache_deleter.delete_keywords_from_cache(year, month, algorithm, keywords_num)
            self.cache_deleter.delete_cloud_from_cache(year, month, category, keywords_num, algorithm)
            self.cache_deleter.delete_summary_from_cache(year, month, category, keywords_num, keyword, algorithm)
            print(f"数据一致性删除完成。")
        except Exception as e:
            print(f"数据一致性删除时发生错误: {e}")

if __name__ == "__main__":
    deleter = DataDeleter(DB_PARAMS)
    year = 2024
    month = 10
    category = "时政"
    keyword = "发展"
    algorithm = "jieba提供的TF-IDF"
    keywords_num = 50
    deleter.delete_data(year, month, category, keyword, algorithm, keywords_num)