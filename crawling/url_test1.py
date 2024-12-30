import time
import random

from playwright.sync_api import sync_playwright


website = 'https://www.blockstreet.co.kr/coin-news'

# # Playwright 실행
# with sync_playwright() as p:
#     # 브라우저 열기(Chromium, Firefox, WebKit 중 하나 선택 가능)
#     browser = p.chromium.launch(headless=False)
#     page = browser.new_page()

#     # 블록스트리트 웹사이트로 이동
#     page.goto(website)

#     while True:
#         button_check = page.wait_for_selector('xpath=//*[@id="container"]/div[2]/div/button')

#         if button_check is None:
#             break

#         page.click('xpath=//*[@id="container"]/div[2]/div/button')

#         time.sleep(random.uniform(1, 2))
    
#     # 작업 후 브라우저 닫기
#     browser.close()


# Playwright 실행
with sync_playwright() as p:
    # 브라우저 열기(Chromium, Firefox, WebKit 중 하나 선택 가능)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 블록스트리트 웹사이트로 이동
    page.goto(website)

    page.wait_for_selector('xpath=//*[@id="container"]/div[2]/div/button')
    
    test = page.locator('//*[@id="newsList"]/section[1050]')
    print(test.count())

    
    # 작업 후 브라우저 닫기
    browser.close()