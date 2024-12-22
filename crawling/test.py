# !pip install httpx
# !pip install beautifulsoup4
# !pip install tqdm

# 파이썬 표준 라이브러리
import os
import json
import re
import random
import time
import asyncio
import logging
import traceback
from datetime import datetime
from functools import partial
from concurrent import futures

# 파이썬 서드파티 라이브러리
import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm


def sync_request(
                url: str, headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                encoding: str = 'utf-8', max_retry: int = 10, min_delay: int | float = 0.55, max_delay: int | float = 1.55
                 ) -> dict[str, str, None]:
    """동기로 HTML 문서 정보를 불러오는 함수

    Args:
        url: URL
        headers: 식별 정보
        follow_redirects: 리다이렉트 허용 여부
        timeout: 응답 대기 허용 시간
        encoding: 인코딩 방법
        max_retry: HTML 문서 정보 불러오기에 실패했을 때 재시도할 최대 횟수
        min_delay: 재시도 할 때 딜레이의 최소 시간
        max_delay: 재시도 할 때 딜레이의 최대 시간
    
    Return:
        {
            "html": HTML 문서 정보, str | None
            "response_reason": 응답 결과 이유, str | None
        }
    """

    result = {"html": None, "response_reason": None}
    client = httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding)

    for _ in range(max_retry):
        # 동기 client로 HTML GET
        response = client.get(url)
        # HTML 문서 정보를 불러오는 것에 성공하면 for문 중단
        if response.status_code == httpx.codes.ok:
            result['html'] = response.text
            break

        # 동기 제어 유지(멀티 프로세싱이라는 전제)
        time.sleep(random.uniform(min_delay, max_delay))
    
    # 응답 요청이 실패했으면 메세지 출력
    if result['html'] is None:
        result['response_reason'] = response.reason_phrase
    
    client.close()
    
    return result


async def async_request(
                url: str, headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                encoding: str = 'utf-8', max_retry: int = 10, min_delay: int | float = 0.55, max_delay: int | float = 1.55
                 ) -> dict[str, str, None]:
    """비동기로 HTML 문서 정보를 불러오는 함수

    Args:
        url: URL
        headers: 식별 정보
        follow_redirects: 리다이렉트 허용 여부
        timeout: 응답 대기 허용 시간
        encoding: 인코딩 방법
        max_retry: HTML 문서 정보 불러오기에 실패했을 때 재시도할 최대 횟수
        min_delay: 재시도 할 때 딜레이의 최소 시간
        max_delay: 재시도 할 때 딜레이의 최대 시간
    
    Return:
        {
            "html": HTML 문서 정보, str | None
            "response_reason": 응답 결과 이유, str | None
        }
    """

    result = {"html": None, "response_reason": None}

    for _ in range(max_retry):
        # 비동기 client로 HTML GET
        async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as client:
            response = await client.get(url)
        # HTML 문서 정보를 불러오는 것에 성공하면 for문 중단
        if response.status_code == httpx.codes.ok:
            result['html'] = response.text
            break

        # 비동기 코루틴 제어 양도
        await asyncio.sleep(random.uniform(min_delay, max_delay))
    
    # 응답 요청이 실패했으면 메세지 출력
    if result['html'] is None:
        result['response_reason'] = response.reason_phrase
    
    return result


