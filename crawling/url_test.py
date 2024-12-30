import time
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

# User-Agent 변경을 위한 옵션 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
headers = {'User-Agent': user_agent, "Referer": "https://cryptonews.com/kr/"}

# client 파라미터
follow_redirects = True # 리다이렉트 허용 여부
timeout = 90 # 응답 대기 허용 시간
encoding = 'utf-8'
max_retry = 10 # HTML 문서 요청 최대 재시도 횟수
min_delay = 0.55 # 재시도 할 때 딜레이의 최소 시간
max_delay = 1.55 # 재시도 할 때 딜레이의 최대 시간

# clinet = httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding)

# url = 'https://cryptonews.com/kr/'
# response = clinet.get(url)

# # html = response.text

# # soup = BeautifulSoup(html, 'html.parser')

# # content = soup.find("div", id="article")
# # content = content.prettify()

# print(response.status_code)
# print(response.reason_phrase)
# print(response.history)


# ----------------------
# import os
# os.environ['PYPPETEER_CHROMIUM_REVISION'] = '1300991'

# from requests_html import HTMLSession

# # 세션 생성
# session = HTMLSession()


# # 대상 URL 요청
# url = 'https://kr.investing.com/news/cryptocurrency-news/article-1314996'
# response = session.get(url)

# # 자바스크립트 실행
# response.html.render()  # 렌더링 시간 조정 가능

# # HTML 파싱
# soup = BeautifulSoup(response.html.html, 'html.parser')

# # 원하는 태그 가져오기
# data = soup.find("div", id="article")  # 예: div 태그 가져오기
# print(data)

# -----------------------
from playwright.sync_api import sync_playwright

url = "https://bloomingbit.io/ko/feed"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    page.get_by_role("button", name="PiCK").click()
    html_content = page.content()
    time.sleep(5)
    browser.close()

print(html_content)
