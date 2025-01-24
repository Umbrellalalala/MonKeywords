# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 18:04
@Auth: Zhang Hongxing
@File: views.py
@Note:   
"""
import json
import os
import time
from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QLabel, QDialog, QVBoxLayout, QDialogButtonBox
from wordcloud import WordCloud

from Mysql.db_config import DB_PARAMS
from Redis.redis_config import get_redis_cluster_client
from ..data_storage.database import Database
from ..data_storage.models import News, Cloud, Summary
from ..services.crawl_service import CrawlService
from ..services.keyword_service import KeywordService
from ..services.news_service import NewsService
from ..text_processing.summarize import SparkAIChatSummarizer


class MonKeyWordsViews:
    def __init__(self, main_window):
        self.main_window = main_window
        self.news_service = NewsService(self.main_window.db)
        self.keyword_service = KeywordService(self.main_window.db)
        self.crawl_service = CrawlService(self.main_window.db)
        self.db_params = DB_PARAMS
        self.db = Database(self.db_params)
        self.redis_client = get_redis_cluster_client()
        # Flask的配置，上传文件夹路径
        self.UPLOAD_FOLDER = 'static/wordclouds'
        # 创建文件夹（如果不存在）
        if not os.path.exists(self.UPLOAD_FOLDER):
            os.makedirs(self.UPLOAD_FOLDER)

    '''
    下拉框
    '''

    def get_existing_times(self):
        self.existing_times = self.crawl_service.get_existing_times()
        return self.existing_times

    def populate_month_combobox(self):
        months = self.get_existing_times()
        self.main_window.month_combobox.clear()
        self.main_window.month_combobox.addItems(months)

    def populate_month_search_combobox(self):
        months = self.get_existing_times()
        self.main_window.month_search_combobox.clear()
        self.main_window.month_search_combobox.addItems(months)

    def populate_category_combobox(self):
        """获取所有分区并填充到下拉框"""
        try:
            with self.main_window.db.get_session() as session:
                categories = session.query(News.category).distinct().all()
                for category in categories:
                    self.main_window.category_combobox.addItem(category[0])
        except Exception as e:
            print(f"Error while fetching categories: {e}")

    '''
    更新数据
    '''

    def update_data(self):
        new_start_time = self.crawl_service.get_last_record_pub_time()
        if new_start_time is not None:
            new_end_time = datetime.now()
            self.main_window.new_start_time = new_start_time.strftime("%Y-%m-%d")
            self.main_window.new_end_time = new_end_time.strftime("%Y-%m-%d")
            if self.main_window.new_start_time != self.main_window.new_end_time:
                self.main_window.update_data_dialog = QMessageBox(self.main_window)
                self.main_window.update_data_dialog.setWindowTitle('稍等')
                self.main_window.update_data_dialog.show()
                self.crawl_service.start_crawler(new_start_time, new_end_time)
            else:
                dialog = QDialog(self.main_window)
                dialog.setWindowTitle('MonKeyWords 🐒')
                dialog.resize(400, 200)  # 直接设置对话框的尺寸
                dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
                layout = QVBoxLayout()
                label = QLabel("没有新的数据，无需更新！", dialog)
                layout.addWidget(label)
                buttons = QDialogButtonBox(QDialogButtonBox.Ok, dialog)
                buttons.accepted.connect(dialog.accept)
                layout.addWidget(buttons)
                dialog.setLayout(layout)
                dialog.exec_()
        self.get_existing_times()
        self.populate_month_combobox()

    '''
    获取关键词
    '''

    def get_keywords(self):
        algorithm = self.main_window.algorithm_combobox.currentText()
        top_k = self.main_window.keywords_count_spinbox.value()
        selected_month = self.main_window.month_combobox.currentText()
        selected_category = self.main_window.category_combobox.currentText()
        _, mon_keywords_list_with_count = self.keyword_service.fetch_keywords_by_time(selected_month, selected_category,
                                                                                      top_k, algorithm)
        self.main_window.keywords_label.clear()
        if algorithm == "jieba提供的TF-IDF" or algorithm == "自行编写的TF-IDF（要等较长时间）":
            label = QListWidgetItem('关键词:词频（tf-idf）')
        elif algorithm == "PageRank":
            label = QListWidgetItem('关键词:词频（PageRank）')
        elif algorithm == "LDA":
            label = QListWidgetItem('关键词:词频（LDA）')
        label.setForeground(Qt.black)
        label.setTextAlignment(Qt.AlignCenter)
        self.main_window.keywords_label.addItem(label)
        for keyword in mon_keywords_list_with_count:
            item = QListWidgetItem(keyword)
            item.setData(Qt.UserRole, keyword)
            self.main_window.keywords_label.addItem(item)
        return mon_keywords_list_with_count

    '''
    获取新闻
    '''

    def get_news_list(self, keyword):
        selected_month = self.main_window.month_combobox.currentText()
        return self.news_service.get_news_list(selected_month, keyword)

    def format_news_results(self, news_results):
        # 格式化新闻显示
        html_content = ""
        for news in news_results:
            html_content += f"<h3><a href='{news['url']}'>{news['title']}</a></h3><p>{news['summary']}</p>"
        return html_content

    """
    获取词云
    """

    def generate_word_cloud(self):
        try:
            sns.set_style('whitegrid')
            plt.rcParams['font.size'] = 12
            plt.rcParams['figure.dpi'] = 300
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False

            keywords_num = self.main_window.keywords_count_spinbox.value()
            algorithm = self.main_window.algorithm_combobox.currentText()
            date = self.main_window.month_combobox.currentText()
            year = date.split("-")[0]
            month = date.split("-")[1]
            category = self.main_window.category_combobox.currentText()
            # Redis缓存Key
            cache_key = f"wordcloud:{year}:{month}:{category}:{keywords_num}:{algorithm}"
            print(f"词云缓存键: {cache_key}")
            # 检查Redis缓存
            cached_image_path = self.redis_client.get(cache_key)
            if cached_image_path:
                print("-----从缓存中获取词云图片-----")
                data = json.loads(cached_image_path)
                image_path = data['cloud_url']
            else:
                print("-----缓存未命中，开始从数据库查询词云-----")
                # 先检查数据库中是否已存在该类别的词云链接
                session = self.db.get_session()
                existing_asset = session.query(Cloud).filter_by(
                    year=year,
                    month=month,
                    category=category,
                    algorithm=algorithm,
                    is_delete=0
                ).first()

                if existing_asset:
                    # 如果数据库中有已生成的词云，直接展示
                    image_path = existing_asset.cloud_url
                    print(f"数据库中已存在词云图片：{image_path}")
                else:
                    # 如果数据库中没有，生成新的词云并保存
                    keywords = self.get_keywords()
                    if not keywords:
                        QMessageBox.warning(self.main_window, "MonKeyWords 🐒", "没有关键词数据可供生成词云！")
                        return
                    keywords_dict = {keyword.split(":")[0]: int(keyword.split(":")[1]) for keyword in keywords}
                    font_path = './utils/SimHei.ttf'
                    wordcloud = WordCloud(
                        font_path=font_path,
                        width=1000, height=600,
                        background_color='white',
                        colormap='tab20'
                    ).generate_from_frequencies(keywords_dict)
                    # 生成图片文件名和路径
                    image_filename = f"{date}_{category}_{algorithm}_{keywords_num}_{time.strftime('%Y%m%d%H%M%S')}.png"
                    image_path = self.UPLOAD_FOLDER + '/' + image_filename
                    wordcloud.to_file(image_path)
                    # 将新的词云路径保存到数据库
                    asset = Cloud(
                        year=year,
                        month=month,
                        category=category,
                        keywords_num=keywords_num,
                        algorithm=algorithm,
                        cloud_url=image_path
                    )
                    print(f"保存图片路径到数据库：{image_path}")
                    session.add(asset)
                    session.commit()
                    session.close()
                # 将新的词云路径保存到Redis
                result = {
                    'cloud_url': image_path,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_delete": 0
                }
                self.redis_client.setex(cache_key, 86400, json.dumps(result))
            # 显示词云图
            dialog = QDialog(self.main_window)
            selected_month = self.main_window.month_combobox.currentText()
            dialog.setWindowTitle(f"{selected_month} 词云")
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            dialog.resize(1000, 600)
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                label = QLabel(dialog)
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                layout = QVBoxLayout(dialog)
                layout.addWidget(label)
                dialog.setLayout(layout)
                dialog.exec_()
            else:
                QMessageBox.warning(self.main_window, "MonKeyWords 🐒", "词云图片无法加载！")
        except Exception as e:
            print(f"Error while generating word cloud: {e}")
            QMessageBox.critical(self.main_window, "MonKeyWords 🐒", "生成词云时出错！")
    """
    生成摘要
    """

    def generate_summary(self, news, keyword):
        try:
            keywords_num = self.main_window.keywords_count_spinbox.value()
            algorithm = self.main_window.algorithm_combobox.currentText()
            date = self.main_window.month_combobox.currentText()
            year = date.split("-")[0]
            month = date.split("-")[1]
            category = self.main_window.category_combobox.currentText()
            # Redis缓存Key
            if ":" in keyword:
                keyword = keyword.split(":")[0]
            cache_key = f"summary:{year}:{month}:{category}:{keywords_num}:{keyword}:{algorithm}"
            print(f"摘要缓存键: {cache_key}")
            # 检查Redis缓存
            cached_summary_path = self.redis_client.get(cache_key)
            if cached_summary_path:
                print("-----从缓存中获取摘要文本-----")
                data = json.loads(cached_summary_path)
                summary = data['summary']
            else:
                print("-----缓存未命中，开始在数据库中查询摘要-----")
                session = self.db.get_session()
                existing_asset = session.query(Summary).filter_by(
                    year=year,
                    month=month,
                    category=category,
                    algorithm=algorithm,
                    keyword=keyword,
                    keywords_num=keywords_num,
                    is_delete=0
                ).first()
                if existing_asset:
                    summary = existing_asset.summary
                    print(f"数据库中已存在摘要：{summary}")
                else:
                    print("生成摘要中...")
                    SPARKAI_APP_ID = 'fc94945d'
                    SPARKAI_API_KEY = 'fe58934e5b985599f221e37d1a351b09'
                    SPARKAI_API_SECRET = 'MWQ5YWMyYjQ5OTE5ODZlNjM1ODA3MTBl'
                    summarizer = SparkAIChatSummarizer(
                        version="pro",
                        SPARKAI_APP_ID=SPARKAI_APP_ID,
                        SPARKAI_API_KEY=SPARKAI_API_KEY,
                        SPARKAI_API_SECRET=SPARKAI_API_SECRET
                    )
                    summary = summarizer.summarize(news, keyword, date)
                    # 保存摘要到数据库
                    if ":" in keyword:
                        keyword = keyword.split(":")[0]
                    asset = Summary(
                        year=year,
                        month=month,
                        category=category,
                        keywords_num=keywords_num,
                        keyword=keyword,
                        algorithm=algorithm,
                        summary=summary
                    )
                    session.add(asset)
                    session.commit()
                result = {
                    'summary': summary,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_delete": 0
                }
                self.redis_client.setex(cache_key, 86400, json.dumps(result))
                session.close()
            if summary:
                self.main_window.show_summary_dialog(keyword, date, summary)
            else:
                self.main_window.show_summary_dialog("未能生成摘要，请稍后再试。")

        except Exception as e:
            print(f"Error while generating summary: {e}")
            QMessageBox.critical(self.main_window, "MonKeyWords 🐒", "生成摘要时出错！")