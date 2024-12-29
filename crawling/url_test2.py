import re
from News_Crawling_Test import sync_request
from httpx import Client
from bs4 import BeautifulSoup

# User-Agent 변경을 위한 옵션 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
headers = {
            'User-Agent': user_agent
        }

# client 파라미터
follow_redirects = True # 리다이렉트 허용 여부
timeout = 90 # 응답 대기 허용 시간
encoding = 'utf-8'
max_retry = 10 # HTML 문서 요청 최대 재시도 횟수
min_delay = 0.55 # 재시도 할 때 딜레이의 최소 시간
max_delay = 1.55 # 재시도 할 때 딜레이의 최대 시간

url = 'https://www.coinreaders.com/138622'

client = Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding)
response = client.get(url)

html = response.text
soup = BeautifulSoup(html, 'html.parser')

title = soup.find("h1", {"class": "read_title"})
title = title.text.strip(' \t\n\r\f\v')

date_time = soup.find("div", {"class": "writer_time"})
*_, _date, _time = date_time.text.split()
_date = _date.replace(r'/', '-')
_time = re.sub(pattern=r'\[|\]', repl='', string=_time)
date_time = f'{_date} {_time}'

author = soup.find("span", {"class": "writer"})
author = author.text

content = soup.find("div", id='textinput')
content = content.prettify()

print(title)
print(date_time)
print(author)
print(content)