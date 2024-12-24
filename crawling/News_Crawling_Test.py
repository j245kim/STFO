# -*- coding: utf-8 -*-

# 설치가 필요한 라이브러리
# pip install httpx
# pip install beautifulsoup4

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
from concurrent import futures

# 파이썬 서드파티 라이브러리
import httpx
from bs4 import BeautifulSoup


def sync_request(
                url: str, client: httpx.Client, max_retry: int = 10,
                min_delay: int | float = 0.55, max_delay: int | float = 1.55
                 ) -> dict[str, str, httpx.Response, None]:
    """동기로 HTML 문서 정보를 불러오는 함수

    Args:
        url: URL
        client: httpx 동기 클라이언트 객체
        max_retry: HTML 문서 정보 불러오기에 실패했을 때 재시도할 최대 횟수
        min_delay: 재시도 할 때 딜레이의 최소 시간
        max_delay: 재시도 할 때 딜레이의 최대 시간
    
    Return:
        {
            "html": HTML 문서 정보, str | None
            "response_reason": 응답 결과 이유, str | None
            "response_history": 수행된 redirect 응답 목록, list[Response]
        }
    """

    result = {"html": None, "response_reason": None, "response_history": None}

    for _ in range(max_retry):
        # 동기 client로 HTML GET
        response = client.get(url)
        # HTML 문서 정보를 불러오는 것에 성공하면 for문 중단
        if response.status_code == httpx.codes.ok:
            result['html'] = response.text
            break

        # 동기 제어 유지(멀티 프로세싱이라는 전제)
        time.sleep(random.uniform(min_delay, max_delay))
    
    # 응답 요청이 실패했으면 기록 추가
    if result['html'] is None:
        result['response_reason'] = response.reason_phrase
    result['response_history'] = response.history
    
    return result


async def async_request(
                        url: str, client: httpx.AsyncClient, max_retry: int = 10,
                        min_delay: int | float = 0.55, max_delay: int | float = 1.55
                        ) -> dict[str, str, httpx.Response, None]:
    """비동기로 HTML 문서 정보를 불러오는 함수

    Args:
        url: URL
        client: httpx 비동기 클라이언트 객체
        max_retry: HTML 문서 정보 불러오기에 실패했을 때 재시도할 최대 횟수
        min_delay: 재시도 할 때 딜레이의 최소 시간
        max_delay: 재시도 할 때 딜레이의 최대 시간
    
    Return:
        {
            "html": HTML 문서 정보, str | None
            "response_reason": 응답 결과 이유, str | None
            "response_history": 수행된 redirect 응답 목록, list[Response]
        }
    """

    result = {"html": None, "response_reason": None, "response_history": None}

    for _ in range(max_retry):
        # 비동기 client로 HTML GET
        response = await client.get(url)
        # HTML 문서 정보를 불러오는 것에 성공하면 for문 중단
        if response.status_code == httpx.codes.ok:
            result['html'] = response.text
            break

        # 비동기 코루틴 제어 양도
        await asyncio.sleep(random.uniform(min_delay, max_delay))
    
    # 응답 요청이 실패했으면 기록 추가
    if result['html'] is None:
        result['response_reason'] = response.reason_phrase
    result['response_history'] = response.history
    
    return result


