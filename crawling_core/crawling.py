# -*- coding: utf-8 -*-
"""코인 뉴스 사이트에서 크롤링하는 Python 모듈

크롤링을 하는데 사이트마다 HTML 문서 구조도 다르고, 멀티 스레딩을 다루는 것도 솔직히 쉽지가 않다.
그래서 이 모듈로 좀 더 쉽게 크롤링을 하도록 한다.
"""

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


class NewsInfo:
    def __init__(self,
                 website_name: str,
                 save_path: str
                 ) -> None:
        self._results = [] # 크롤링한 데이터들
        self._website = website_name.capitalize() # 크롤링한 사이트 이름
        self._save_path = save_path # 저장 경로

    def __len__(self) -> int:
        return len(self._results)
    
    def __eq__(self, other) -> bool:
        return self._results == other
    
    def to_json(self) -> None:
        with open(self._save_path, mode='w', encoding='utf-8') as f:
            json.dump(self._results, f, ensure_ascii=False, indent=4)


class Crawling:
    def __init__(self,
                 headers: dict[str, str] = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"},
                 allow_redirects: bool = True,
                 timeout: int | float | tuple[int, float] = 90,
                 max_retry: int = 10,
                 min_delay: int | float = 0.5,
                 max_delay: int | float = 1.25
                 ) -> None:
        # requests 파라미터
        self.headers = headers # User-Agent 변경을 위한 옵션 설정
        self.allow_redirects = allow_redirects # 리다이렉트 허용 여부
        self.timeout = timeout # 응답 대기 허용 시간
        self.max_retry = max_retry # HTML 문서 요청 최대 재시도 횟수
        self.min_delay = min_delay # request 요청 후 잠깐동안 넣을 딜레이 최소 시간
        self.max_delay = max_delay # request 요청 후 잠깐동안 넣을 딜레이 최소 시간

        self.__websites = set(('investing',))
        self.crawlings = []
    

