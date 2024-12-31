# -*- coding: utf-8 -*-

# 설치가 필요한 라이브러리
# pip install httpx
# pip install beautifulsoup4
# pip install pytest-playwright
# 반드시 https://playwright.dev/python/docs/intro 에서 Playwright 설치 관련 가이드 참고

# 파이썬 표준 라이브러리
import os
import json
import re
import random
import time
import asyncio
import logging
import traceback
from copy import deepcopy
from datetime import datetime
from functools import partial
from concurrent import futures

# 파이썬 서드파티 라이브러리
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


def datetime_trans(
                    website: str,
                   date_time: str, date_format: str = '%Y-%m-%d %H:%M'
                   ) -> str:
    """웹사이트에 따른 업로드 시각, 수정 시각들을 같은 포맷으로 바꾸는 함수

    Args:
        website: 웹사이트 이름
        date_time: 바꿀 시각
        date_format: 바꾸는 포맷
    
    Return:
        2000-01-01 23:59 형태의 str 포맷, 단 포맷은 사용자가 지정 가능
    """
        
    match website:
        case 'investing':
            _, y, m, d, ap, hm = re.split(pattern=r'-?\s+', string=date_time)
            if ap == '오전':
                ap = 'AM'
            else:
                ap = 'PM'
            news_datetime = f'{y}-{m}-{d} {ap} {hm}'
            news_datetime = datetime.strptime(news_datetime, '%Y-%m-%d %p %I:%M')
        case 'hankyung':
            news_datetime = date_time.replace('.', '-')
            news_datetime = datetime.strptime(news_datetime, '%Y-%m-%d %H:%M')
        case 'bloomingbit':
            _, y, m, d, ap, hm = re.split(pattern=r'\.?\s+', string=date_time)
            if ap == '오전':
                ap = 'AM'
            else:
                ap = 'PM'
            news_datetime = f'{y}-{m}-{d} {ap} {hm}'
            news_datetime = datetime.strptime(news_datetime, '%Y-%m-%d %p %I:%M')
        case 'coinreaders':
            *_, _date, _time = date_time.split()
            _date = _date.replace(r'/', '-')
            _time = re.sub(pattern=r'\[|\]', repl='', string=_time)
            news_datetime = f'{_date} {_time}'
            news_datetime = datetime.strptime(news_datetime, '%Y-%m-%d %H:%M')
        case 'blockstreet':
            news_datetime = datetime.strptime(date_time, '%Y-%m-%d %H:%M')

    news_datetime = datetime.strftime(news_datetime, date_format)

    return news_datetime


def datetime_cut(
                news_list: list[dict[str, str, None]],
                end_date: datetime, date_format: str = '%Y-%m-%d %H:%M'
                ) -> dict[str, list[dict[str, str, None]], bool]:
    """end_date보다 빠른 날짜의 데이터들을 제거하는 함수

    Args:
        news_list: 크롤링 및 스크래핑한 뉴스 데이터들
        end_date: 기준 시각
        date_format: 날짜 포맷
    
    Returns
        {
            "result": 자르기 완료한 크롤링 및 스크래핑한 뉴스 데이터들, list[dict[str, str, None]]
            "nonstop": 진행 여부 부울 변수, bool
        }
    """
    
    info = {"result": deepcopy(news_list), 'nonstop': True}

    while info['result'] and (datetime.strptime(info['result'][-1]['news_first_upload_time'], date_format) < end_date):
            info['nonstop'] = False
            del info['result'][-1]

    return info


