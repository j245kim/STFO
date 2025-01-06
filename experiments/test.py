import time
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler


# Configure logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'crawling_scraping.log'

logger = logging.getLogger('crawling_scraping')
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=7)
handler.suffix = "%Y-%m-%d.txt"
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Example usage of logger
while True:
    logger.info("Crawling scraping module initialized")
    time.sleep(25)