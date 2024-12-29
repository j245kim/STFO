# import re

# from playwright.sync_api import sync_playwright

# # User-Agent 변경을 위한 옵션 설정
# user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
# headers = {
#             'User-Agent': user_agent
#         }

# # client 파라미터
# follow_redirects = True # 리다이렉트 허용 여부
# timeout = 90 # 응답 대기 허용 시간
# encoding = 'utf-8'
# max_retry = 10 # HTML 문서 요청 최대 재시도 횟수
# min_delay = 0.55 # 재시도 할 때 딜레이의 최소 시간
# max_delay = 1.55 # 재시도 할 때 딜레이의 최대 시간

# url = 'https://coinness.com/'

# with sync_playwright() as p:
#     # 브라우저 열기(Chromium, Firefox, WebKit 중 하나 선택 가능)
#     browser = p.chromium.launch(headless=True)
#     page = browser.new_page()

#     # 코인니스 웹사이트로 이동
#     page.goto(url)

#     page.wait_for_selector('xpath=//*[@id="root"]/div/div[2]/div/main/div[2]/div/div[2]/div[1]/div')
#     latest_news_html = page.locator('//*[@id="root"]/div/div[2]/div/main/div[2]/div/div[2]/div[1]/div')
#     a = latest_news_html.locator("a").first
#     href = a.get_attribute("href")

#     # 하이퍼링크에서 가장 마지막 숫자 가져오기
#     news_last_number = re.split(pattern=r'/+', string=href)[-1]
#     news_last_number = int(news_last_number)

# print(news_last_number)