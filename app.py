# -*- coding: utf-8 -*-

# 파이썬 표준 라이브러리
import os

# 사용자 정의 라이브러리
from crawling_scraping_core import crawling_scraping





if __name__ == '__main__':
    # 현재 'Crawling_App.py'가 있는 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = current_dir + r'\logs'
    crawling_log_dir = current_dir + r'\logs\crawling_log'
    data_dir = current_dir + r'\datas'
    news_data_dir = current_dir + r'\datas\news_data'

    # logs 폴더가 없으면 logs 폴더와 그 하위 폴더로 crwaling_log 폴더 생성
    if not os.path.exists(logs_dir):
        os.makedirs(crawling_log_dir, exist_ok=True)
    # logs 폴더는 있지만 crawling_log 폴더가 없으면 crawling_log 폴더 생성
    elif not os.path.exists(crawling_log_dir):
        os.mkdir(crawling_log_dir)
    # datas 폴더가 없으면 datas 폴더와 그 하위 폴더로 news_data 폴더 생성
    if not os.path.exists(data_dir):
        os.makedirs(news_data_dir, exist_ok=True)
    # datas 폴더는 있지만 newsdata 폴더가 없으면 news_data 폴더 생성
    elif not os.path.exists(news_data_dir):
        os.mkdir(news_data_dir)
    


    cs = crawling_scraping.CrawlingScraping()
    cs.add_website('hankyung')
    cs.add_website('bloomingbit')
    cs.add_website('coinreaders')
    cs.add_website('blockstreet')

    end_datetime, date_format = '2024-12-31 00:00', '%Y-%m-%d %H:%M'

    result = cs.run(end_datetime=end_datetime, date_format=date_format)
    cs.to_json()