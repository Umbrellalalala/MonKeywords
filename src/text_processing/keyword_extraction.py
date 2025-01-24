# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 17:52
@Auth: Zhang Hongxing
@File: keyword_extraction.py
@Note:   
"""
import math
import re
import logging
from collections import Counter
import jieba
import jieba.analyse
from src.text_processing.TFIDF import TFIDF

logging.getLogger('jieba').setLevel(logging.ERROR)

from gensim import corpora, models
import jieba


def lda_extract_keywords(text, top_k, num_topics=5):
    """
    使用LDA提取文本中的关键词。
    :param text: 输入文本
    :param top_k: 选择前 K 个关键词
    :param num_topics: LDA 模型的主题数
    :return: 关键词列表
    """
    from gensim import corpora, models
    from jieba import lcut
    words = [word for word in lcut(text) if len(word) > 1]
    if not words:
        print("输入文本分词后为空！")
        return []
    dictionary = corpora.Dictionary([words])
    corpus = [dictionary.doc2bow(words)]
    lda_model = models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=10)
    topics = lda_model.show_topics(num_topics=num_topics, num_words=top_k, formatted=False)
    keywords_list = []
    for topic in topics:
        for word, weight in topic[1]:
            keywords_list.append(f"{word}:{round(weight, 3)}")
    keywords_list = remove_rubbish_words(keywords_list)
    return keywords_list



def pagerank_extract_keywords(text, top_k):
    """
    使用 TextRank 提取文本中的关键词。
    :param text: 输入文本
    :param top_k: 选择前 K 个关键词
    :return: 格式化的关键词列表
    """
    try:
        tags_list_with_weight = jieba.analyse.textrank(text, topK=top_k, withWeight=True)
        tags_list_with_weight = sorted(tags_list_with_weight, key=lambda x: x[1], reverse=True)
        keywords_list = [f"{tag[0]}:{round(tag[1], 3)}" for tag in tags_list_with_weight]
        keywords_list = remove_rubbish_words(keywords_list)
        return keywords_list
    except Exception as e:
        print(f"Error in TextRank keyword extraction: {e}")
        return []


def jieba_tfidf_extract_keywords(text, top_k, docs=None):
    """
    提取文本中的关键词。
    :param text: 输入文本
    :param top_k: 选择前 K 个关键词
    :param docs: 文档列表 (可选)
    :return: 关键词列表
    """
    tags_list_with_weight = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
    tags_list_with_weight = sorted(tags_list_with_weight, key=lambda x: x[1], reverse=True)
    keywords_list = [':'.join(tuple(str(item) for item in tag)) for tag in tags_list_with_weight]
    keywords_list = remove_rubbish_words(keywords_list)
    return keywords_list


def tfidf_extract_keywords(top_k, idx, news_in_selected_month):
    """
    提取文本中的关键词。
    :param text: 输入文本
    :param top_k: 选择前 K 个关键词
    :param docs: 文档列表 (可选)
    :return: 关键词列表
    """
    docs = []
    for news in news_in_selected_month:
        docs.append(news.title)
    tfidf_extractor = TFIDF(docs)
    keywords_with_weight = tfidf_extractor.extract_keywords(idx, top_k)
    keywords_list = [f"{keyword}:{round(weight, 3)}" for keyword, weight in keywords_with_weight]
    keywords_list = remove_rubbish_words(keywords_list)
    return keywords_list


def get_mon_keywords_with_count_list(all_mon_keywords_list, top_k):
    """
    获取关键词及其出现次数的统计列表。
    :param all_mon_keywords_list: 所有关键词的列表
    :param top_k: 选择前 K 个关键词
    :return: 带统计次数的关键词列表
    """
    all_mon_keywords_list = [mon_keywords.split(":")[0] for mon_keywords in all_mon_keywords_list]
    keyword_counts = Counter(all_mon_keywords_list)
    mon_keywords_list = [f"{keyword}:{count}" for keyword, count in keyword_counts.most_common(top_k)]
    return mon_keywords_list


def remove_rubbish_words(mon_keywords_list):
    """
    移除指定的无用关键词，包括纯英文、纯数字、小数。
    :param mon_keywords_list: 关键词列表
    :return: 去除无用关键词后的列表
    """
    try:
        with open('./utils/remove_keywords_list.txt', 'r', encoding='UTF-8') as f:
            rubbish_word_list = [line.strip() for line in f.readlines()]
        def is_pure_english(word):
            return bool(re.match(r'^[a-zA-Z]+$', word))  # 纯英文
        def is_pure_number(word):
            return bool(re.match(r'^\d+$', word))  # 纯数字
        def is_decimal(word):
            return bool(re.match(r'^\d*\.\d+$', word))  # 小数
        def is_space(word):
            return bool(re.match(r'^\s$', word))
        def is_pure_symbol(word):
            return bool(re.match(r'^[^\u4e00-\u9fa5a-zA-Z0-9\s]+$', word))
        mon_keywords_list = [
            word for word in mon_keywords_list
            if word.split(":")[0] not in rubbish_word_list
               and not is_pure_english(word.split(":")[0])
               and not is_pure_number(word.split(":")[0])
               and not is_decimal(word.split(":")[0])
               and not is_space(word.split(":")[0])
               and not is_pure_symbol(word.split(":")[0])
        ]
    except Exception as e:
        print("Error loading rubbish words:", e)
    return mon_keywords_list
