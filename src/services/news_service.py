# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 21:17
@Auth: Zhang Hongxing
@File: news_service.py
@Note: Updated to support multi-table structure
"""
import json
import re
from datetime import datetime

from PyQt5.QtWidgets import QMessageBox
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import joinedload
from Redis.bloom_filter import BloomFilter
from Redis.redis_config import get_redis_cluster_client
from ..data_storage.models import News, Keywords


class NewsService:
    def __init__(self, db, bloom_filter_size=100000, hash_count=5):
        """
        初始化新闻管理器
        :param redis_client: Redis 客户端实例
        :param db: 数据库实例
        :param bloom_filter_size: 布隆过滤器大小
        :param hash_count: 哈希函数数量
        """
        self.redis_client = get_redis_cluster_client()
        self.db = db
        self.bloom_filter = BloomFilter(bloom_filter_size, hash_count)

    def get_news_list(self, selected_month, keyword):
        # keyword = "不存在的hhh"
        try:
            cache_key = f"news:{selected_month[:4]}:{selected_month[5:7]}:{keyword}"
            print(f"新闻缓存键: {cache_key}")
            # 检查布隆过滤器
            if not self.bloom_filter.check(cache_key):
                print("-----布隆过滤器未命中，直接返回-----")
                print("未找到相关新闻")
                return "未找到相关新闻", "未找到相关新闻"
            print("-----布隆过滤器命中，继续查询缓存-----")
            # 获取缓存数据
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                print("-----从缓存中获取新闻数据-----")
                cached_data = json.loads(cached_data)
                processed_news_text = cached_data["processed_news_text"]
                original_news_text = cached_data["original_news_text"]
                return processed_news_text, original_news_text
            else:
                print("-----缓存未命中，开始从数据库查询新闻-----")
                with self.db.get_session() as session:
                    start_date = datetime.strptime(selected_month, "%Y-%m")
                    end_date = start_date + relativedelta(months=1)
                    # 查询符合条件的新闻和关键词
                    related_news = (
                        session.query(News)
                        .join(Keywords, News.id == Keywords.news_id)
                        .filter(
                            News.pub_time >= start_date,
                            News.pub_time < end_date,
                            News.is_delete == 0,
                            Keywords.keywords.op('REGEXP')(fr'\b{re.escape(keyword)}\b')
                        )
                        .all()
                    )
                    if not related_news:
                        print("未找到相关新闻")
                        return "未找到相关新闻", "未找到相关新闻"
                    news_with_values = []
                    for news in related_news:
                        # 获取关键词权重
                        keyword_value_pairs = [
                            pair.strip() for pair in news.keywords[0].keywords.split(',')
                        ]
                        values_dict = {
                            pair.split(':')[0]: float(pair.split(':')[1]) for pair in keyword_value_pairs
                        }
                        value = values_dict.get(keyword, 0.0)
                        news_with_values.append((news, value))

                    # 按权重排序并归一化
                    news_with_values.sort(key=lambda x: x[1], reverse=True)
                    values = [value for (_, value) in news_with_values]
                    max_value = values[0] if values else 1
                    min_value = values[-1] if values else 0
                    normalized_news_with_values = [
                        (_, (value - min_value) / (max_value - min_value + 0.00001))
                        for (_, value) in news_with_values
                    ]
                    news_with_values = normalized_news_with_values

                    # 按发布时间排序
                    news_with_values.sort(key=lambda x: x[0].pub_time, reverse=True)

                    # 构建返回结果
                    processed_news_text = (
                        f'<p style="font-size: 25px; text-align: center; font-family: 微软雅黑;">'
                        f"<h3>关键词【{keyword}】在【{selected_month.split('-')[0]}】年"
                        f"【{selected_month.split('-')[1]}】月份的相关新闻共有{len(news_with_values)}条"
                        f"（按关键词相关指数排序）</h3></p>"
                    )
                    original_news_text = ""

                    for idx, (news, value) in enumerate(news_with_values, start=1):
                        value = round(value, 3)
                        pub_time = news.pub_time.strftime("%Y-%m-%d %H:%M:%S")
                        category = news.category if news.category else '未知分区'
                        processed_news_text += f"""
                            <div style="margin-bottom: 20px; font-size: 22px;">
                                <p style="font-size: 28px; text-align: center; font-family: 微软雅黑;">
                                    <a href="{news.url}" style="color: #1E90FF; text-decoration: none;">{news.title}</a>
                                </p>
                                <p><strong>发布时间：</strong>{str(pub_time).split(' ')[0]}</p>
                                <p><strong>分区：</strong>{category}</p>
                                <p><strong>重要指数：</strong>{value}</p>
                                <p style="font-size: 22px; font-family: 微软雅黑; color: #333333;">{self._get_summary(news.body)}</p>
                            </div>
                        """
                        original_news_text += str(idx) + '. ' + news.title
                    result = {
                        "processed_news_text": processed_news_text,
                        "original_news_text": original_news_text,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "is_delete": 0
                    }
                    # 缓存1个月
                    self.redis_client.setex(cache_key, 2592000, json.dumps(result))
                    # 添加到布隆过滤器
                    self.bloom_filter.add(cache_key)
                    return processed_news_text, original_news_text
        except Exception as e:
            print(f"Error during database connection or query: {e}")
            return "查询时出现错误"

    def search_news_by_keyword(self, keyword, selected_month, selected_category):
        """
        根据关键词在当前月份范围内搜索新闻
        """
        try:
            if selected_month != "请选择月份":
                start_date = datetime.strptime(selected_month, "%Y-%m")
                end_date = start_date + relativedelta(months=1)

            # 获取缓存数据
            cache_key = f"news:{selected_month[:4]}:{selected_month[5:7]}:{keyword}:{selected_category}"
            print(f"新闻缓存键: {cache_key}")
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                print("-----从缓存中获取新闻数据-----")
                cached_data = json.loads(cached_data)
                if "error" in cached_data:
                    print(cached_data["error"])
                    return None
                news_results = cached_data["news_results"]
                print(f"找到相关新闻{len(news_results)}条")
                # 增加热点新闻点击量
                self._increment_click_for_keyword(keyword)
                print(f"关键词：{keyword} 热度：{self.redis_client.zscore('keyword_click_rank', keyword)}")
                return news_results
            else:
                print("-----缓存未命中，开始从数据库查询新闻-----")
                # 获取分布式锁，设置过期时间10秒防止死锁
                lock_key = f"lock:{cache_key}"
                lock_acquired = self.redis_client.set(lock_key, "locked", ex=10, nx=True)
                if not lock_acquired:
                    print("-----缓存未命中，且锁被其他请求占用，等待中-----")
                    # 如果没有获得锁，等待一段时间后重新检查缓存
                    while not self.redis_client.get(lock_key):
                        cached_data = self.redis_client.get(cache_key)
                        if cached_data:
                            print("-----缓存重新命中，返回缓存数据-----")
                            cached_data = json.loads(cached_data)
                            if "error" in cached_data:
                                print(cached_data["error"])
                                return None
                            news_results = cached_data["news_results"]
                            print(f"找到相关新闻{len(news_results)}条")
                            # 增加热点新闻点击量
                            self._increment_click_for_keyword(keyword)
                            print(f"关键词：{keyword} 热度：{self.redis_client.zscore('keyword_click_rank', keyword)}")
                            return news_results
                else:
                    # 如果获得了锁，查询数据库并更新缓存
                    try:
                        with self.db.get_session() as session:
                            # 查询符合条件的新闻和关键词
                            query = (
                                session.query(News)
                                .join(Keywords, News.id == Keywords.news_id)
                                .filter(
                                    News.pub_time >= start_date,
                                    News.pub_time < end_date,
                                    News.is_delete == 0,
                                    Keywords.keywords.like(f"%{keyword}%")
                                )
                                .options(joinedload(News.keywords))
                            )
                            if selected_category != "所有分区":
                                query = query.filter(News.category == selected_category)
                            related_news = query.all()
                            if not related_news:
                                print("未找到相关新闻")
                                result = {
                                    "error": "未找到相关新闻",
                                }
                                # 设置缓存，避免后续请求重复查询
                                self.redis_client.setex(cache_key, 60, json.dumps(result))
                                # 增加热点新闻点击量
                                self._increment_click_for_keyword(keyword)
                                print(f"关键词：{keyword} 热度：{self.redis_client.zscore('keyword_click_rank', keyword)}")
                                return None
                            # 构建新闻列表
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
                            # 缓存1个月
                            self.redis_client.setex(cache_key, 2592000, json.dumps(result))
                            print(f"找到相关新闻{len(news_results)}条")
                            # 增加热点新闻点击量
                            self._increment_click_for_keyword(keyword)
                            print(f"关键词：{keyword} 热度：{self.redis_client.zscore('keyword_click_rank', keyword)}")
                            return news_results
                    finally:
                        # 释放锁
                        self.redis_client.delete(lock_key)
        except Exception as e:
            print(f"Error during database connection or query: {e}")
            return "查询时出现错误"

    def _increment_click_for_keyword(self, keyword):
        self.redis_client.zincrby("keyword_click_rank", 1, keyword)

    def get_top_keyword(self, n):
        top_keyword = self.redis_client.zrevrange("keyword_click_rank", 0, n - 1, withscores=True)
        return [{"keyword": keyword[0], "clicks": keyword[1]} for keyword in top_keyword]

    def _get_summary(self, body):
        return body[:150] + '...' if len(body) > 150 else body
