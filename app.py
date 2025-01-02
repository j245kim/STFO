# -*- coding: utf-8 -*-


# 사용자 정의 라이브러리
from crawling_scraping_core import crawling_scraping





if __name__ == '__main__':
    cs = crawling_scraping.CrawlingScraping(record_log=True)
    cs.add_website('hankyung')
    cs.add_website('bloomingbit')
    cs.add_website('coinreaders')
    cs.add_website('blockstreet')

    end_datetime, date_format = '2025-01-01 00:00', '%Y-%m-%d %H:%M'

    result = cs.run(end_datetime=end_datetime, date_format=date_format)
    cs.to_json()