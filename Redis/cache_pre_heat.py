# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25 16:33
@Auth: Zhang Hongxing
@File: cache_pre_heat.py
@Note:   
"""
import json
import random
import threading
import schedule
import time
from datetime import datetime
from sqlalchemy.orm import joinedload

from Mysql.db_config import DB_PARAMS
from Redis.redis_config import get_redis_cluster_client
from src.data_storage.database import Database
from src.data_storage.models import News, Keywords


class CachePreheat:
    def __init__(self, db_params, refresh_time):
        self.db = Database(db_params)
        self.redis_client = get_redis_cluster_client()
        self.refresh_time = refresh_time

    def _reload_and_cache_data_for_keyword(self, keyword, cache_key):
        try:
            print(f"开始查询关键词 {keyword} 对应的新闻数据")
            with self.db.get_session() as session:
                query = (
                    session.query(News)
                    .join(Keywords, News.id == Keywords.news_id)
                    .filter(Keywords.keywords.like(f"%{keyword}%"))
                    .options(joinedload(News.keywords))
                )
                related_news = query.all()
                if not related_news:
                    print(f"未找到关键词 {keyword} 的相关新闻")
                    result = {"error": "未找到相关新闻"}
                    self.redis_client.setex(cache_key, 60, json.dumps(result))
                    return
                print(f"为关键词 {keyword} 找到 {len(related_news)} 条相关新闻")
                news_results = [
                    {
                        "id": news.id,
                        "title": news.title,
                        "summary": self._get_summary(news.body),
                        "url": news.url,
                        "pub_time": str(news.pub_time),
                        "category": news.category,
                        "keywords": news.keywords[0].keywords if news.keywords else "",
                    }
                    for news in related_news
                ]
                result = {
                    "news_results": news_results,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_delete": 0
                }
                random_time = random.randint(0, 3600)
                self.redis_client.setex(cache_key, 2592000 + random_time, json.dumps(result))
                print(f"缓存更新成功，关键词 {keyword} 的新闻数据已缓存 1个月+{random_time}秒")
        except Exception as e:
            print(f"Error during database connection or query for keyword {keyword}: {e}")

    def refresh_cache_for_keyword(self, keyword):
        cache_key = f"news:{keyword}"
        print(f"检查缓存：{cache_key}")
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            random_time = random.randint(0, 3600)
            self.redis_client.expire(cache_key, 2592000 + random_time)
            print(f"缓存命中，关键词 {keyword} 的新闻数据延长缓存时间为 1个月+{random_time}秒")
        else:
            print(f"缓存未命中，开始从数据库加载数据")
            self._reload_and_cache_data_for_keyword(keyword, cache_key)

    def refresh_hot_keywords_cache(self):
        print("开始刷新热点关键词缓存")
        hot_keywords = self.get_top_keyword(10)
        for keyword_data in hot_keywords:
            keyword = keyword_data["keyword"]
            threading.Thread(target=self.refresh_cache_for_keyword, args=(keyword,)).start()

    def get_top_keyword(self, n):
        print(f"获取前 {n} 个热点关键词")
        top_keyword = self.redis_client.zrevrange("keyword_click_rank", 0, n - 1, withscores=True)
        return [{"keyword": keyword[0], "clicks": keyword[1]} for keyword in top_keyword]

    def start_scheduler(self):
        print(f"启动定时任务，每{self.refresh_time}分钟刷新一次热点关键词缓存")
        schedule.every(self.refresh_time).minutes.do(self.refresh_hot_keywords_cache)
        threading.Thread(target=self.run_scheduler).start()

    def run_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def _get_summary(self, body):
        return body[:150] + '...' if len(body) > 150 else body


if __name__ == "__main__":
    print("启动缓存预热系统")
    cache_preheat = CachePreheat(DB_PARAMS, refresh_time=0.1)
    cache_preheat.start_scheduler()
