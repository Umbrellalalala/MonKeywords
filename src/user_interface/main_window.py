# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 18:04
@Auth: Zhang Hongxing
@File: main_window.py
@Note:
"""

import re
import webbrowser
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, \
    QScrollArea, QTextBrowser, QDialog, QListWidget, QLineEdit, QDialogButtonBox, QVBoxLayout, QSpinBox, QMessageBox
from sqlalchemy.dialects.mssql.information_schema import views

from Mysql.db_config import DB_PARAMS
from src.data_storage.database import Database
from src.data_storage.models import News
from src.user_interface.views import MonKeyWordsViews
from src.helpers.url_helpers import open_url_in_browser


class MonKeyWords(QWidget):
    def __init__(self, db_params):
        super().__init__()
        self.db_params = db_params
        self.db = Database(self.db_params)
        # 创建窗口
        self.setWindowTitle('MonKeyWords 🐒')
        self.resize(800, 1200)
        self.views = MonKeyWordsViews(self)
        # 更新数据按钮
        self.update_data_btn = QPushButton('【⌛️更新数据】')
        self.update_data_btn.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
        self.update_data_btn.clicked.connect(self.views.update_data)
        # 年月选择下拉框
        self.month_combobox = QComboBox()
        self.views.populate_month_combobox()
        # 获取关键词按钮
        self.get_keywords_btn = QPushButton('【🐒直接获取月度关键词！】')
        self.get_keywords_btn.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
        self.get_keywords_btn.clicked.connect(self.views.get_keywords)
        # 选择算法
        self.algorithm_combobox = QComboBox()
        self.algorithm_combobox.addItem("jieba提供的TF-IDF")
        self.algorithm_combobox.addItem("自行编写的TF-IDF（要等较长时间）")
        self.algorithm_combobox.addItem("PageRank")
        self.algorithm_combobox.addItem("LDA")  # 可以根据需要添加更多算法
        self.algorithm_combobox.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
        # 搜索框和搜索图标
        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText('🔍用关键词搜索新闻（键入关键词后，输入Enter以确认）')
        self.search_line_edit.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
        self.search_line_edit.returnPressed.connect(self.on_search)
        # 搜索页月份选择下拉框
        self.month_search_combobox = QComboBox()
        self.month_search_combobox.addItem('请选择月份')
        self.views.populate_month_combobox()
        # 关键词数量输入框
        self.keywords_count_spinbox = QSpinBox()
        self.keywords_count_spinbox.setRange(1, 200)
        self.keywords_count_spinbox.setValue(50)
        # 关键词列表
        self.keywords_label = QListWidget()
        self.keywords_label.itemClicked.connect(self.show_news_and_values)
        # 分区筛选下拉框
        self.category_combobox = QComboBox(self)
        self.category_combobox.addItem('所有分区')
        self.views.populate_category_combobox()  # 初始化分区下拉框
        # 弹出框实例
        self.current_dialog = None
        # 词云按钮
        self.word_cloud_btn = QPushButton('【🌐生成词云】')
        self.word_cloud_btn.clicked.connect(self.views.generate_word_cloud)
        # 摆放组件
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        VBox = QVBoxLayout()
        VBox.addWidget(self.search_line_edit)
        HBox = QHBoxLayout()
        H2Box = QHBoxLayout()
        H3Box = QHBoxLayout()

        category_layout = QHBoxLayout()
        category_layout.addWidget(self.category_combobox)
        HBox.addLayout(category_layout)

        month_layout = QHBoxLayout()
        month_layout.addWidget(self.month_combobox)
        HBox.addLayout(month_layout)

        VBox.addLayout(HBox)

        H2Box.addWidget(self.update_data_btn)
        H2Box.addWidget(self.get_keywords_btn)
        H2Box.addWidget(self.algorithm_combobox)

        VBox.addLayout(H2Box)

        num_label = QLabel("请设置关键词数量（1至200个）:")
        num_label.setStyleSheet(
            "font-size: 22px; color: black; font-family: 微软雅黑;")
        H3Box.addWidget(num_label)
        H3Box.addWidget(self.keywords_count_spinbox)

        VBox.addLayout(H3Box)

        self.keywords_label.setStyleSheet(
            "font-size: 35px; font-weight: bold; color: black; font-family: 微软雅黑; text-decoration:underline; ")
        VBox.addWidget(self.keywords_label)
        main_layout.addLayout(VBox)

        self.word_cloud_btn.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
        VBox.addWidget(self.word_cloud_btn)

        # 帮助按钮
        self.help_btn = QPushButton('【🧭用户指引】')
        self.help_btn.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
        self.help_btn.clicked.connect(self.show_help_dialog)
        main_layout.addWidget(self.help_btn)
        self.setLayout(main_layout)
        self.show()

    def on_search(self, redo=False):
        if redo:
            search_keyword = self.search_redo_edit.text().strip()
        else:
            search_keyword = self.search_line_edit.text().strip()
        if redo:
            selected_month = self.month_search_combobox.currentText()
            if selected_month == "请选择月份":
                selected_month = self.month_combobox.currentText()
        else:
            selected_month = self.month_combobox.currentText()
        if search_keyword:
            self.search_news(search_keyword, selected_month)
        else:
            QMessageBox.warning(self, "MonKeyWords 🐒", "输入为空，请输入后再进行搜索！")

    def search_news(self, search_keyword, selected_month):
        # print("正在搜索: ", search_keyword)
        selected_category = self.category_combobox.currentText()
        news_results = self.views.news_service.search_news_by_keyword(search_keyword, selected_month, selected_category)
        if self.current_dialog:
            self.current_dialog.close()
        if news_results:
            dialog = QDialog(self)
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            dialog.resize(1200, 1400)
            # 月份选择下拉框
            month_search_label = QLabel("请选择月份:", dialog)
            self.month_search_combobox = QComboBox(dialog)
            self.month_search_combobox.addItem('请选择月份')
            self.views.populate_month_search_combobox()
            dialog.setWindowTitle(f"MonKeyWords 🐒")
            # 搜索框
            search_label = QLabel("修改搜索关键词:", dialog)
            self.search_redo_edit = QLineEdit(dialog)
            self.search_redo_edit.setPlaceholderText('🔍修改搜索关键词')
            self.search_redo_edit.setText(search_keyword)
            self.search_redo_edit.returnPressed.connect(lambda: self.on_search(redo=True))
            # 显示新闻的浏览器
            text_browser = QTextBrowser(dialog)
            text_browser.setOpenExternalLinks(True)
            processed_news, original_news = self.format_news_results(search_keyword, selected_month, news_results)
            text_browser.setHtml(processed_news)
            summary_button = QPushButton('🤖【生成摘要】', dialog)
            summary_button.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
            summary_button.clicked.connect(
                lambda: self.views.generate_summary(original_news, search_keyword))
            # 设置布局
            layout = QVBoxLayout(dialog)
            layout.addWidget(month_search_label)
            layout.addWidget(self.month_search_combobox)
            layout.addWidget(search_label)
            layout.addWidget(self.search_redo_edit)
            layout.addWidget(text_browser)
            layout.addWidget(summary_button)
            dialog.setLayout(layout)
            self.current_dialog = dialog
            dialog.exec_()
        else:
            QMessageBox.warning(self, "MonKeyWords 🐒", "没有找到与该关键词相关的新闻！")

    def show_news_and_values(self):
        # 获取当前选中的项
        keyword = self.keywords_label.currentItem().text()
        if '关键词:词频' in keyword:
            return
        date = self.month_combobox.currentText()
        # 创建新的窗口
        dialog = QDialog(self)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setWindowTitle(f'关键词：{keyword.split(":")[0]} 词频：{keyword.split(":")[1]}')
        dialog.resize(1200, 1400)
        # 创建用于显示新闻和词频的文本浏览器
        text_browser = QTextBrowser(dialog)
        font = QFont()
        font.setPointSize(12)
        font.setFamily("微软雅黑")
        text_browser.setCurrentFont(font)
        # 获取相关的新闻和词频信息
        processed_news, original_news = self.views.get_news_list(str(keyword.split(':')[0]))
        if processed_news == "未找到相关新闻":
            QMessageBox.warning(self, "MonKeyWords 🐒", "没有找到与该关键词相关的新闻！")
        # 设置文本浏览器显示新闻
        text_browser.setHtml(processed_news)
        text_browser.setOpenExternalLinks(True)
        text_browser.setAlignment(Qt.AlignCenter)
        # 创建生成摘要的按钮
        summary_button = QPushButton('🤖【生成摘要】', dialog)
        summary_button.setStyleSheet("font-size: 20px; color: black; font-family: 微软雅黑;")
        summary_button.clicked.connect(lambda: self.views.generate_summary(original_news, keyword))
        # 设置布局
        layout = QVBoxLayout(dialog)
        layout.addWidget(text_browser)
        layout.addWidget(summary_button)
        dialog.setLayout(layout)
        # 显示新的窗口
        dialog.exec_()

    def format_news_results(self, search_keyword, selected_month, news_results):
        print("关键词: ", search_keyword)
        print("月份: ", selected_month)
        html_content = (f'<p style="font-size: 25px; text-align: center; font-family: 微软雅黑;">' +
                        f"<h3>关键词【{search_keyword}】在【{selected_month.split('-')[0]}】年【{selected_month.split('-')[1]}】月份的相关新闻共有{len(news_results)}条（按时间排序）</h3></p>")
        # 遍历新闻结果，构建HTML内容
        original_news = ""
        index = 1
        for news in news_results:
            title = news.get('title', '无标题')
            summary = news.get('summary', '无摘要')
            url = news.get('url', '#')
            pub_time = news.get('pub_time', '未知')
            pub_time = str(pub_time).split(' ')[0]
            category = news.get('category', '未知')
            keywords = news.get('keywords', '未知')
            if keywords != '未知':
                keywords = keywords.split(',')
                for idx, keyword in enumerate(keywords):
                    keywords[idx] = keyword.split(':')[0]
                keywords = keywords[:10]
                keywords = ', '.join(keywords).strip(',')
            html_content += f"""
                <div style="margin-bottom: 20px; font-size: 22px;">
                    <p style="font-size: 28px; text-align: center; font-family: 微软雅黑;">
                        <a href='{url}' style="color: #1E90FF; text-decoration: none;">{title}</a>
                    </p>
                    <p><strong>发布时间：</strong>{str(pub_time).split(' ')[0]}</p>
                    <p><strong>分区：</strong>{category}</p>
                    <p><strong>关键词：</strong>{keywords}</p>
                    <p style="font-size: 22px; font-family: 微软雅黑; color: #333333;">{summary}</p>
                </div>
            """
            original_news += str(index) + '. ' + news.get('title', '无标题')
            index += 1
        # print("HTML内容: ", html_content)
        # print("原始新闻: ", original_news)
        return html_content, original_news

    def show_help_dialog(self):
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle('项目介绍、公式与使用说明')
        help_dialog.resize(1000, 1200)
        help_dialog.setWindowFlags(help_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        text_browser = QTextBrowser(help_dialog)
        text_browser.setOpenExternalLinks(True)
        with open('./help_doc.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        text_browser.setHtml(content)
        text_browser.setAlignment(Qt.AlignCenter)
        font = text_browser.font()
        font.setPointSize(12)
        text_browser.setCurrentFont(font)
        main_layout = QVBoxLayout()
        main_layout.addWidget(text_browser)
        help_dialog.setLayout(main_layout)
        help_dialog.finished.connect(lambda: self.on_help_dialog_closed(help_dialog))  # 监听对话框关闭事件
        help_dialog.exec_()

    def on_help_dialog_closed(self, dialog):
        if self.current_dialog == dialog:
            self.current_dialog = None

    def show_summary_dialog(self, keyword, date, summary_text):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"关键词：【{keyword}】在日期：【{date}】生成的摘要")
        dialog.resize(600, 400)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        text_browser = QTextBrowser(dialog)
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(f"<p style='font-size: 22px; color: black;'>{summary_text}</p>")
        # 设置布局
        layout = QVBoxLayout(dialog)
        layout.addWidget(text_browser)
        dialog.setLayout(layout)
        dialog.exec_()


if __name__ == '__main__':
    app = QApplication([])
    window = MonKeyWords(DB_PARAMS)
    app.exec_()