def sync_request(
                url: str, headers: dict[str, str], follow_redirects: bool = True,
                timeout: int | float = 90, encoding: str = 'utf-8', max_retry: int = 10,
                min_delay: int | float = 0.55, max_delay: int | float = 1.55
                 ) -> dict[str, int, str, httpx.Response, None]:
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
            "response_status_code": 응답 코드, int
            "response_reason": 응답 결과 이유, str
            "response_history": 수행된 redirect 응답 목록, list[Response]
        }
    """

    result = {"html": None, "response_status_code": None, "response_reason": None, "response_history": None,
              "error_type": None}

    with httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding, limits=httpx.Limits(max_keepalive_connections=150, max_connections=150)) as client:
        for _ in range(max_retry):
            try:
                # 동기 client로 HTML GET
                response = client.get(url)
                # 응답 기록 추가
                result['response_status_code'] = response.status_code
                result['response_reason'] = response.reason_phrase
                result['response_history'] = response.history
                # HTML 문서 정보를 불러오는 것에 성공하면 for문 중단
                if response.status_code == httpx.codes.ok:
                    result['html'] = response.text
                    break

                # 동기 제어 유지(멀티 프로세싱이라는 전제)
                time.sleep(random.uniform(min_delay, max_delay))
            except Exception as e:
                print()
                print(f'{url}에서 {type(e).__name__}가 발생했습니다.')
                # 응답 기록 추가
                result['response_status_code'] = None
                result['response_reason'] = None
                result['response_history'] = None
                result['error_type'] = type(e).__name__
    
    return result


async def async_request(
                        url: str, headers: dict[str, str], follow_redirects: bool = True,
                        timeout: int | float = 90, encoding: str = 'utf-8', max_retry: int = 10,
                        min_delay: int | float = 0.55, max_delay: int | float = 1.55
                        ) -> dict[str, int, str, httpx.Response, None]:
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
            "response_status_code": 응답 코드, int
            "response_reason": 응답 결과 이유, str
            "response_history": 수행된 redirect 응답 목록, list[Response]
        }
    """

    result = {"html": None, "response_status_code": None, "response_reason": None, "response_history": None,
              'error_type': None}

    async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding, limits=httpx.Limits(max_keepalive_connections=200, max_connections=200)) as client:
        for _ in range(max_retry):
            try:
                # 비동기 client로 HTML GET
                response = await client.get(url)
                # 응답 기록 추가
                result['response_status_code'] = response.status_code
                result['response_reason'] = response.reason_phrase
                result['response_history'] = response.history
                # HTML 문서 정보를 불러오는 것에 성공하면 for문 중단
                if response.status_code == httpx.codes.ok:
                    result['html'] = response.text
                    break

                # 비동기 코루틴 제어 양도
                await asyncio.sleep(random.uniform(min_delay, max_delay))
            except Exception as e:
                print()
                print(f'{url}에서 {type(e).__name__}가 발생했습니다.')
                # 응답 기록 추가
                result['response_status_code'] = None
                result['response_reason'] = None
                result['response_history'] = None
                result['error_type'] = type(e).__name__
    
    return result


