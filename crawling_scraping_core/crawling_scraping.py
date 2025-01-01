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
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from http_process import sync_request, async_request
from preprocessing import datetime_trans, datetime_cut


class NewsInfo:
    def __init__(self, website_name: str, save_path: str) -> None:
        self._results = [] # 크롤링한 데이터들
        self.__website = website_name # 크롤링한 사이트 이름
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
    def __init__(self) -> None:
        self._crawling_scraping = dict()
        self.__possible_sites = ['hankyung', 'bloomingbit', 'coinreaders', 'blockstreet']
        self.__stfo_path = Path(__file__).parents[1]
        self.__data_path = rf'{self.__stfo_path}\datas\news_data'
    
    def add_website(self, website_name: str) -> bool:
        """크롤링 및 스크래핑할 사이트를 추가하는 메소드
        
        Args:
            website_name: 크롤링 및 스크래핑할 사이트 이름
        
        Returns:
            크롤링 및 스크래핑할 사이트가 성공적으로 추가되었는지 여부, bool
        """

        if website_name not in self.__possible_sites:
            raise ValueError(f'사이트의 이름은 {", ".join(self.__possible_sites)} 중 하나여야 합니다.')
        
        data_path = rf'{self.__data_path}\{website_name}_data.json'
        self._crawling_scraping[website_name] = NewsInfo(website_name=website_name, save_path=data_path)
        return True

    def to_json(self) -> None:
        """크롤링 및 스크래핑한 데이터들을 json 파일로 저장하는 메소드"""

        for website in self._crawling_scraping.keys():
            self._crawling_scraping[website].to_json()
