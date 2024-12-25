from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

total_wait = 90
scroll_wait = 2
options = Options()

# 1. 브라우저 창 숨기기 (Headless 모드)
options.add_argument("--headless")
# 2. 사용자 에이전트 변경 (옵션)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
options.add_argument(f'user-agent={user_agent}')
# 3. 불필요한 로그 최소화
options.add_argument("--log-level=3")
# 4. 알림 비활성화
options.add_argument('--disable-notifications')

# WebDriver 생성 (webdriver-manager 사용)
service = Service(ChromeDriverManager().install())  # 크롬드라이버 자동 설치 및 경로 설정
driver = webdriver.Chrome(service=service, options=options)
# 모든 driver 작업들에 대해 최대 10초까지 대기
driver.implicitly_wait(total_wait)




driver.get("https://kr.investing.com/news/cryptocurrency-news/article-1314975")
content = driver.find_element(By.XPATH, '//*[@id="article"]')

print(content.get_attribute('outerHTML'))