# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 21:28
@Auth: Zhang Hongxing
@File: db_helpers.py
@Note:   
"""
import re
from contextlib import contextmanager
from src.data_storage.models import News


@contextmanager
def get_session(db):
    """上下文管理器"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_existing_times(db):
    with get_session(db) as session:
        return session.query(News.pub_time).distinct().all()


def get_news_by_keyword_and_time(db, keyword, start_time, end_time):
    with get_session(db) as session:
        return session.query(News).filter(
            News.pub_time >= start_time,
            News.pub_time < end_time,
            News.keywords.op('REGEXP')(fr'\b{re.escape(keyword)}\b')
        ).all()
