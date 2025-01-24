# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 17:51
@Auth: Zhang Hongxing
@File: main.py
@Note:   
"""
from PyQt5.QtWidgets import QApplication
from Mysql.db_config import DB_PARAMS
from src.user_interface.main_window import MonKeyWords

if __name__ == '__main__':
    app = QApplication([])
    window = MonKeyWords(DB_PARAMS)
    app.exec_()
