import re

from playwright.sync_api import sync_playwright

bloomingbit_website = 'https://bloomingbit.io/ko/feed'

with sync_playwright() as p:
    # 브라우저 열기 (Chromium, Firefox, WebKit 중 하나 선택 가능)
    browser = p.chromium.launch(headless=True)  # headless=True로 설정하면 브라우저가 안열림
    page = browser.new_page()

    # 블루밍비트 브라우저 열기
    page.goto(bloomingbit_website)

    # 실시간 뉴스의 전체 버튼이 로드될 떄까지 대기하고 클릭
    page.wait_for_selector('xpath=//*[@id="feedRealTimeHeader"]/div/ul/li[1]/button')
    page.click('xpath=//*[@id="feedRealTimeHeader"]/div/ul/li[1]/button')
    # 가장 최신 뉴스를 클릭할 수 있을때까지 대기하고 하이퍼링크 가져오기
    page.wait_for_selector('xpath=//*[@id="feedRealTimeContainer"]/section/div/div/div/div/div[1]/div')
    latest_news_html = page.locator('//*[@id="feedRealTimeContainer"]/section/div/div/div/div/div[1]/div/section')
    all_a = latest_news_html.locator("a").all()
    href = all_a[-1].get_attribute("href")

    # 작업 후 브라우저 닫기
    browser.close()

last_number = re.split(pattern=r'/+', string=href)[-1]
last_number = int(last_number)
print(last_number)