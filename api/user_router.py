from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from app import crud, schema, auth
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from fastapi.responses import Response
from app.config import PROFILE_IMAGE_DIR  # 이미지 경로 설정
import os, uuid, shutil
import mimetypes
import logging

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 회원가입
@router.post("/signup", response_model=schema.User, summary="회원가입")
def create_user_route(user: schema.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user_email = crud.get_user_by_email(db, email=user.email)
        db_user_phone = crud.get_user_by_phone(db, cell_phone=user.cell_phone)
        if db_user_email or db_user_phone:
            raise HTTPException(status_code=400, detail="User already registered")
        
        # 6자리 인증 코드 생성
        verification_code = auth.generate_verification_code()
        
        # 사용자 생성 (아직 계정 비활성화)
        user_data = crud.create_user(db=db, user=user, verification_code=verification_code)
        
        # 이메일로 인증 코드 전송
        auth.send_verification_email(user.email, verification_code)

        return user_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 이메일 인증
@router.post("/verify-code", summary="이메일 인증")
def verify_code_route(request: schema.VerifyCodeRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.verification_code != request.verification_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # 계정 활성화
    user.user_isDisabled = False
    user.verification_code = None  # 인증 코드 제거
    db.commit()
    
    return {"msg": "Account successfully verified"}


# 로그인
@router.post("/login", summary="로그인")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect user ID or password")
    
    if user.user_isDisabled:
        # 계정이 비활성화된 경우 이메일 인증 먼저 하라고 알려줌
        raise HTTPException(status_code=403, detail="Email not verified")
    
    access_token = auth.create_access_token(user.email)
    refresh_token = auth.create_refresh_token(user.email)
    return {"access_token": access_token, "refresh_token": refresh_token, "user_no": user.user_no}

# 프로필 등록
@router.post("/profile-create/{user_no}", summary="프로필 등록")
async def profile_create_route(
    user_no: int,
    nickname: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):

    # 사용자 권한 확인
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to create this profile.")

    # 기존 프로필이 있는지 확인
    existing_profile = crud.get_profile_by_user_no(db=db, user_no=user_no)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user.")

    profile_data = schema.ProfileCreate(nickname=nickname)
    profile = crud.create_user_profile(db=db, user_no=user_no, profile_data=profile_data, file=file)
    
    return {"msg": "Profile created successfully", "user_no": user_no}

# 사용자 정보 + 프로필 조회
@router.get("/profile/{user_no}", response_model=schema.UserInfo, summary="프로필 조회")
def profile_read_route(
    user_no: int,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    # 사용자 권한 확인
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to view this profile.")

    user_info = crud.get_user_info_with_profile(db=db, user_no=user_no)

    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")

    return user_info

# 프로필 이미지 조회
@router.get("/profile-image/{user_no}", summary="프로필 이미지 조회")
def get_profile_image(user_no: int, db: Session = Depends(get_db)):
    profile = crud.get_profile_by_user_no(db, user_no=user_no)
    if not profile or not profile.image_url:
        raise HTTPException(status_code=404, detail="Image file not found")

    image_path = os.path.join(PROFILE_IMAGE_DIR, os.path.basename(profile.image_url))

    # 이미지 파일이 실제로 존재하는지 확인
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # 파일 확장자에 따라 media_type 설정
    file_extension = os.path.splitext(image_path)[1].lower()
    media_type = "image/jpeg" if file_extension == ".jpg" or file_extension == ".jpeg" else "image/png"

    return Response(content=image_data, media_type=media_type)

# 프로필 수정
@router.put("/profile-update/{user_no}", summary="프로필 수정")
async def profile_update_route(
    user_no: int,
    nickname: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),  # 이미지 파일은 선택 사항
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(auth.get_current_user)
):
    if user_no != current_user.user_no:
        raise HTTPException(status_code=403, detail="You do not have permission to update this profile.")

    profile_data = schema.ProfileUpdate(nickname=nickname)
    updated_profile = crud.profile_update(db=db, user_no=user_no, profile_data=profile_data, file=file)
    
    return {"msg": "Profile updated successfully", "profile": updated_profile}

# 비밀번호 변경
@router.put("/change-password", summary="비밀번호 변경")
def change_password_route(password_data: schema.ChangePassword, db: Session = Depends(get_db), current_user: schema.User = Depends(auth.get_current_user)):
    # 세션에 현재 사용자를 병합하여 세션 내에서 지속되도록 보장
    current_user = db.merge(current_user)
    # 비밀번호 업데이트
    crud.update_user_password(
        db=db,
        user=current_user,
        password=password_data.password
    )
    return {"msg": "Password successfully changed"}