async def news_crawling(
                        url:str, category: str, website: str, headers: dict[str, str],
                        max_retry: int = 10, min_delay: int | float = 0.55, max_delay: int | float = 1.55
                        ) -> dict[str, str, None] | None:
    """뉴스 URL을 바탕으로 크롤링을 하는 함수

    Args:
        url: 뉴스 URL
        category: 뉴스 카테고리
        website: 웹사이트 이름
        headers: 식별 정보
        max_retry: HTML 문서 정보 불러오기에 실패했을 때 재시도할 최대 횟수
        min_delay: 재시도 할 때 딜레이의 최소 시간
        max_delay: 재시도 할 때 딜레이의 최대 시간

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
    result = await async_request(url=url, headers=headers, max_retry=max_retry, min_delay=min_delay, max_delay=max_delay)
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
            first_upload_time = span.text.strip(' \t\n\r\f\v')
            first_upload_time = datetime_trans(website=website, date_time=first_upload_time)
            last_upload_time = None
            
            # 3. 뉴스 데이터의 기사 작성자
            author = None

            # 4. 뉴스 데이터의 본문
            content = soup.find('div', id='article')
            content = content.prettify()

            # 8. 비고
            note = '해외 사이트'
        case 'hankyung':
            # 1. 뉴스 데이터의 제목
            title = soup.find('h1', {"class": "headline"})
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            upload_times = soup.find_all('span', {"class": "txt-date"})

            first_upload_time = upload_times[0].text
            first_upload_time = datetime_trans(website=website, date_time=first_upload_time)
            last_upload_time = upload_times[1].text
            last_upload_time = datetime_trans(website=website, date_time=last_upload_time)


            # 3. 뉴스 데이터의 기사 작성자
            author_list = soup.find_all('div', {"class": "author link subs_author_list"})
            if author_list:
                author_list = map(lambda x: x.find("a").text, author_list)
                author = ', '.join(author_list)
            else:
                author = None

            # 4. 뉴스 데이터의 본문
            content = soup.find("div", id="articletxt")
            content = content.prettify()

            # 8. 비고
            note = '국내 사이트'
        case 'bloomingbit':
            # 1. 뉴스 데이터의 제목
            title = soup.find("h1", {"class": "_feedDetailContet_newsContentTitle__ftCYu"})
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            first_upload_time = soup.find("span", {"class": "_feedReporterWithDatePublished_createDate__pphI_"})
            if first_upload_time is not None:
                first_upload_time = first_upload_time.text
                first_upload_time = datetime_trans(website=website, date_time=first_upload_time)
            last_upload_time = soup.find("span", {"class": "_feedReporterWithDatePublished_updateDate__xCxls"})
            if last_upload_time is not None:
                last_upload_time = last_upload_time.text
                last_upload_time = datetime_trans(website=website, date_time=last_upload_time)
            
            # 3. 뉴스 데이터의 기사 작성자
            author_list = soup.find_all('span', {"class": "_feedReporterWithDatePublished_newsReporter__nRjik"})
            if author_list:
                author_list = map(lambda x: x.text, author_list)
                author = ', '.join(author_list)
            else:
                author = None
            
            # 4. 뉴스 데이터의 본문
            content = soup.find("div", {"class": "_feedMainContent_feedDetailArticle__B_0Sy _feedMainContent_markdown__s5mjo"})
            content = content.prettify()

            # 7. 뉴스 category
            category = soup.find("h3", {"class": "_feedType_feedTypeLabel__DQpII"})
            if category is None:
                category = '전체 뉴스'
            else:
                category = category.text

            # 8. 비고
            note = '국내 사이트'
        case 'coinreaders':
            # 1. 뉴스 데이터의 제목
            title = soup.find("h1", {"class": "read_title"})
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            first_upload_time = soup.find("div", {"class": "writer_time"})
            first_upload_time = first_upload_time.text
            first_upload_time = datetime_trans(website=website, date_time=first_upload_time)
            last_upload_time = None

            # 3. 뉴스 데이터의 기사 작성자
            author_tag = soup.find("div", {"class": "writer_time"})
            author_list = author_tag.find_all("span", {"class": "writer"})
            if author_list:
                author_list = map(lambda x: x.text.strip(), author_list)
                author = ', '.join(author_list)
            else:
                author = None

            # 4. 뉴스 데이터의 본문
            content = soup.find("div", id='textinput')
            content = content.prettify()

            # 8. 비고
            note = '국내 사이트'
        case 'blockstreet':
            # 1. 뉴스 데이터의 제목
            title = soup.find('h1', {"class": "headline"})
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            date_time = soup.find("div", {"class": "datetime"})
            date_time = date_time.find_all("span")
            first_upload_time = None
            last_upload_time = None
            for span in date_time:
                span = span.text.split()
                if span[0] == '등록':
                    first_upload_time = f'{span[1]} {span[2]}'
                    first_upload_time = datetime_trans(website=website, date_time=first_upload_time)
                elif span[0] == '수정':
                    last_upload_time = f'{span[1]} {span[2]}'
                    last_upload_time = datetime_trans(website=website, date_time=last_upload_time)

            # 3. 뉴스 데이터의 기사 작성자
            author_list = soup.find("div", {"class": "byline"})
            author_list = author_list.find_all("span")
            if author_list:
                author_list = map(lambda x: x.find('a').text, author_list)
                author = ', '.join(author_list)
            else:
                author = None

            # 4. 뉴스 데이터의 본문
            content = soup.find("div", {"class": "view-body fs3"})
            content = content.prettify()

            # 8. 비고
            note = '국내 사이트'

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


async def async_crawling(
                        url_list: list[str], category: str, website: str, headers: dict[str, str],
                        min_delay: int | float = 0.55, max_delay: int | float = 1.55
                        ) -> list[dict[str, str, None], None]:
    """비동기로 뉴스 URL들을 크롤링하는 함수

    Args:
        url_list: 뉴스 URL list
        category: 뉴스 카테고리
        website: 웹사이트 이름
        headers: 식별 정보
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

    if url_list:
        crawl_list = [news_crawling(url=url, category=category, website=website, headers=headers, min_delay=min_delay, max_delay=max_delay) for url in url_list]
        async_result = await asyncio.gather(*crawl_list)
        return async_result
    return []


