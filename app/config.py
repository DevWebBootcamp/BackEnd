import os

# 프로젝트의 기본 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 프로필 이미지 저장 경로 설정
PROFILE_IMAGE_DIR = os.path.join(BASE_DIR, "app", "images", "profile")
os.makedirs(PROFILE_IMAGE_DIR, exist_ok=True)  # 디렉토리가 존재하지 않으면 생성

# 물건 이미지 저장 경로 설정
ITEM_IMAGE_DIR = os.path.join(BASE_DIR, "app", "images", "items")
os.makedirs(ITEM_IMAGE_DIR, exist_ok=True)