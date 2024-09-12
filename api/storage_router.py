from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import app.crud as crud
import app.schema as schema
import app.auth  as auth
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 사용자 공간 조회
@router.get("/{user_no}/spaces/{area_no}", response_model=schema.StorageAreaSchema, summary="특정 저장 공간 조회")
def read_user_storage_space(
    user_no: int, 
    area_no: int, 
    db: Session = Depends(get_db), 
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 현재 로그인한 사용자만 자신의 저장 공간에 접근할 수 있도록 제한
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to access this storage space.")
    
    # 특정 유저가 해당 저장 공간을 소유하는지 확인
    space = crud.get_user_storage_space(db, user_no=user_no, area_no=area_no)
    
    return space