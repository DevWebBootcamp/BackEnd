from fastapi import FastAPI
from api.user_router import router as user_router
from api.storage_router import router as storage_router
from app.database import create_tables

# 데이터베이스 테이블 생성
create_tables()

# FastAPI 인스턴스 생성
app = FastAPI()

# 라우터 등록
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(storage_router, prefix="/storages", tags=["storages"])

# 루트 URL에 대한 GET 요청 처리
@app.get("/")
def read_root():
    return {"Hello": "World"}