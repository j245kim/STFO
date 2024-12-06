import json

import pandas as pd

with open('./news_crawlings.json') as f:
    data = json.load(f)

data_trans = list(map(lambda x: list(x.values()), data))

df = pd.DataFrame(data_trans, columns=['news_title', 'news_first_upload_time', 'news_last_upload_time', 'author', 'news_content', 'news_url', 'news_website'])
df.head()