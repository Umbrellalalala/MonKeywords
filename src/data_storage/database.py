# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 17:51
@Auth: Zhang Hongxing
@File: database.py
@Note:   
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data_storage.models import Base


class Database:
    def __init__(self, db_params):
        self.engine = create_engine(
            f"mysql+pymysql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def dispose_connection(self):
        self.engine.dispose()
