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

url = 'https://bloomingbit.io/ko/feed/news/80611'
response = clinet.get(url)

html = response.text
soup = BeautifulSoup(html, 'html.parser')

title = soup.find("h1", {"class": "_feedDetailContet_newsContentTitle__ftCYu"})
title = title.text.strip(' \t\n\r\f\v')

first_upload_time_list = soup.find("span", {"class": "_feedReporterWithDatePublished_createDate__pphI_"})
first_upload_time_list = first_upload_time_list.text
first_upload_time_list = first_upload_time_list.replace('.', '')
first_upload_time_list = first_upload_time_list.split()[1:]
last_upload_time_list = soup.find("span", {"class": "_feedReporterWithDatePublished_updateDate__xCxls"})
last_upload_time_list = last_upload_time_list.text
last_upload_time_list = last_upload_time_list.replace('.', '')
last_upload_time_list = last_upload_time_list.split()[1:]

print(first_upload_time_list)
print(last_upload_time_list)

# category = soup.find("h3", {"class": "_feedType_feedTypeLabel__DQpII"})

# if category is not None:
#     category.text
# else:
#     category