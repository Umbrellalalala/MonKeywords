# -*- coding: utf-8 -*-
"""
@Time: 2024/12/8 18:06
@Auth: Zhang Hongxing
@File: news_spider.py
@Note:   
"""
import datetime
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin
import scrapy
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from scrapy_project.items import NewsItem


class NewsSpider(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        super(NewsSpider, self).__init__(*args, **kwargs)
        self.start_time, self.end_time = self.get_period(kwargs.get('new_start_time'), kwargs.get('new_end_time'))

    @staticmethod
    def get_period(new_start_time, new_end_time):
        start_time = new_start_time
        end_time = new_end_time
        if start_time is None or end_time is None:
            print("未获取到时间，使用默认值")
            start_time = datetime(2014, 1, 1) - relativedelta(days=1)
            end_time = datetime.now()
            # end_time = start_time + relativedelta(months=1)
        if end_time > datetime.now():
            end_time = datetime.now()
        formatted_start_time = start_time.strftime("%Y-%m-%d")
        formatted_end_time = end_time.strftime("%Y-%m-%d")
        return formatted_start_time, formatted_end_time

    name = "news_spider"
    start_urls = ["https://www.people.com.cn"]

    # @staticmethod
    # def get_period():
    #     start_time = datetime(2020, 1, 1) - relativedelta(days=1)
    #     end_time = datetime.now()
    #     # end_time = start_time + relativedelta(months=1)
    #     if end_time > datetime.now():
    #         end_time = datetime.now()
    #     formatted_start_time = start_time.strftime("%Y-%m-%d")
    #     formatted_end_time = end_time.strftime("%Y-%m-%d")
    #     return formatted_start_time, formatted_end_time
    # start_time, end_time = get_period()

    def parse(self, response):
        print('-'*10 + "开始爬虫：" + self.start_time, ' -> ', self.end_time + '-'*10 )
        start_url = "https://www.people.com.cn/GB/59476/review/" + self.start_time.replace('-', '') + '.html'
        yield scrapy.Request(url=start_url, callback=self.parse_pages)

    def parse_pages(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        news_list = soup.find_all('li')
        for i in range(0, len(news_list)):
            news = news_list[i].find('a')
            try:
                href = str(news['href'])
                response.meta['url'] = href
                absolute_url = urljoin(response.url, href)  # 使用urljoin构建绝对URL
                print(href)
                yield scrapy.Request(url=absolute_url, callback=self.parse_news, meta=response.meta)
            except:
                print("pass")
                pass

        current_time = datetime.strptime(self.start_time, "%Y-%m-%d") + timedelta(days=1)
        formatted_current_time = current_time.strftime("%Y-%m-%d")
        self.start_time = formatted_current_time
        if current_time <= datetime.strptime(self.end_time, "%Y-%m-%d"):
            # 跳过2016-10-21到2016-10-23的数据
            if formatted_current_time == '2016-10-21' or formatted_current_time == '2016-10-22' or formatted_current_time == '2016-10-23':
                formatted_current_time = '2016-10-24'
            next_page = "https://www.people.com.cn/GB/59476/review/" + formatted_current_time.replace('-', '') + '.html'
            print(next_page)
            yield scrapy.Request(url=next_page, callback=self.parse_pages)

    @staticmethod
    def clean_special_characters(input_string):
        # 使用正则表达式去掉所有非中文、英文、数字、标点符号的特殊字符
        cleaned_string = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.,;，。？！……!?]+', '', input_string)
        return cleaned_string

    def parse_news(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            head = soup.find('title').text.split('--')
            category = head[1]
            title = head[0]
            if '/n1/' in response.meta['url']:
                temp_time = response.meta['url'].split('/n1/')[1].split('/')
                pub_time = temp_time[0] + '-' + temp_time[1][:2] + '-' + temp_time[1][2:4]
            elif '/review/' in response.meta['url']:
                temp_time = response.meta['url'].split('/review/')[1].split('.html')[0]
                pub_time = temp_time[:4] + '-' + temp_time[4:6] + '-' + temp_time[6:]
            else:
                pass
            # print("pub_time: ", pub_time)
            if datetime.strptime(pub_time, "%Y-%m-%d") <= datetime.strptime(self.end_time, "%Y-%m-%d"):
                p_list = soup.find_all('p')
                body = ""
                for i in range(1, len(p_list)):
                    p = p_list[i].text
                    if '分享让更多人看到' not in p and '《 人民日报 》' not in p and '关于人民网|' not in p and '人民日报社概况' not in p:
                        body += p.strip()
                    else:
                        break
                item = NewsItem()
                item['url'] = response.meta['url']
                item['category'] = category
                item['title'] = title
                item['pub_time'] = pub_time
                item['body'] = self.clean_special_characters(body.replace('忘记密码？', ''))
                if len(body) > 20:
                    # print(item)
                    yield item
        except Exception:
            pass

# cmdline.execute("scrapy crawl news_spider".split())
