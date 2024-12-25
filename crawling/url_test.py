import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

# User-Agent 변경을 위한 옵션 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
headers = {'User-Agent': user_agent}

# client 파라미터
follow_redirects = True # 리다이렉트 허용 여부
timeout = 90 # 응답 대기 허용 시간
encoding = 'utf-8'
max_retry = 10 # HTML 문서 요청 최대 재시도 횟수
min_delay = 0.55 # 재시도 할 때 딜레이의 최소 시간
max_delay = 1.55 # 재시도 할 때 딜레이의 최대 시간

clinet = httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding)

url = 'https://cryptonews.com/kr/news/south-korean-crypto-exchange-upbit-to-delist-bitcoin-gold/'
response = clinet.get(url)

html = response.text

soup = BeautifulSoup(html, 'html.parser')

# 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
last_upload_time = soup.find("div", {"class": "single-post-new__author-top"})
last_upload_time = last_upload_time.find("time")
last_upload_time = last_upload_time.text

date_time = re.sub(pattern=r'[월,]', repl='', string=last_upload_time)
m, d, y, hm = date_time.split()[:-1]
print(f'{y}-{m}-{d} {hm}')