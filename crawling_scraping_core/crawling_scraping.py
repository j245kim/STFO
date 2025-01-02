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
from pathlib import Path

# 파이썬 서드파티 라이브러리
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# 사용자 정의 라이브러리
from .http_process import sync_request, async_request
from .preprocessing import datetime_trans, datetime_cut


class NewsInfo:
    def __init__(self, website: str, save_path: str) -> None:
        self._results = [] # 크롤링 및 스크래핑한 데이터들
        self.__website = website # 크롤링 및 스크래핑한 사이트 이름
        self.__save_path = save_path # 저장 경로

    def __len__(self) -> int:
        return len(self._results)
    
    def __eq__(self, other) -> bool:
        return self._results == other
    
    def to_json(self) -> None:
        """크롤링 및 스크래핑한 데이터를 json 파일로 저장하는 메소드"""

        with open(self.__save_path, mode='w', encoding='utf-8') as f:
            json.dump(self._results, f, ensure_ascii=False, indent=4)

class CrawlingScraping:
    def __init__(self, record_log: bool = False) -> None:
        self._crawling_scraping = dict()
        self.__possible_websites = ['hankyung', 'bloomingbit', 'coinreaders', 'blockstreet']
        self.__stfo_path = Path(__file__).parents[1]
        self.__logs_path = rf'{self.__stfo_path}\logs'
        self.__logs_data_path = rf'{self.__stfo_path}\logs\crawling_scraping_log'
        self.__datas_path = rf'{self.__stfo_path}\datas'
        self.__datas_news_path = rf'{self.__stfo_path}\datas\news_data'

        if record_log:
            # logs 폴더가 없으면 logs 폴더와 그 하위 폴더로 crawling_scraping_log 폴더 생성
            if not os.path.exists(self.__logs_path):
                os.makedirs(self.__logs_data_path, exist_ok=True)
            # logs 폴더는 있지만 crawling_scraping_log 폴더가 없으면 crawling_scraping_log 폴더 생성
            elif not os.path.exists(self.__logs_data_path):
                os.mkdir(self.__logs_data_path)
        # datas 폴더가 없으면 datas 폴더와 그 하위 폴더로 news_data 폴더 생성
        if not os.path.exists(self.__datas_path):
            os.makedirs(self.__datas_news_path, exist_ok=True)
        # datas 폴더는 있지만 newsdata 폴더가 없으면 news_data 폴더 생성
        elif not os.path.exists(self.__datas_news_path):
            os.mkdir(self.__datas_news_path)
    
    def add_website(self, website: str, save_path: str = None) -> bool:
        """크롤링 및 스크래핑할 사이트를 추가하는 메소드
        
        Args:
            website: 크롤링 및 스크래핑할 웹사이트 이름
            save_path: 크롤링 및 스크래핑한 데이터를 저장할 경로
        
        Returns:
            크롤링 및 스크래핑할 사이트가 성공적으로 추가되었는지 여부, bool
        """

        if website not in self.__possible_websites:
            raise ValueError(f'웹사이트의 이름은 "{", ".join(self.__possible_websites)}" 중 하나여야 합니다.')
        
        if save_path is None:
            save_path = rf'{self.__datas_news_path}\{website}_data.json'
        self._crawling_scraping[website] = NewsInfo(website=website, save_path=save_path)
        return True
    
    @staticmethod
    async def news_crawling(
                            url:str, category: str, website: str, change_format: str,
                            headers: dict[str, str], max_retry: int = 10,
                            min_delay: int | float = 0.55, max_delay: int | float = 1.55
                            ) -> dict[str, str, None] | None:
        """뉴스 URL을 바탕으로 크롤링 및 스크래핑을 하는 메소드

        Args:
            url: 뉴스 URL
            category: 뉴스 카테고리
            website: 웹사이트 이름
            change_format: 바꾸는 포맷
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
            case 'hankyung':
                # 1. 뉴스 데이터의 제목
                title = soup.find('h1', {"class": "headline"})
                title = title.text.strip(' \t\n\r\f\v')

                # 2. 뉴스 데이터의 최초 업로드 시각과 최종 수정 시각
                upload_times = soup.find_all('span', {"class": "txt-date"})

                first_upload_time = upload_times[0].text
                first_upload_time = datetime_trans(website=website, date_time=first_upload_time, change_format=change_format)
                last_upload_time = upload_times[1].text
                last_upload_time = datetime_trans(website=website, date_time=last_upload_time, change_format=change_format)

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
                    first_upload_time = datetime_trans(website=website, date_time=first_upload_time, change_format=change_format)
                last_upload_time = soup.find("span", {"class": "_feedReporterWithDatePublished_updateDate__xCxls"})
                if last_upload_time is not None:
                    last_upload_time = last_upload_time.text
                    last_upload_time = datetime_trans(website=website, date_time=last_upload_time, change_format=change_format)
                
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
                first_upload_time = datetime_trans(website=website, date_time=first_upload_time, change_format=change_format)
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
                        first_upload_time = datetime_trans(website=website, date_time=first_upload_time, change_format=change_format)
                    elif span[0] == '수정':
                        last_upload_time = f'{span[1]} {span[2]}'
                        last_upload_time = datetime_trans(website=website, date_time=last_upload_time, change_format=change_format)

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
    
    @staticmethod
    async def async_crawling(
                            url_list: list[str], category: str, website: str,
                            change_format: str, headers: dict[str, str],
                            min_delay: int | float = 0.55, max_delay: int | float = 1.55
                            ) -> list[dict[str, str, None], None]:
        """비동기로 뉴스 URL들을 크롤링 및 스크래핑하는 메소드

        Args:
            url_list: 뉴스 URL list
            category: 뉴스 카테고리
            website: 웹사이트 이름
            change_format: 바꾸는 포맷
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
            crawl_list = [CrawlingScraping.news_crawling(url=url, category=category, website=website, change_format=change_format, headers=headers, min_delay=min_delay, max_delay=max_delay) for url in url_list]
            async_result = await asyncio.gather(*crawl_list)
            return async_result
        return []
    
    @staticmethod
    async def hankyung(
                        end_datetime: str, date_format: str,
                        change_format: str, headers: dict[str, str],
                        min_delay: int | float = 2, max_delay: int | float = 3
                        ) -> list[dict[str, str, None]]:
        """hankyung 사이트를 크롤링 및 스크래핑 하는 메소드

        Args:
            end_datetime: 크롤링 및 스크래핑할 마지막 시각
            date_format: 시각 포맷
            change_format: 바꾸는 포맷
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
            if sync_result['html'] is None:
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

            async_result = await CrawlingScraping.async_crawling(url_list=url_list, category=category, website=website, change_format=change_format, headers=headers)
            
            # 요청이 실패했으면 제외
            result = []
            for idx, res in enumerate(async_result):
                if res is None:
                    print()
                    print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
                else:
                    result.append(res)
            
            # end_date 이후가 아니면은 제거
            cut_info = datetime_cut(news_list=result, end_date=end_date, change_format=change_format)
            result, nonstop = cut_info['result'], cut_info['nonstop']

            hankyung_results.extend(result)
            time.sleep(random.uniform(min_delay, max_delay))
        
        return hankyung_results

    @staticmethod
    async def bloomingbit(
                        end_datetime: str, date_format: str,
                        change_format: str, headers: dict[str, str],
                        min_delay: int | float = 2, max_delay: int | float = 3
                        ) -> list[dict[str, str, None]]:
        """bloomingbit 사이트를 크롤링 및 스크래핑 하는 메소드

        Args:
            end_datetime: 크롤링 및 스크래핑할 마지막 시각
            date_format: 시각 포맷
            change_format: 바꾸는 포맷
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
        
            async_result = await CrawlingScraping.async_crawling(url_list=url_list, category=category, website=website, change_format=change_format, headers=headers)
            
            # 요청이 실패했으면 제외
            result = []
            for idx, res in enumerate(async_result):
                if res is None:
                    print()
                    print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
                else:
                    result.append(res)
            
            # end_date 이후가 아니면은 제거
            cut_info = datetime_cut(news_list=result, end_date=end_date, change_format=change_format)
            result, nonstop = cut_info['result'], cut_info['nonstop']

            bloomingbit_results.extend(result)
            time.sleep(random.uniform(min_delay, max_delay))
        
        return bloomingbit_results

    @staticmethod
    async def coinreaders_category(
                                    category: str, end_datetime: str, date_format: str,
                                    change_format: str, headers: dict[str, str],
                                    min_delay: int | float = 2, max_delay: int | float = 3
                                    ) -> list[dict[str, str, None]]:
        """coinreaders 사이트에서 일부 카테고리를 크롤링 및 스크래핑 하는 메소드

        Args:
            category: 뉴스 카테고리
            end_datetime: 크롤링 및 스크래핑할 마지막 시각
            date_format: 시각 포맷
            change_format: 바꾸는 포맷
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
            if sync_result['html'] is None:
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

            async_result = await CrawlingScraping.async_crawling(url_list=url_list, category=category, website=website, change_format=change_format, headers=headers, min_delay=min_delay, max_delay=max_delay)
            
            # 요청이 실패했으면 제외
            result = []
            for idx, res in enumerate(async_result):
                if res is None:
                    print()
                    print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
                else:
                    result.append(res)
            
            # end_date 이후가 아니면은 제거
            cut_info = datetime_cut(news_list=result, end_date=end_date, change_format=change_format)
            result, nonstop = cut_info['result'], cut_info['nonstop']

            coinreaders_results.extend(result)
            time.sleep(random.uniform(min_delay, max_delay))
        
        return coinreaders_results

    @staticmethod
    async def coinreaders(
                            end_datetime: str, date_format: str,
                            change_format: str, headers: dict[str, str],
                        )-> list[dict[str, str, None]]:
        """coinreaders 사이트를 크롤링 및 스크래핑 하는 메소드

        Args:
            end_datetime: 크롤링 및 스크래핑할 마지막 시각
            date_format: 시각 포맷
            change_format: 바꾸는 포맷
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

        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(CrawlingScraping.coinreaders_category(category='Breaking_news', end_datetime=end_datetime, date_format=date_format, change_format=change_format, headers=headers))
            task2 = tg.create_task(CrawlingScraping.coinreaders_category(category='Crypto&Blockchain', end_datetime=end_datetime, date_format=date_format, change_format=change_format, headers=headers))

        breaking_news_list = task1.result()
        crypto_blockchain_news_list = task2.result()
        coinreaders_result = breaking_news_list + crypto_blockchain_news_list
        return coinreaders_result

    @staticmethod
    async def blockstreet(
                            end_datetime: str, date_format: str,
                            change_format: str, headers: dict[str, str],
                            min_delay: int | float = 2, max_delay: int | float = 3
                        ) -> list[dict[str, str, None]]:
        """blockstreet 사이트를 크롤링 및 스크래핑 하는 메소드

        Args:
            end_datetime: 크롤링 및 스크래핑할 마지막 시각
            date_format: 시각 포맷
            change_format: 바꾸는 포맷
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

                    async_result = await CrawlingScraping.async_crawling(url_list=url_list, category=category, website=website, change_format=change_format, headers=headers)
                    
                    # 요청이 실패했으면 제외
                    result = []
                    for idx, res in enumerate(async_result):
                        if res is None:
                            print()
                            print(f'요청 실패한 데이터 : URL={url_list[idx]}, category={category}, website={website}')
                        else:
                            result.append(res)
                    
                    # end_date 이후가 아니면은 제거
                    cut_info = datetime_cut(news_list=result, end_date=end_date, change_format=change_format)
                    result, nonstop = cut_info['result'], cut_info['nonstop']

                    blockstreet_results.extend(result)
                    time.sleep(random.uniform(min_delay, max_delay))

                    button = page.locator('//*[@id="container"]/div[2]/div/button')
                    if button.count() == 0:
                        nonstop = False
                        break
                    await page.click('xpath=//*[@id="container"]/div[2]/div/button')
                    await page.wait_for_selector('xpath=//*[@id="container"]/div[2]/div/button')
            except Exception as e:
                print()
                print(f'Playwright 동작 중 {type(e).__name__}가 발생했습니다.')
                print(traceback.format_exc())
            
            # 작업 후 브라우저 닫기
            await browser.close()
        
        return blockstreet_results
    
    @staticmethod
    def web_crawling(
                    website: str, end_datetime: str,
                    date_format: str, change_format: str
                    ) -> list[dict[str, str, None]]:
        """해당 웹사이트를 크롤링 및 스크래핑 하는 메소드

        Args:
            website: 웹사이트 이름
            end_datetime: 크롤링 및 스크래핑할 마지막 시각
            date_format: 시각 포맷
            change_format: 바꾸는 포맷

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
                    'User-Agent': user_agent,
                    "Connection": "close"
                }

        match website:
            case 'hankyung':
                return asyncio.run(CrawlingScraping.hankyung(end_datetime=end_datetime, date_format=date_format, change_format=change_format, headers=headers))
            case 'bloomingbit':
                return asyncio.run(CrawlingScraping.bloomingbit(end_datetime=end_datetime, date_format=date_format, change_format=change_format, headers=headers))
            case 'coinreaders':
                return asyncio.run(CrawlingScraping.coinreaders(end_datetime=end_datetime, date_format=date_format, change_format=change_format, headers=headers))
            case 'blockstreet':
                return asyncio.run(CrawlingScraping.blockstreet(end_datetime=end_datetime, date_format=date_format, change_format=change_format, headers=headers))

    def run(self,
            end_datetime: str, date_format: str,
            change_format: str = '%Y-%m-%d %H:%M'
            ) -> dict[str, list[dict[str, str, None]]]:
        """멀티 프로세싱으로 웹사이트를 크롤링 및 스크래핑 하는 메소드

        Args:
            end_datetime: 크롤링 및 스크래핑할 마지막 시각
            date_format: 시각 포맷
            change_format: 바꾸는 포맷

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

        website_list = list(self._crawling_scraping.keys())
        fixed_params_crawling = partial(CrawlingScraping.web_crawling, end_datetime=end_datetime, date_format=date_format, change_format=change_format)
        n = len(self._crawling_scraping)

        with futures.ProcessPoolExecutor(max_workers=n) as executor:
            for website, news_list in zip(website_list, executor.map(fixed_params_crawling, website_list)):
                self._crawling_scraping[website]._results = news_list
        
        return self._crawling_scraping

    def to_json(self) -> None:
        """크롤링 및 스크래핑한 데이터들을 json 파일로 저장하는 메소드"""

        for website in self._crawling_scraping.keys():
            self._crawling_scraping[website].to_json()