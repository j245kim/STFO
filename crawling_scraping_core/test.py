from pathlib import Path

# 현재 파일의 2단계 상위 디렉토리
parent_path = Path(__file__).parents[1]
data_path = rf'{parent_path}\datas\news_data'

print(type(data_path))
print(data_path)