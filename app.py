# -*- coding: utf-8 -*-
"""
@Time: 2024/12/24 13:39
@Auth: Zhang Hongxing
@File: app.py
@Note:   
"""

from flask import Flask, send_from_directory, jsonify
import os
from wordcloud import WordCloud
import seaborn as sns
import matplotlib.pyplot as plt
from src.user_interface.views import MonKeyWordsViews
app = Flask(__name__)

# 静态文件目录
app.config['UPLOAD_FOLDER'] = 'static/wordclouds'

# 用于展示静态文件的URL映射
@app.route('/wordclouds/<filename>')
def serve_wordcloud(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
