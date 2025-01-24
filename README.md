### 使用说明

1. 打开mysql，导入程序使用的数据集（monkeyword_news.sql）
2. 用pycharm等IDE打开项目（MonKeyWords）
3. 加载虚拟环境后，在终端输入pip install -r requirements.txt，以安装依赖包
4. 运行main.py以启动用户界面
5. 点击用户界面底部的“用户指引”可以看到具体的操作指南

### 项目结构

MonKeyWords/
├── config/
│   ├── config.py                 # 项目配置信息
│
├── scrapy_project/               # Scrapy框架相关
│   ├── scrapy_project/           # Scrapy项目的模块
│   │   ├── spiders/              # 爬虫代码
│   │   │   ├── __init__.py       # 标识为Python包
│   │   │   ├── news_spider.py    # 实现新闻爬虫
│   │   ├── __init__.py           # 标识为Python包
│   │   ├── items.py              # 定义数据结构
│   │   ├── middlewares.py        # 定义中间件
│   │   ├── pipelines.py          # 定义管道
│   │   ├── settings.py           # 项目设置
│   ├── scrapy.cfg                # Scrapy配置文件
│
├── src/                          # 主要功能模块
│   ├── data_storage/             # 数据存储模块
│   │   ├── __init__.py           # 标识为Python包
│   │   ├── database.py           # 提供数据库操作功能
│   │   ├── models.py             # 定义数据库模型
│   │
│   ├── services/                  # 业务逻辑模块
│   │   ├── __init__.py           # 标识为Python包
│   │   ├── crawl_service.py      # 爬虫相关业务逻辑
│   │   ├── news_service.py       # 新闻相关的业务逻辑
│   │   ├── keyword_service.py    # 关键词提取相关业务逻辑
│   │
│   ├── text_processing/          # 文本处理模块
│   │   ├── __init__.py           # 标识为Python包
│   │   ├── tokenizer.py          # 分词功能
│   │   ├── keyword_extraction.py # 关键词提取功能
│   │
│   ├── user_interface/           # 用户界面模块
│   │   ├── __init__.py           # 标识为Python包
│   │   ├── main_window.py        # PyQt的主窗口类
│   │   ├── views.py              # 用户界面逻辑
│
├── utils/                        # 项目中的辅助资源
│   ├── stop_words/               # 停用词文件
│   ├── word_dict/                # 词典文件
│   ├── remove_keywords_list/     # 需移除关键词文件
│
├── main.py                       # 项目入口文件
├── requirements.txt              # 依赖库清单
└── README.md                     # 项目说明文档