async def investing(
                    end_datetime: str, date_format: str, headers: dict[str, str],
                    min_delay: int | float = 0.55, max_delay: int | float = 1.55
                    ) -> list[dict[str, str, None]]:
    """investing 사이트를 크롤링 하는 함수

    Args:
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷
        headers: 식별 정보
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

    page = 1
    web_page = 'https://kr.investing.com/news/cryptocurrency-news'
    category = '암호화폐'
    website = 'investing'
    end_date = datetime.strptime(end_datetime, date_format)
    nonstop = True
    investing_results = []

    while nonstop:
        sync_result = sync_request(url=web_page, headers=headers)
        page += 1
        web_page = f'https://kr.investing.com/news/cryptocurrency-news/{page}'

        # redirect를 했으면 최종 페이지까지 갔다는 것이므로 종료
        if sync_result['response_history']:
            nonstop = False
            break
        # html 문서 불러오기에 실패했으면 다음 페이지로 넘기기
        if sync_result['html'] is None or sync_result['response_reason'] != 'OK':
            print()
            print(f'{page}번 페이지의 HTML 문서 정보를 불러오는데 실패했습니다.')
            continue

        soup = BeautifulSoup(sync_result['html'], 'html.parser')
        url_tag_list = soup.find_all('article', {"data-test": "article-item"})
        url_list = [url_tag.find('a')["href"] for url_tag in url_tag_list]

        async_result = await async_crawling(url_list=url_list, category=category, website=website, headers=headers)
        
        # 요청이 실패했으면 제외
        result = []
        for idx, res in enumerate(async_result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
            else:
                result.append(res)

        # end_date 이후가 아니면은 제거
        cut_info = datetime_cut(news_list=result, end_date=end_date, date_format=date_format)
        result, nonstop = cut_info['result'], cut_info['nonstop']

        investing_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return investing_results


async def hankyung(
                    end_datetime: str, date_format: str, headers: dict[str, str],
                    min_delay: int | float = 0.55, max_delay: int | float = 1.55
                    ) -> list[dict[str, str, None]]:
    """hankyung 사이트를 크롤링 하는 함수

    Args:
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷
        headers: 식별 정보
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

    page = 1
    web_page = f'https://www.hankyung.com/koreamarket/news/crypto?page={page}'
    category = '암호화폐'
    website = 'hankyung'
    end_date = datetime.strptime(end_datetime, date_format)
    nonstop = True
    hankyung_results = []

    while nonstop:
        sync_result = sync_request(url=web_page, headers=headers)
        page += 1
        web_page = f'https://www.hankyung.com/koreamarket/news/crypto?page={page}'
        
        # html 문서 불러오기에 실패했으면 다음 페이지로 넘기기
        if sync_result['html'] is None or sync_result['response_reason'] != 'OK':
            print()
            print(f'{page}번 페이지의 HTML 문서 정보를 불러오는데 실패했습니다.')
            continue

        soup = BeautifulSoup(sync_result['html'], 'html.parser')
        url_tag_list = soup.find_all('h2', {"class": "news-tit"})

        # url_tag_list가 비어있으면 최종 페이지까지 갔다는 것이므로 종료
        if not url_tag_list:
            nonstop = False
            break

        url_list = [url_tag.find('a')["href"] for url_tag in url_tag_list]

        async_result = await async_crawling(url_list=url_list, category=category, website=website, headers=headers)
        
        # 요청이 실패했으면 제외
        result = []
        for idx, res in enumerate(async_result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
            else:
                result.append(res)
        
        # end_date 이후가 아니면은 제거
        cut_info = datetime_cut(news_list=result, end_date=end_date, date_format=date_format)
        result, nonstop = cut_info['result'], cut_info['nonstop']

        hankyung_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return hankyung_results


async def bloomingbit(
                    end_datetime: str, date_format: str, headers: dict[str, str],
                    min_delay: int | float = 0.55, max_delay: int | float = 1.55
                    ) -> list[dict[str, str, None]]:
    """bloomingbit 사이트를 크롤링 하는 함수

    Args:
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷
        headers: 식별 정보
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
    bloomingbit_website = 'https://bloomingbit.io/ko/feed'
    max_retry = 10
    news_last_number = None

    # Playwright 실행
    async with async_playwright() as p:
        # 브라우저 열기(Chromium, Firefox, WebKit 중 하나 선택 가능)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for _ in range(max_retry):
            try:
                # 블루밍비트 웹사이트로 이동
                await page.goto(bloomingbit_website)

                # 실시간 뉴스의 전체 버튼이 로드될 떄까지 대기하고 클릭
                await page.wait_for_selector('xpath=//*[@id="feedRealTimeHeader"]/div/ul/li[1]/button')
                await page.click('xpath=//*[@id="feedRealTimeHeader"]/div/ul/li[1]/button')
                # 가장 최신 뉴스를 클릭할 수 있을때까지 대기하고 하이퍼링크 가져오기
                await page.wait_for_selector('xpath=//*[@id="feedRealTimeContainer"]/section/div/div/div/div/div[1]/div/section')
                latest_news_html = page.locator('//*[@id="feedRealTimeContainer"]/section/div/div/div/div/div[1]/div/section')
                all_a = await latest_news_html.locator("a").all()
                href = await all_a[-1].get_attribute("href")

                # 하이퍼링크에서 가장 마지막 숫자 가져오기
                news_last_number = re.split(pattern=r'/+', string=href)[-1]
                news_last_number = int(news_last_number)
            except Exception as e:
                print()
                print(f'Playwright 동작 중 {type(e).__name__}가 발생했습니다.')
                print(traceback.format_exc())
            
            # 가장 마지막 숫자를 불러오는 것에 성공하면 for문 중단
            if news_last_number is not None:
                break
            time.sleep(random.uniform(min_delay, max_delay))
        
        # 작업 후 브라우저 닫기
        await browser.close()

    if news_last_number is None:
        return []

    get_cnt = 20
    category = '전체 뉴스'
    website = 'bloomingbit'
    end_date = datetime.strptime(end_datetime, date_format)
    nonstop = True
    bloomingbit_results = []

    while nonstop:
        first_url_number = news_last_number
        last_url_number = max(2, news_last_number - get_cnt)

        news_last_number -= (get_cnt + 1)
        # 가장 마지막 페이지인 1페이지는 삭제된 기사이므로 그 아래 포함 종료
        if news_last_number <= 1:
            nonstop = False
        
        url_list = [f'https://bloomingbit.io/ko/feed/news/{url}' for url in range(first_url_number, last_url_number - 1, -1)]
    
        async_result = await async_crawling(url_list=url_list, category=category, website=website, headers=headers)
        
        # 요청이 실패했으면 제외
        result = []
        for idx, res in enumerate(async_result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
            else:
                result.append(res)
        
        # end_date 이후가 아니면은 제거
        cut_info = datetime_cut(news_list=result, end_date=end_date, date_format=date_format)
        result, nonstop = cut_info['result'], cut_info['nonstop']

        bloomingbit_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return bloomingbit_results


async def coinreaders_category(
                                category: str, end_datetime: str, date_format: str, headers: dict[str, str],
                                min_delay: int | float = 2, max_delay: int | float = 3
                                ) -> list[dict[str, str, None]]:
    """coinreaders 사이트에서 일부 카테고리를 크롤링 하는 함수

    Args:
        category: 뉴스 카테고리
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷
        headers: 식별 정보
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

    page = 1
    if category == 'Breaking_news':
        web_page = f'https://www.coinreaders.com/sub.html?page={page}&section=sc16&section2='
    else:
        web_page = f'https://www.coinreaders.com/sub.html?page={page}&section=sc21&section2='
    website = 'coinreaders'
    end_date = datetime.strptime(end_datetime, date_format)
    nonstop = True
    coinreaders_results = []

    while nonstop:
        sync_result = sync_request(url=web_page, headers=headers, min_delay=min_delay, max_delay=max_delay)
        page += 1
        if category == 'Breaking_news':
            web_page = f'https://www.coinreaders.com/sub.html?page={page}&section=sc16&section2='
        else:
            web_page = f'https://www.coinreaders.com/sub.html?page={page}&section=sc21&section2='
        
        # html 문서 불러오기에 실패했으면 다음 페이지로 넘기기
        if sync_result['html'] is None or sync_result['response_reason'] != 'OK':
            print()
            print(f'{page}번 페이지의 HTML 문서 정보를 불러오는데 실패했습니다.')
            continue

        soup = BeautifulSoup(sync_result['html'], 'html.parser')
        url_tag_list = soup.find_all('div', {"class": "sub_read_list_box"})

        # url_tag_list가 비어있으면 최종 페이지까지 갔다는 것이므로 종료
        if not url_tag_list:
            nonstop = False
            break

        url_list = [f"https://www.coinreaders.com{url_tag.find('a')['href']}" for url_tag in url_tag_list]

        async_result = await async_crawling(url_list=url_list, category=category, website=website, headers=headers, min_delay=min_delay, max_delay=max_delay)
        
        # 요청이 실패했으면 제외
        result = []
        for idx, res in enumerate(async_result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
            else:
                result.append(res)
        
        # end_date 이후가 아니면은 제거
        cut_info = datetime_cut(news_list=result, end_date=end_date, date_format=date_format)
        result, nonstop = cut_info['result'], cut_info['nonstop']

        coinreaders_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return coinreaders_results


async def coinreaders(
                        end_datetime: str, date_format: str, headers: dict[str, str],
                    )-> list[dict[str, str, None]]:
    """coinreaders 사이트를 크롤링 하는 함수

    Args:
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷
        headers: 식별 정보

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

    task1 = asyncio.create_task(coinreaders_category(category='Breaking_news', end_datetime=end_datetime, date_format=date_format, headers=headers))
    task2 = asyncio.create_task(coinreaders_category(category='Crypto&Blockchain', end_datetime=end_datetime, date_format=date_format, headers=headers))
    
    await task1
    await task2

    breaking_news_list = task1.result()
    crypto_blockchain_news_list = task2.result()
    coinreaders_result = breaking_news_list + crypto_blockchain_news_list
    return coinreaders_result


async def blockstreet(
                        end_datetime: str, date_format: str, headers: dict[str, str],
                        min_delay: int | float = 1, max_delay: int | float = 2
                    ) -> list[dict[str, str, None]]:
    """blockstreet 사이트를 크롤링 하는 함수

    Args:
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷
        headers: 식별 정보
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
    
    section_cnt = 1
    category = '암호화폐'
    website = 'blockstreet'
    blockstreet_website = 'https://www.blockstreet.co.kr/coin-news'
    end_date = datetime.strptime(end_datetime, date_format)
    nonstop = True
    blockstreet_results = []

    # Playwright 실행
    async with async_playwright() as p:
        # 브라우저 열기(Chromium, Firefox, WebKit 중 하나 선택 가능)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # 블록스트리트 웹사이트로 이동
            await page.goto(blockstreet_website)

            await page.wait_for_selector('xpath=//*[@id="container"]/div[2]/div/button')
            section_list = await page.locator('//*[@id="newsList"]').locator('section').all()
            list_unit = len(section_list)

            while nonstop:
                url_list = []

                for i in range(section_cnt, section_cnt + list_unit):
                    section_n = page.locator(f'//*[@id="newsList"]/section[{i}]')

                    # 만약 section_n을 찾는 것에 실패하면 종료
                    cnt = await section_n.count()
                    if cnt == 0:
                        nonstop = False
                        break
                    
                    href = await section_n.locator("a").get_attribute("href")
                    url = f'https://www.blockstreet.co.kr{href}'
                    url_list.append(url)

                    section_cnt += 1

                async_result = await async_crawling(url_list=url_list, category=category, website=website, headers=headers)
                
                # 요청이 실패했으면 제외
                result = []
                for idx, res in enumerate(async_result):
                    if res is None:
                        print()
                        print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
                    else:
                        result.append(res)
                
                # end_date 이후가 아니면은 제거
                cut_info = datetime_cut(news_list=result, end_date=end_date, date_format=date_format)
                result, nonstop = cut_info['result'], cut_info['nonstop']

                blockstreet_results.extend(result)
                time.sleep(random.uniform(min_delay, max_delay))

                await page.click('xpath=//*[@id="container"]/div[2]/div/button')
                await page.wait_for_selector('xpath=//*[@id="container"]/div[2]/div/button')
        except Exception as e:
            print()
            print(f'Playwright 동작 중 {type(e).__name__}가 발생했습니다.')
            print(traceback.format_exc())
        
        # 작업 후 브라우저 닫기
        await browser.close()
    
    return blockstreet_results


def web_crawling(
                website: str,
                end_datetime: str, date_format: str
                ) -> list[dict[str, str, None]]:
    """해당 웹사이트를 크롤링 하는 함수

    Args:
        website: 웹사이트 이름
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷

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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    match website:
        case 'investing':
            result = loop.run_until_complete(investing(end_datetime=end_datetime, date_format=date_format, headers=headers))
        case 'hankyung':
            result = loop.run_until_complete(hankyung(end_datetime=end_datetime, date_format=date_format, headers=headers))
        case 'bloomingbit':
            result = loop.run_until_complete(bloomingbit(end_datetime=end_datetime, date_format=date_format, headers=headers))
        case 'coinreaders':
            result = loop.run_until_complete(coinreaders(end_datetime=end_datetime, date_format=date_format, headers=headers))
        case 'blockstreet':
            result = loop.run_until_complete(blockstreet(end_datetime=end_datetime, date_format=date_format, headers=headers))
    
    loop.close()

    return result


def multiprocess_crawling(
                    website_list: list[str],
                    end_datetime: str, date_format: str = '%Y-%m-%d %H:%M'
                    ) -> dict[str, list[dict[str, str, None]]]:
    """멀티 프로세싱으로 웹사이트를 크롤링 하는 함수

    Args:
        website_list: 웹사이트 이름 리스트
        end_datetime: 크롤링할 마지막 시각
        date_format: 시각 포맷

    Returns:
        {
            "웹사이트1":    [
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
                ],
            "웹사이트2":    ...
                                .
                                .
                                .
        }
    """

    fixed_params_crawling = partial(web_crawling, end_datetime=end_datetime, date_format=date_format)
    n = len(website_list)
    result = dict()

    with futures.ProcessPoolExecutor(max_workers=n) as executor:
        for website, news_list in zip(website_list, executor.map(fixed_params_crawling, website_list)):
            result[website] = news_list
    
    return result





if __name__ == '__main__':
    website_list = ['hankyung', 'bloomingbit', 'coinreaders', 'blockstreet']
    end_datetime = '2024-12-27 12:00'
    result = multiprocess_crawling(website_list=website_list, end_datetime=end_datetime)