import random

import redis
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import joinedload

from Redis.redis_config import get_redis_cluster_client
from ..text_processing.keyword_extraction import (
    tfidf_extract_keywords,
    remove_rubbish_words,
    get_mon_keywords_with_count_list, jieba_tfidf_extract_keywords, pagerank_extract_keywords, lda_extract_keywords
)
from ..data_storage.models import News, Keywords


class KeywordService:
    def __init__(self, db):
        self.db = db
        self.redis_client = get_redis_cluster_client()

    def fetch_keywords_by_time(self, selected_month, selected_category, keywords_num=50, algorithm="tf-idf"):
        print(f"选择的算法是: {algorithm}")
        cache_key = f"keywords:{selected_month[:4]}:{selected_month[5:7]}:{algorithm}:{keywords_num}"
        print(f"关键词缓存键: {cache_key}")
        # 检查缓存
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            # print(f"-----从缓存中获取关键词数据-----")
            cached_result = json.loads(cached_data)
            mon_keywords_list_with_weight = cached_result['keywords_with_weight']
            mon_keywords_list_with_count = get_mon_keywords_with_count_list(cached_result['keywords_with_weight'],
                                                                            keywords_num)
            return mon_keywords_list_with_weight, mon_keywords_list_with_count
        print(f"-----缓存未命中，开始从数据库查询并计算关键词------")

        try:
            with self.db.get_session() as session:
                # 计算时间范围
                start_time = datetime.strptime(selected_month, "%Y-%m")
                end_time = start_time + relativedelta(months=1)
                last_day_of_month = end_time - relativedelta(days=1)
                # 查询符合条件的关键词数据
                query = session.query(Keywords).join(News, News.id == Keywords.news_id).filter(
                    News.pub_time >= start_time,
                    News.pub_time < end_time,
                    News.is_delete == 0,
                    Keywords.created_at >= last_day_of_month,
                    Keywords.is_delete == 0
                )
                if selected_category and selected_category != "所有分区":
                    query = query.filter(News.category.ilike(selected_category.strip()))
                existing_keywords = query.all()

                if existing_keywords and len(existing_keywords) > keywords_num:
                    print(
                        f"找到数据库中已存在的关键词数据，且数据量{len(existing_keywords)}大于{keywords_num}，直接返回数据")
                    mon_keywords_list_with_weight = []
                    for keyword_entry in existing_keywords:
                        mon_keywords_list_with_weight.extend(keyword_entry.keywords.split(", "))
                    mon_keywords_list_with_count = get_mon_keywords_with_count_list(mon_keywords_list_with_weight,
                                                                                    keywords_num)
                else:
                    print(
                        f"找不到数据库中已存在的关键词数据，或数据量{len(existing_keywords)}小于{keywords_num}，重新提取关键词")
                    # 尝试从缓存中获取新闻数据
                    print(selected_category)
                    news_cache_key = f"news:{selected_month[:4]}:{selected_month[5:7]}:{selected_category}"
                    print(f"新闻缓存键: {news_cache_key}")
                    news_cached_data = self.redis_client.get(news_cache_key)
                    if news_cached_data:
                        print(f"-----从缓存中获取新闻数据-----")
                        news_in_selected_month = json.loads(news_cached_data)
                    else:
                        query = session.query(News).filter(
                            News.pub_time >= start_time,
                            News.pub_time < end_time,
                            News.is_delete == 0
                        )
                        if selected_category and selected_category != "所有分区":
                            query = query.filter(News.category == selected_category)
                        mon_keywords_list_with_weight = []
                        idx = 0
                        news_in_selected_month = query.options(joinedload(News.keywords)).all()
                        # 将新闻数据转换为符合格式并写入缓存
                        news_data = [
                            {
                                "id": news.id,
                                "url": news.url,
                                "category": news.category,
                                "title": news.title,
                                "pub_time": news.pub_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "body": news.body,
                                "created_at": news.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                                "is_delete": news.is_delete
                            }
                            for news in news_in_selected_month
                        ]
                        # 设置1个月的过期时间
                        self.redis_client.setex(news_cache_key, 2592000 + random.randint(0, 3600), json.dumps(news_data))
                        print(f"新闻数据写入缓存成功！")

                    # 遍历新闻，提取关键词
                    for news in news_in_selected_month:
                        if algorithm == "jieba提供的TF-IDF":
                            keywords = jieba_tfidf_extract_keywords(news.body, keywords_num)
                        elif algorithm == "自行编写的TF-IDF（要等较长时间）":
                            keywords = tfidf_extract_keywords(keywords_num, idx, news_in_selected_month)
                        elif algorithm == "PageRank":
                            keywords = pagerank_extract_keywords(news.body, keywords_num)
                        elif algorithm == "LDA":
                            keywords = lda_extract_keywords(news.body, keywords_num)
                        else:
                            raise ValueError("不存在这种算法！")

                        # 保存关键词到 Keywords 表
                        keyword_entry = Keywords(
                            news_id=news.id,
                            algorithm=algorithm,
                            keywords=", ".join(keywords),
                            keywords_num=len(keywords)
                        )
                        session.add(keyword_entry)
                        mon_keywords_list_with_weight.extend(keywords)
                        idx += 1
                    session.commit()
                    # 获取关键词的统计信息
                    mon_keywords_list_with_count = get_mon_keywords_with_count_list(mon_keywords_list_with_weight,
                                                                                    keywords_num)
                # 将结果写入缓存
                cache_data = {
                    "keywords_with_weight": mon_keywords_list_with_weight,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_delete": 0
                }
                # 设置1天的过期时间
                self.redis_client.setex(cache_key, 86400, json.dumps(cache_data))
                print(f"关键词数据写入缓存成功！")
                return mon_keywords_list_with_weight, mon_keywords_list_with_count
        except Exception as e:
            print(f"Error during database connection or text processing: {e}")
            return [], []
