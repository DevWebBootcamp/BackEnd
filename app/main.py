from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.user_router import router as user_router
from api.storage_router import router as storage_router
from app.database import create_tables
from fastapi.staticfiles import StaticFiles
from app.config import PROFILE_IMAGE_DIR, ITEM_IMAGE_DIR

# 데이터베이스 테이블 생성
create_tables()

# FastAPI 인스턴스 생성
app = FastAPI()

# 허용할 도메인 설정 (예: 특정 도메인만 허용하거나 모든 도메인을 허용할 수 있음)
origins = [
    "http://localhost",          # 기본 localhost
    "http://localhost:3000",     # 프론트엔드 포트 명시
    "http://127.0.0.1:3000"      # IP 형식으로 명시 가능
]

# CORS 미들웨어 추가, 모든 출처 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처에서 접근 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프로필 이미지 static 경로 등록
app.mount("/images/profile", StaticFiles(directory=PROFILE_IMAGE_DIR), name="profile_images")

# 물건 이미지 static 경로 등록
app.mount("/images/items", StaticFiles(directory=ITEM_IMAGE_DIR), name="item_images")

# 라우터 등록
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(storage_router, prefix="/storages", tags=["storages"])

# 루트 URL에 대한 GET 요청 처리
@app.get("/")
def read_root():
    return {"Hello": "World"}