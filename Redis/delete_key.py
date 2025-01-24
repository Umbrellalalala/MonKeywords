# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25 11:10
@Auth: Zhang Hongxing
@File: delete_key.py
@Note: 封装删除操作为类，确保数据库和缓存一致性，支持 Redis 集群
"""
from Redis.redis_config import get_redis_cluster_client
redis_client = get_redis_cluster_client()

class DataDeleterWithCache:
    def __init__(self):
        self.redis_client = redis_client # Redis 客户端实例

    def _get_news_cache_keys(self, year, month, category=None, keyword=None):
        keys = []
        if category and keyword:
            keys.append(f"news:{year}:{month}:{keyword}:{category}")
        elif category:
            keys.append(f"news:{year}:{month}:{category}")
        elif keyword:
            keys.append(f"news:{year}:{month}:{keyword}")
        else:
            keys.append(f"news:{year}:{month}")
        return keys

    def _get_keywords_cache_key(self, year, month, algorithm, keywords_num):
        return f"keywords:{year}:{month}:{algorithm}:{keywords_num}"

    def _get_cloud_cache_key(self, year, month, category, keywords_num, algorithm):
        return f"wordcloud:{year}:{month}:{category}:{keywords_num}:{algorithm}"

    def _get_summary_cache_key(self, year, month, category, keywords_num, keyword, algorithm):
        return f"summary:{year}:{month}:{category}:{keywords_num}:{keyword}:{algorithm}"

    def delete_news_from_cache(self, year, month, category=None, keyword=None):
        cache_keys = self._get_news_cache_keys(year, month, category, keyword)
        for key in cache_keys:
            result = self.redis_client.delete(key)
            if result:
                print(f"{key} 的新闻缓存已删除。")
            else:
                print(f"{key} 的新闻缓存不存在或已被删除。")

    def delete_keywords_from_cache(self, year, month, algorithm, keywords_num):
        cache_key = self._get_keywords_cache_key(year, month, algorithm, keywords_num)
        result = self.redis_client.delete(cache_key)
        if result:
            print(f"{cache_key} 的关键词缓存已删除。")
        else:
            print(f"{cache_key} 的关键词缓存不存在或已被删除。")

    def delete_cloud_from_cache(self, year, month, category, keywords_num, algorithm):
        cache_key = self._get_cloud_cache_key(year, month, category, keywords_num, algorithm)
        result = self.redis_client.delete(cache_key)
        if result:
            print(f"ID为 {cache_key} 的词云图缓存已删除。")
        else:
            print(f"ID为 {cache_key} 的词云图缓存不存在或已被删除。")

    def delete_summary_from_cache(self, year, month, category, keywords_num, keyword, algorithm):
        cache_key = self._get_summary_cache_key(year, month, category, keywords_num, keyword, algorithm)
        result = self.redis_client.delete(cache_key)
        if result:
            print(f"ID为 {cache_key} 的摘要缓存已删除。")
        else:
            print(f"ID为 {cache_key} 的摘要缓存不存在或已被删除。")

if __name__ == "__main__":
    cache_deleter = DataDeleterWithCache()
    year = 2024
    month = 10
    category = "时政"
    keyword = "发展"
    cache_deleter.delete_news_from_cache(year, month, None, keyword)
    keyword = "北京"
    cache_deleter.delete_news_from_cache(year, month, category, keyword)
    algorithm = "jieba提供的TF-IDF"
    keywords_num = 50
    cache_deleter.delete_keywords_from_cache(year, month, algorithm, keywords_num)
    cache_deleter.delete_cloud_from_cache(year, month, category, keywords_num, algorithm)
    keyword = "发展"
    cache_deleter.delete_summary_from_cache(year, month, category, keywords_num, keyword, algorithm)
