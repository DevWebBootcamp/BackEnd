from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.user_router import router as user_router
from api.storage_router import router as storage_router
from app.database import create_tables

# 데이터베이스 테이블 생성
create_tables()

# FastAPI 인스턴스 생성
app = FastAPI()

# 허용할 도메인 설정 (예: 특정 도메인만 허용하거나 모든 도메인을 허용할 수 있음)
origins = [
    "http://localhost"
]

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 허용할 출처
    allow_credentials=True, # 쿠키 및 인증 정보 허용 여부
    allow_methods=["*"], # 허용할 HTTP 메서드 (예: GET, POST 등)
    allow_headers=["*"], # 허용할 HTTP 헤더
)

# 라우터 등록
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(storage_router, prefix="/storages", tags=["storages"])

# 루트 URL에 대한 GET 요청 처리
@app.get("/")
def read_root():
    return {"Hello": "World"}