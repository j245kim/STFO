import httpx
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

url = 'https://www.blockstreet.co.kr/news/view?ud=2024121314424347693'


with httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding, limits=httpx.Limits(max_keepalive_connections=150, max_connections=150)) as client:
    response = client.get(url=url)

html = response.text
soup = BeautifulSoup(html, 'html.parser')

title = soup.find('h1', {"class": "headline"})
title = title.text.strip(' \t\n\r\f\v')

date_time = soup.find("div", {"class": "datetime"})
date_time = date_time.find_all("span")
first_upload_time = None
last_upload_time = None
for span in date_time:
    span = span.text.split()
    if span[0] == '등록':
        first_upload_time = f'{span[1]} {span[2]}'
    elif span[0] == '수정':
        last_upload_time = f'{span[1]} {span[2]}'

author_list = soup.find("div", {"class": "byline"})
author_list = author_list.find_all("span")
if author_list:
    author_list = map(lambda x: x.find('a').text, author_list)
    author = ', '.join(author_list)
else:
    author = None

content = soup.find("div", {"class": "view-body fs3"})
content = content.prettify()

print(title)
print(first_upload_time)
print(last_upload_time)
print(author)
print(content)