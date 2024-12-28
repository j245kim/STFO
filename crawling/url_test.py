from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

website = 'https://kr.investing.com/news/cryptocurrency-news/article-1316479'

# with sync_playwright() as p:
#     # 브라우저 열기 (Chromium, Firefox, WebKit 중 하나 선택 가능)
#     browser = p.chromium.launch(headless=True)  # headless=True로 설정하면 브라우저가 안열림
#     page = browser.new_page()

#     page.goto(website)
#     html_content = page.content()

#     # 작업 후 브라우저 닫기
#     browser.close()

# soup = BeautifulSoup(html_content, 'html.parser')
# article = soup.find('div', id='article')
# print(article.prettify())



from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.request.new_context()
    response = context.get(website)

    soup = BeautifulSoup(response.text(), 'html.parser')
    article = soup.find('div', id='article')

    print(article.prettify())
    print()
    print(response.ok)
    print(response.status)
    print(response.status_text)