# -*- coding: utf-8 -*-

# 설치가 필요한 라이브러리
# pip install httpx
# pip install beautifulsoup4
# pip install selenium
# pip install webdriver-manager

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
from concurrent import futures

# 파이썬 서드파티 라이브러리
import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


def datetime_trans(website: str, date_time: str, format: str = '%Y-%m-%d %H:%M') -> str:
    """웹사이트에 따른 업로드 시각, 수정 시각들을 같은 포맷으로 바꾸는 함수

    Args:
        website: 웹사이트 이름
        date_time: 바꿀 시각
        format: 바꾸는 포맷
    
    Return:
        2000-01-01 23:59 형태의 str 포맷
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
            news_datetime = datetime.strftime(news_datetime, format)
        case 'hankyung':
            news_datetime = date_time.replace('.', '-')
        case 'bloomingbit':
            _, y, m, d, ap, hm = re.split(pattern=r'\.?\s+', string=date_time)
            if ap == '오전':
                ap = 'AM'
            else:
                ap = 'PM'
            news_datetime = f'{y}-{m}-{d} {ap} {hm}'
            news_datetime = datetime.strptime(news_datetime, '%Y-%m-%d %p %I:%M')
            news_datetime = datetime.strftime(news_datetime, format)
        case 'cryptonews':
            date_time = re.sub(pattern=r'[월,]', repl='', string=date_time)
            m, d, y, hm = date_time.split()[:-1]
            news_datetime = f'{y}-{m}-{d} {hm}'
        case 'coinreaders':
            pass
        case 'dealsite':
            pass
        case 'blockstreet':
            pass

    return news_datetime


def datetime_cut(news_list: list[dict[str, str, None]], end_date: datetime) -> dict[str, list[dict[str, str, None]], bool]:
    """end_date보다 빠른 날짜의 데이터들을 제거하는 함수

    Args:
        news_list: 크롤링 및 스크래핑한 뉴스 데이터들
        end_date: 기준 시각
    
    Returns
        {
            "result": 자르기 완료한 크롤링 및 스크래핑한 뉴스 데이터들, list[dict[str, str, None]]
            "nonstop": 진행 여부 부울 변수, bool
        }
    """
    
    info = {"result": deepcopy(news_list), 'nonstop': True}

    while info['result'] and (datetime.strptime(info['result'][-1]['news_first_upload_time'], format) < end_date):
            info['nonstop'] = False
            del info['result'][-1]

    return info


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
            "response_reason": 응답 결과 이유, str
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
    
    # 응답 기록 추가
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
            "response_reason": 응답 결과 이유, str
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
    
    # 응답 기록 추가
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
        case 'cryptonews':
            # 1. 뉴스 데이터의 제목
            title = soup.find("h1", {"class": "mb-10"})
            title = title.text.strip(' \t\n\r\f\v')

            # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
            first_upload_time = None
            last_upload_time = soup.find("div", {"class": "single-post-new__author-top"})
            last_upload_time = last_upload_time.find("time")
            last_upload_time = last_upload_time.text
            last_upload_time = datetime_trans(website=website, date_time=last_upload_time)

            # 3. 뉴스 데이터의 기사 작성자
            author_list = soup.find_all("div", {"class": "author-mini__link"})
            if author_list:
                author_list = map(lambda x: x.text, author_list)
                author = ', '.join(author_list)
            else:
                author = None
            
            # 4. 뉴스 데이터의 본문
            content = soup.find("div", {"class": "article-single__content category_contents_details"})
            content = content.prettify()

            # 8. 비고
            note = '해외 사이트'
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
    category = '암호화폐'
    website = 'investing'
    page = 0
    end_date = datetime.strptime(end_datetime, format)
    nonstop = True
    investing_results = []

    while nonstop:
        page += 1

        with httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as sync_client:
            sync_result = sync_request(url=web_page, client=sync_client)
        web_page = f'https://kr.investing.com/news/cryptocurrency-news/{page + 1}'

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

        async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as async_client:
            crawl_list = [news_crawling(url=url, category=category, website=website, client=async_client) for url in url_list]
            async_result = await asyncio.gather(*crawl_list)
        
        # 요청이 실패했으면 제외
        result = []
        for idx, res in enumerate(async_result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
            else:
                result.append(res)

        # end_date 이후가 아니면은 제거
        cut_info = datetime_cut(news_list=result, end_date=end_date)
        result, nonstop = cut_info['result'], cut_info['nonstop']

        investing_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return investing_results


async def hankyung(
                    end_datetime: str, format: str,
                    headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                    encoding: str = 'utf-8', min_delay: int | float = 0.55, max_delay: int | float = 1.55
                    ) -> list[dict[str, str, None]]:
    """hankyung 사이트를 크롤링 하는 함수

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

    category = '암호화폐'
    website = 'hankyung'
    page = 0
    end_date = datetime.strptime(end_datetime, format)
    nonstop = True
    hankyung_results = []

    while nonstop:
        page += 1
        web_page = f'https://www.hankyung.com/koreamarket/news/crypto?page={page}'

        with httpx.Client(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as sync_client:
            sync_result = sync_request(url=web_page, client=sync_client)
        
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

        async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as async_client:
            crawl_list = [news_crawling(url=url, category=category, website=website, client=async_client) for url in url_list]
            async_result = await asyncio.gather(*crawl_list)
        
        # 요청이 실패했으면 제외
        result = []
        for idx, res in enumerate(async_result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
            else:
                result.append(res)
        
        # end_date 이후가 아니면은 제거
        cut_info = datetime_cut(news_list=result, end_date=end_date)
        result, nonstop = cut_info['result'], cut_info['nonstop']

        hankyung_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return hankyung_results


async def bloomingbit(
                    end_datetime: str, format: str,
                    headers: dict[str, str], follow_redirects: bool = True, timeout: int | float = 90,
                    encoding: str = 'utf-8', min_delay: int | float = 0.55, max_delay: int | float = 1.55
                    ) -> list[dict[str, str, None]]:
    """bloomingbit 사이트를 크롤링 하는 함수

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

    bloomingbit_website = 'https://bloomingbit.io/ko/feed'
    get_cnt = 20
    category = '전체 뉴스'
    website = 'bloomingbit'
    end_date = datetime.strptime(end_datetime, format)
    nonstop = True
    bloomingbit_results = []

    try:
        total_wait = 60
        options = Options()
        # 1. 브라우저 창 숨기기 (Headless 모드)
        options.add_argument("--headless")
        # 2. 사용자 에이전트 변경 (옵션)
        options.add_argument(f'user-agent={headers["User-Agent"]}')
        # 3. 불필요한 로그 최소화
        options.add_argument("--log-level=3")
        # 4. 알림 비활성화
        options.add_argument('--disable-notifications')

        # WebDriver 생성 (webdriver-manager 사용)
        service = Service(ChromeDriverManager().install())  # 크롬드라이버 자동 설치 및 경로 설정
        driver = webdriver.Chrome(service=service, options=options)
        # 모든 driver 작업들에 대해 최대 total_wait초까지 대기
        driver.implicitly_wait(total_wait)

        # 블루밍비트 웹사이트 열기
        driver.get(bloomingbit_website)
        # 블루밍비트 실시간 뉴스에서 전체 클릭
        driver.find_element(By.XPATH, '//*[@id="feedRealTimeHeader"]/div/ul/li[1]/button').click()
        # 가장 최신 기사 번호를 추출
        result = driver.find_element(By.XPATH, '//*[@id="feedRealTimeContainer"]/section/div/div/div/div/div[1]')
        a_tag = result.find_elements(By.TAG_NAME, 'a')[-1]
        href = a_tag.get_attribute("href")
        last_number = re.split(pattern=r'/+', string=href)[-1]
        last_number = int(last_number)
        # driver 종료
        driver.quit()
    except Exception:
        print()
        print('selenium 동작 중 실패')
        print(traceback.format_exc())
        return bloomingbit_results

    while nonstop:
        first_url_number = last_number
        last_url_number = max(2, last_number - get_cnt)

        last_number -= (get_cnt + 1)
        # 가장 마지막 페이지인 1페이지는 삭제된 기사이므로 그 아래 포함 종료
        if last_number <= 1:
            nonstop = False
        
        url_list = [f'https://bloomingbit.io/ko/feed/news/{url}' for url in range(first_url_number, last_url_number - 1, -1)]
    
        async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects, timeout=timeout, default_encoding=encoding) as async_client:
            crawl_list = [news_crawling(url=url, category=category, website=website, client=async_client) for url in url_list]
            async_result = await asyncio.gather(*crawl_list)
        
        # 요청이 실패했으면 제외
        result = []
        for idx, res in enumerate(async_result):
            if res is None:
                print()
                print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
            else:
                result.append(res)
        
        # end_date 이후가 아니면은 제거
        cut_info = datetime_cut(news_list=result, end_date=end_date)
        result, nonstop = cut_info['result'], cut_info['nonstop']

        bloomingbit_results.extend(result)
        time.sleep(random.uniform(min_delay, max_delay))
    
    return bloomingbit_results


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
    
    investing_result = asyncio.run(investing(end_datetime='2024-12-20 00:00', format='%Y-%m-%d %H:%M', headers=headers))
    print(investing_result[-1])
    # hankyung_result = asyncio.run(hankyung(end_datetime='2024-12-20 00:00', format='%Y-%m-%d %H:%M', headers=headers))
    # bloomingbit_result = asyncio.run(bloomingbit(end_datetime='2024-12-20 00:00', format='%Y-%m-%d %H:%M', headers=headers))