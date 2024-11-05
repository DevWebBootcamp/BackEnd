import os

# 프로젝트의 기본 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 이미지 저장 경로 설정
IMAGE_UPLOAD_DIR = os.path.join(BASE_DIR, "images", "profile")

# 디렉토리가 존재하지 않으면 생성
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)