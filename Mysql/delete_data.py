# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25 11:10
@Auth: Zhang Hongxing
@File: delete_data.py
@Note:
"""
from datetime import datetime

from Mysql.db_config import DB_PARAMS
from Redis.redis_config import get_redis_cluster_client
from src.data_storage.database import Database
from src.data_storage.models import Summary, Cloud, Keywords, News

# 创建 Redis 集群客户端连接
redis_client = get_redis_cluster_client()


class DataDeleterWithDatabase:
    def __init__(self, db_params):
        self.db = Database(db_params)
        self.session = self.db.get_session()
        self.redis_client = redis_client

    def _get_news_key_parts(self, cache_key):
        parts = cache_key.split(":")
        if len(parts) == 4:
            # 解析到 "news:year:month:category"
            return parts[1], parts[2], parts[3], None
        elif len(parts) == 5:
            # 解析到 "news:year:month:keyword:category"
            return parts[1], parts[2], parts[4], parts[3]
        elif len(parts) == 3:
            # 解析到 "news:year:month"
            return parts[1], parts[2], None, None
        return None

    def _get_keywords_key_parts(self, cache_key):
        parts = cache_key.split(":")
        if len(parts) == 5:
            # 解析到 "keywords:year:month:algorithm:keywords_num"
            return parts[1], parts[2], parts[3], parts[4]
        return None

    def _get_cloud_key_parts(self, cache_key):
        parts = cache_key.split(":")
        if len(parts) == 6:
            # 解析到 "wordcloud:year:month:category:keywords_num:algorithm"
            return parts[1], parts[2], parts[3], parts[4], parts[5]
        return None

    def _get_summary_key_parts(self, cache_key):
        parts = cache_key.split(":")
        if len(parts) == 7:
            # 解析到 "summary:year:month:category:keywords_num:keyword:algorithm"
            return parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
        return None

    def mark_news_as_deleted(self, year, month, category=None, keyword=None):
        try:
            from calendar import monthrange
            last_day = monthrange(year, month)[1]
            pub_time_start = f"{year}-{month}-01 00:00:00"
            pub_time_end = f"{year}-{month}-{last_day} 23:59:59"
            pub_time_start = datetime.strptime(pub_time_start, "%Y-%m-%d %H:%M:%S")
            pub_time_end = datetime.strptime(pub_time_end, "%Y-%m-%d %H:%M:%S")
            # 查询数据库中符合条件的新闻数据
            query = self.session.query(News).filter(News.pub_time >= pub_time_start, News.pub_time <= pub_time_end,
                                                    News.is_delete == 0)
            if category:
                query = query.filter(News.category == category)
            if keyword:
                keyword_query = self.session.query(Keywords).filter(Keywords.keywords.contains(keyword))
                news_ids_with_keyword = [kw.news_id for kw in keyword_query.all()]
                if news_ids_with_keyword:
                    query = query.filter(News.id.in_(news_ids_with_keyword))
                else:
                    print(f"没有找到包含关键词 '{keyword}' 的新闻数据。")
                    return False
            news_list = query.all()
            if news_list:
                for news in news_list:
                    news.is_delete = 1
                self.session.commit()
                print(f"共标记了 {len(news_list)} 条新闻数据为删除。")
                return True
            else:
                print(f"数据库中未找到符合条件的新闻数据。")
                return False
        except Exception as e:
            print(f"标记新闻数据为删除时发生错误: {e}")
            self.session.rollback()
            return False

    def mark_keywords_as_deleted(self, year, month, algorithm, keywords_num):
        try:
            from calendar import monthrange
            last_day = monthrange(year, month)[1]
            pub_time_start = f"{year}-{month}-01 00:00:00"
            pub_time_end = f"{year}-{month}-{last_day} 23:59:59"
            pub_time_start = datetime.strptime(pub_time_start, "%Y-%m-%d %H:%M:%S")
            pub_time_end = datetime.strptime(pub_time_end, "%Y-%m-%d %H:%M:%S")
            news_query = self.session.query(News).filter(News.pub_time >= pub_time_start, News.pub_time <= pub_time_end,
                                                         News.is_delete == 0)
            if algorithm:
                news_query = news_query.filter(News.keywords.any(Keywords.algorithm == algorithm))
            if keywords_num:
                news_query = news_query.filter(News.keywords.any(Keywords.keywords_num == keywords_num))
            news_list = news_query.all()
            if news_list:
                news_ids = [news.id for news in news_list]
                keywords_query = self.session.query(Keywords).filter(Keywords.news_id.in_(news_ids),
                                                                     Keywords.is_delete == 0)
                keywords_list = keywords_query.all()
                if keywords_list:
                    for keyword in keywords_list:
                        keyword.is_delete = 1
                    self.session.commit()
                    print(f"共标记了 {len(keywords_list)} 条关键词数据为删除。")
                    return True
                else:
                    print(f"未找到符合条件的关键词数据。")
                    return False
            else:
                print(f"未找到符合条件的新闻数据。")
                return False
        except Exception as e:
            print(f"标记关键词数据为删除时发生错误: {e}")
            self.session.rollback()
            return False

    def mark_cloud_as_deleted(self, year, month, category, keywords_num, algorithm):
        try:
            cloud = self.session.query(Cloud).filter(Cloud.year == year, Cloud.month == month,
                                                     Cloud.category == category,
                                                     Cloud.keywords_num == keywords_num,
                                                     Cloud.algorithm == algorithm,
                                                     Cloud.is_delete == 0
                                                     ).first()
            if cloud:
                cloud.is_delete = 1
                self.session.commit()
                print(f"数据库中ID为 {cloud.id} 的云数据已标记为删除。")
                return True
            else:
                print(f"数据库中未找到符合条件的云数据。")
                return False
        except Exception as e:
            print(f"标记云数据为删除时发生错误: {e}")
            self.session.rollback()
            return False

    def mark_summary_as_deleted(self, year, month, category, keywords_num, keyword, algorithm):
        try:
            summary = self.session.query(Summary).filter(Summary.year == year, Summary.month == month,
                                                         Summary.category == category,
                                                         Summary.keywords_num == keywords_num,
                                                         Summary.keyword == keyword,
                                                         Summary.algorithm == algorithm,
                                                         Summary.is_delete == 0
                                                         ).first()
            if summary:
                summary.is_delete = 1
                self.session.commit()
                print(f"数据库中ID为 {summary.id} 的摘要数据已标记为删除。")
                return True
            else:
                print(f"数据库中未找到符合条件的摘要数据。")
                return False
        except Exception as e:
            print(f"标记摘要数据为删除时发生错误: {e}")
            self.session.rollback()
            return False