async def news_crawling(
                        url:str, category: str, website: str, client: httpx.AsyncClient
                        ) -> dict[str, str, None] | None:
    """뉴스 URL을 바탕으로 크롤링을 하는 함수

    Args:
        url: 뉴스 URL
        category: 뉴스 카테고리
        website: 웹사이트 이름
        client: httpx 비동기 클라이언트 객체

    Returns:
        {
            "news_title": 뉴스 제목, str
            "news_first_upload_time": 뉴스 최초 업로드 시각, str | None
            "news_last_upload_time": 뉴스 최종 수정 시각, str | None
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
    result = await async_request(url=url, client=client)
    # HTML 문서 정보를 불러오는 것에 실패하면 None 반환
    if result['html'] is None:
        return None
    # BeautifulSoup로 parser
    soup = BeautifulSoup(result['html'], 'html.parser')

    match website:
        case 'investing':
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
            first_upload_time = datetime.strptime(first_upload_time, '%Y-%m-%d %p %I:%M')
            first_upload_time = datetime.strftime(first_upload_time, '%Y-%m-%d %H:%M')
            last_upload_time = None
            
            # 3. 뉴스 데이터의 기사 작성자
            author = None

            # 4. 뉴스 데이터의 본문
            content = soup.find('div', id='article')

            # 7. 비고
            note = '해외 사이트'
        case 'hankyung':
            # 1. 뉴스 데이터의 제목
            title = soup.find('h1', {"class": "headline"})
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            upload_times = soup.find_all('span', {"class": "txt-date"})

            first_upload_time = upload_times[0].text
            first_upload_time = datetime.strptime(first_upload_time, '%Y.%m.%d %H:%M')
            first_upload_time = datetime.strftime(first_upload_time, '%Y-%m-%d %H:%M')
            last_upload_time = upload_times[1].text
            last_upload_time = datetime.strptime(last_upload_time, '%Y.%m.%d %H:%M')
            last_upload_time = datetime.strftime(last_upload_time, '%Y-%m-%d %H:%M')

            # 3. 뉴스 데이터의 기사 작성자
            author_list = soup.find_all('div', {"class": "author link subs_author_list"})
            if author_list:
                author_list = map(lambda x: x.find("a").text, author_list)
                author = ', '.join(author_list)
            else:
                author = None

            # 4. 뉴스 데이터의 본문
            content = soup.find("div", id="articletxt")

            # 7. 비고
            note = '국내 사이트'
        case 'bloomingbit':
            pass
        case 'coinreaders':
            pass
        case 'dealsite':
            pass
        case 'blockstreet':
            pass

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


async def investing(
                end_datetime: str, format: str,
                headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                encoding: str = 'utf-8', min_delay: int | float = 0.55, max_delay: int | float = 1.55
                ) -> list[dict[str, str, None]]:
    """investing 사이트를 크롤링 하는 함수

    Args:
        end_datetime: 크롤링할 마지막 시각
        format: 시각 포맷
        headers: 식별 정보
        follow_redirects: 리다이렉트 허용 여부
        timeout: 응답 대기 허용 시간
        encoding: 인코딩 방법
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
    investing_results = []
    page = 0
    end_date = datetime.strptime(end_datetime, format)
    nonstop = True

    while nonstop:
        page += 1

        with httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as sync_client:
            result = sync_request(url=web_page, client=sync_client)
        web_page = f'https://kr.investing.com/news/cryptocurrency-news/{page + 1}'

        # html 문서 불러오기에 실패했으면 다음 페이지로 넘기기
        if result['html'] is None or result['response_reason'] is not None:
            print()
            print(f'{page}번 페이지의 HTML 문서 정보를 불러오는데 실패했습니다.')
            continue
        # redirect를 했으면 최종 페이지까지 갔다는 것이므로 종료
        if result['response_history']:
            nonstop = False
            break

        soup = BeautifulSoup(result['html'], 'html.parser')
        url_tag_list = soup.find_all('article', {"data-test": "article-item"})
        url_list = [url_tag.find('a')["href"] for url_tag in url_tag_list]

        async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as async_client:
            crawl_list = [news_crawling(url=url, category='암호화폐', website='investing', client=async_client) for url in url_list]
            result = await asyncio.gather(*crawl_list)
        
        remove_none = []
        for idx, res in enumerate(result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category=암호화폐, website=investing')
            else:
                remove_none.append(res)

        result = remove_none
        while result and (datetime.strptime(result[-1]['news_first_upload_time'], format) < end_date):
            nonstop = False
            del result[-1]

        investing_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return investing_results



if __name__ == '__main__':
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
    
    result = asyncio.run(investing(end_datetime='2024-11-01 00:00', format='%Y-%m-%d %H:%M', headers=headers))
    print(result[-1])