from sqlalchemy import Column, Integer, String, DateTime, Text, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class News(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True)
    url = Column(String(255))
    category = Column(String(255))
    title = Column(String(255))
    pub_time = Column(DateTime)
    body = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())
    is_delete = Column(Integer, default=0)

class Keywords(Base):
    __tablename__ = 'keywords'

    id = Column(Integer, primary_key=True)
    news_id = Column(Integer, ForeignKey('news.id'))
    algorithm = Column(String(255))
    keywords = Column(Text)
    keywords_num = Column(Integer)
    created_at = Column(TIMESTAMP, default=func.now())
    is_delete = Column(Integer, default=0)
    news = relationship("News", backref="keywords")

class Cloud(Base):
    __tablename__ = 'cloud'

    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    month = Column(Integer)
    category = Column(String(255))
    keywords_num = Column(Integer)
    algorithm = Column(String(255))
    cloud_url = Column(String(255))
    created_at = Column(TIMESTAMP, default=func.now())
    is_delete = Column(Integer, default=0)

class Summary(Base):
    __tablename__ = 'summary'

    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    month = Column(Integer)
    category = Column(String(255))
    keywords_num = Column(Integer)
    keyword = Column(String(255))
    algorithm = Column(String(255))
    summary = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())
    is_delete = Column(Integer, default=0)
