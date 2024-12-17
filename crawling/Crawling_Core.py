# Crawling_Core.py
"""코인 뉴스 사이트에서 크롤링하는 Python 모듈

크롤링을 하는데 사이트마다 HTML 문서 구조도 다르고, 멀티 스레딩을 다루는 것도 솔직히 쉽지가 않다.
그래서 이 모듈로 좀 더 쉽게 크롤링을 하도록 한다.
"""

# Python 라이브러리
# 파이썬 표준 라이브러리
import os
import json
import re
import random
import time
import traceback
from datetime import datetime
from functools import partial
from concurrent import futures

# 파이썬 서드파티 라이브러리
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


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
        self.request_get = partial(requests.get, headers=self.headers, allow_redirects=self.allow_redirects, timeout=self.timeout)

        self.__websites = set(('investing',))
        self.crawlings = []
    
    def request_html(self, url: str) -> str | None:
        """requests로 HTML 문서 정보를 불러오는 함수

        Args:
            url: URL
        
        Return:
            텍스트화한 HTML 문서 정보, str

            or 
        
            None
        """

        html = None

        for _ in range(self.max_retry):
            # requests로 HTML GET
            response = self.request_get(url)
            # HTML 문서 정보를 불러오는 것에 성공하면 for문 중단
            if response.ok and response.status_code == requests.codes.ok:
                html = response.text
                break

            time.sleep(random.uniform(self.min_delay, self.max_delay))
        
        # 응답 요청이 실패했으면 메세지 출력
        if html is None:
            print()
            print(response.reason)
            print(f'HTML 문서 정보 가져오기를 실패한 URL : {url}')
        
        return html