async def news_crawling(
                        url:str, category: str, website: str,
                        headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                        encoding: str = 'utf-8', max_retry: int = 10, min_delay: int | float = 0.55, max_delay: int | float = 1.55
                        ) -> dict[str, str, None] | None:
    """뉴스 URL을 바탕으로 크롤링을 하는 함수

    Args:
        url: 뉴스 URL
        category: 뉴스 카테고리
        website: 웹사이트 이름
        headers: 식별 정보
        follow_redirects: 리다이렉트 허용 여부
        timeout: 응답 대기 허용 시간
        encoding: 인코딩 방법
        max_retry: HTML 문서 정보 불러오기에 실패했을 때 재시도할 최대 횟수
        min_delay: 재시도 할 때 딜레이의 최소 시간
        max_delay: 재시도 할 때 딜레이의 최대 시간

    Returns:
        {
            "news_title": 뉴스 제목, str
            "news_first_upload_time": 뉴스 최초 업로드 시각, str | None
            "newsfinal_upload_time": 뉴스 최종 수정 시각, str | None
            "news_author": 뉴스 작성자, str | None
            "news_content": 뉴스 본문, str
            "news_url": 뉴스 URL, str
            "news_category": 뉴스 카테고리, str
            "news_website": 뉴스 웹사이트, str
            "note": 비고, str | None
        }

        or

        None
    """

    info = {} # 뉴스 데이터 정보 Dictionary

    # 비동기로 HTML GET
    result = await async_request(url=url, headers=headers, follow_redirects=follow_redirects, timeout=timeout,
                               encoding=encoding, max_retry=max_retry, min_delay=min_delay, max_delay=max_delay)
    # HTML 문서 정보를 불러오는 것에 실패하면 None 반환
    if result['html'] is None:
        return None
    # BeautifulSoup로 parser
    soup = BeautifulSoup(result['html'], 'html.parser')

    match website:
        case 'inveseting':
            # 1. 뉴스 데이터의 제목
            title = soup.find('h1', id='articleTitle')
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            div = soup.find_all('div', {'class': 'flex flex-row items-center'})
            span = div[1].find('span')
            span = span.text.strip(' \t\n\r\f\v')

            first_upload_time_list = re.split(pattern=r'\s+\r\n\s+', string=span)[1].split()
            y_m_d = '-'.join(times[:-1] for times in first_upload_time_list[:3])
            if first_upload_time_list[3] == '오전':
                ap = 'AM'
            else:
                ap = 'PM'

            first_upload_time = y_m_d + ' ' + ap + ' ' + first_upload_time_list[4]
            last_upload_time = None
            
            # 3. 뉴스 데이터의 기사 작성자
            author = None

            # 4. 뉴스 데이터의 본문
            content = soup.find('div', id='article')
        case 'cryptonews':
            pass
        case 'hankyung':
            # 1. 뉴스 데이터의 제목
            title = soup.find('h1', {"class": "headline"})
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            upload_times = soup.find_all('span', {"class": "txt-date"})

            first_upload_time = upload_times[0].text
            first_upload_time = datetime.strptime(first_upload_time, '%Y.%m.%d %H:%M')
            first_upload_time = datetime.strftime(first_upload_time, '%Y-%m-%d %p %I:%M')
            last_upload_time = upload_times[1].text
            last_upload_time = datetime.strptime(last_upload_time, '%Y.%m.%d %H:%M')
            last_upload_time = datetime.strftime(last_upload_time, '%Y-%m-%d %p %I:%M')

            # 3. 뉴스 데이터의 기사 작성자
            author_list = soup.find_all('div', {"class": "author link subs_author_list"})
            author_list = map(lambda x: x.find("a").text, author_list)
            author = ', '.join(author_list)

            # 4. 뉴스 데이터의 본문
            content = soup.find("div", id="articletxt")
        case 'bloomingbit':
            pass
        case 'coinreaders':
            pass
        case 'dealsite':
            pass
        case 'blockstreet':
            pass
    

    # 7. 비고
    note = None

    info['news_title'] = title
    info['news_first_upload_time'] = first_upload_time
    info['news_last_upload_time'] = last_upload_time
    info['news_author'] = author
    info['news_content'] = content
    info['news_url'] = url
    info['news_category'] = category
    info['news_website'] = website
    info['note'] = note

    return info


async def async_main(
                url_list: list[str], category: str, website: str,
                headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                encoding: str = 'utf-8', max_retry: int = 10, min_delay: int | float = 0.55, max_delay: int | float = 1.55
                ) -> list[dict[str, str, None]]:
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as client:
        crawl_list = [news_crawling(url=url, category=category, website=website, headers=headers) for url in url_list]
        result = asyncio.gather(*crawl_list)
    return result


def investing(
                headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                encoding: str = 'utf-8', max_retry: int = 10, min_delay: int | float = 0.55, max_delay: int | float = 1.55
                ) -> list[dict[str, str, None]]:
    """investing 사이트를 크롤링 하는 함수

    Args:
        headers: 식별 정보
        follow_redirects: 리다이렉트 허용 여부
        timeout: 응답 대기 허용 시간
        encoding: 인코딩 방법
        max_retry: HTML 문서 정보 불러오기에 실패했을 때 재시도할 최대 횟수
        min_delay: 재시도 할 때 딜레이의 최소 시간
        max_delay: 재시도 할 때 딜레이의 최대 시간

    Returns:
        [
            {
                "news_title": 뉴스 제목, str
                "news_first_upload_time": 뉴스 최초 업로드 시각, str | None
                "newsfinal_upload_time": 뉴스 최종 수정 시각, str | None
                "news_author": 뉴스 작성자, str | None
                "news_content": 뉴스 본문, str
                "news_url": 뉴스 URL, str
                "news_category": 뉴스 카테고리, str
                "news_website": 뉴스 웹사이트, str
                "note": 비고, str | None
            },
            {
                                    ...
            },
                                    .
                                    .
                                    .
        ]
    """

    web_page = 'https://kr.investing.com/news/cryptocurrency-news'
    start = 1
    get_page_cnt = 30
    end = start + get_page_cnt

    investing_results = []

    for i in tqdm(range(start, end), mininterval=1, miniters=1):
        result = sync_request(url=web_page, headers=headers)

        if result['html'] is None:
            print()
            print(f'{i}번 페이지의 HTML 문서 정보를 불러오는데 실패했습니다.')
            print(traceback.format_exc())
            web_page = f'https://kr.investing.com/news/cryptocurrency-news/{i + 1}'
            continue

        soup = BeautifulSoup(result['html'], 'html.parser')
        url_tag_list = soup.find_all('article', {"data-test": "article-item"})
        url_list = [url["href"] for url_tag in url_tag_list if ((url := url_tag.find('a')) is not None)]
        result = asyncio.run(async_main(url_list, category='암호화폐', website='investing', headers=headers))
        investing_results.extend(result)

        time.sleep(random.uniform(min_delay, max_delay))
        web_page = f'https://kr.investing.com/news/cryptocurrency-news/{i + 1}'
    
    return investing_results


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


result = investing(headers=headers)

print(result)
print(len(result))