# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 21:28
@Auth: Zhang Hongxing
@File: url_helpers.py
@Note:   
"""

import webbrowser
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

def open_url_in_browser(url):
    if url:
        QDesktopServices.openUrl(QUrl(url), QUrl.TolerantMode)
    else:
        webbrowser.open(url)
