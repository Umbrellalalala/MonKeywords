# -*- coding: utf-8 -*-
"""
@Time: 2024/12/15 22:10
@Auth: Zhang Hongxing
@File: summarize.py
@Note:  SparkAI LLM 摘要生成类封装
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from ..data_storage.models import News, Keywords, Cloud
from sparkai.core.messages import ChatMessage
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
MAX_TOKENS = 4096
TOP_K = 1
TEMPERATURE = 0.1

class SparkAIChatSummarizer:
    def __init__(self, version="pro", SPARKAI_APP_ID=None, SPARKAI_API_KEY=None, SPARKAI_API_SECRET=None,
                 prompt_preprocessor=None, db=None):
        """
        初始化 SparkAIChatSummarizer 类，配置相关参数
        :param version: LLM版本，支持的版本有 'ultra', 'max-32k', 'max', 'pro-128k', 'pro', 'lite'
        :param SPARKAI_APP_ID: SparkAI应用ID
        :param SPARKAI_API_KEY: SparkAI API Key
        :param SPARKAI_API_SECRET: SparkAI API Secret
        :param prompt_preprocessor: 可选的预处理器，可以处理输入的文本
        """
        self.version = version
        self.SPARKAI_APP_ID = SPARKAI_APP_ID
        self.SPARKAI_API_KEY = SPARKAI_API_KEY
        self.SPARKAI_API_SECRET = SPARKAI_API_SECRET
        self.prompt_preprocessor = prompt_preprocessor
        self._configure_spark_api()
        # 配置数据库连接
        self.db = db
        self._configure_spark_api()

    def _configure_spark_api(self):
        """
        根据版本配置 SparkAI 的 URL 和 Domain
        """
        if self.version == "ultra":
            self.SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'
            self.SPARKAI_DOMAIN = '4.0Ultra'
        elif self.version == "max-32k":
            self.SPARKAI_URL = 'wss://spark-api.xf-yun.com/chat/max-32k'
            self.SPARKAI_DOMAIN = 'max-32k'
        elif self.version == "max":
            self.SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
            self.SPARKAI_DOMAIN = 'generalv3.5'
        elif self.version == "pro-128k":
            self.SPARKAI_URL = 'wss://spark-api.xf-yun.com/chat/pro-128k'
            self.SPARKAI_DOMAIN = 'pro-128k'
        elif self.version == "pro":
            self.SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.1/chat'
            self.SPARKAI_DOMAIN = 'generalv3'
        elif self.version == "lite":
            self.SPARKAI_URL = 'wss://spark-api.xf-yun.com/v1.1/chat'
            self.SPARKAI_DOMAIN = 'lite'
        else:
            raise ValueError("Invalid version")

        self.spark = ChatSparkLLM(
            spark_api_url=self.SPARKAI_URL,
            spark_app_id=self.SPARKAI_APP_ID,
            spark_api_key=self.SPARKAI_API_KEY,
            spark_api_secret=self.SPARKAI_API_SECRET,
            spark_llm_domain=self.SPARKAI_DOMAIN,
            streaming=False
        )

    def _prepare_prompt(self, articles, keyword, date):
        """
        准备输入给模型的提示（Prompt），可以添加额外的处理逻辑
        :param articles: 文章内容的列表
        :return: 返回一个完整的提示字符串
        """
        if self.prompt_preprocessor:
            articles = self.prompt_preprocessor(articles)
        if len(articles) > MAX_TOKENS:
            articles = articles[:MAX_TOKENS]
        prompt = (f"请确保你的回答符合伦理规范，避免包含任何违法、敏感或不适当的内容。请你扮演一个新闻总结器；根据关键词、日期以及以下新闻内容，用你自己的话做出概括性的总结，"
                  f"不要分点作答，可以分段，有层次地给出，字数控制在100字以内！\n"
                  f"新闻以“““{{新闻}}”””的格式给你了，请以关键词：【{keyword}】，日期：【{date}】为开头作答；\n")
        prompt += "“““"
        prompt += articles
        prompt = prompt.replace("总书记", "")
        prompt = prompt.replace("习近平", "")
        prompt = prompt.replace("记者", "")
        prompt = prompt.replace("叙利亚", "")
        prompt = prompt.replace("台军", "")
        prompt = prompt.replace("台湾", "")
        prompt = prompt.replace("部队", "")
        prompt += "”””"
        return prompt

    def summarize(self, articles, keyword, date):
        """
        生成文章总结
        :param articles: 文章内容的列表
        :return: 返回摘要
        """
        prompt = self._prepare_prompt(articles, keyword, date)
        print("Prompt: ", prompt)
        messages = [ChatMessage(
            role="user",
            content=prompt
        )]
        handler = ChunkPrintHandler()
        try:
            response = self.spark.generate([messages], callbacks=[handler], temperature=TEMPERATURE, top_k=TOP_K)
            summary = response.generations[0][0].text
            print("生成的摘要是：", summary)
        except Exception as e:
            summary = f"无法生成摘要，可能是涉及了违法违规的内容，试试其他内容吧！"
        return summary