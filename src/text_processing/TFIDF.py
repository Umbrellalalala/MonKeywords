# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 22:52
@Auth: Zhang Hongxing
@File: TFIDF.py
@Note:   
"""
import math
from collections import Counter, defaultdict

import jieba


class TFIDF:
    def __init__(self, docs):
        """
        :param docs: 文档列表，每个文档是一个字符串
        """
        self.docs = docs
        self.num_docs = len(docs)
        self.word_doc_freq = defaultdict(int)
        self.word_freq_in_doc = []
        self.calculate_word_doc_freq()
        self.calculate_word_freq_in_docs()

    def calculate_word_doc_freq(self):
        """
        计算每个词在多少个文档中出现
        """
        for doc in self.docs:
            words = set(jieba.cut(doc))
            for word in words:
                self.word_doc_freq[word] += 1

    def calculate_word_freq_in_docs(self):
        """
        计算每个文档中每个词的词频
        """
        for doc in self.docs:
            word_count = Counter(jieba.cut(doc))
            self.word_freq_in_doc.append(word_count)

    def calculate_tf(self, word, doc_idx):
        """
        计算某个词在指定文档中的 TF 值
        :param word: 词
        :param doc_idx: 文档索引
        :return: TF 值
        """
        word_count = self.word_freq_in_doc[doc_idx]
        total_words = sum(word_count.values())
        return word_count[word] / total_words

    def calculate_idf(self, word):
        """
        计算某个词的 IDF 值
        :param word: 词
        :return: IDF 值
        """
        doc_freq = self.word_doc_freq.get(word, 0)
        return math.log(self.num_docs / (1 + doc_freq)) if doc_freq > 0 else 0

    def calculate_tfidf(self, word, doc_idx):
        """
        计算某个词在某个文档中的 TF-IDF 值
        :param word: 词
        :param doc_idx: 文档索引
        :return: TF-IDF 值
        """
        tf = self.calculate_tf(word, doc_idx)
        idf = self.calculate_idf(word)
        return tf * idf

    def extract_keywords(self, doc_idx, top_k=10):
        """
        提取指定文档中 TF-IDF 权重最高的 top_k 个词
        :param doc_idx: 文档索引
        :param top_k: 取前 K 个关键词
        :return: 关键词及其 TF-IDF 权重
        """
        doc = self.docs[doc_idx]
        words = jieba.cut(doc)
        tfidf_scores = {}
        # print(f"words: {words}")
        for word in words:
            tfidf_scores[word] = self.calculate_tfidf(word, doc_idx)
        sorted_words = sorted(tfidf_scores.items(), key=lambda item: item[1], reverse=True)
        # print(f"sorted_words: {sorted_words}")
        return sorted_words[:top_k]
