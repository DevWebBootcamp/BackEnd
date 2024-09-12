from sqlalchemy.orm import Session, joinedload
from app.model import MemberUser as member_user
from app.model import MemberProfile as member_profile 
from app.model import Storage_Area as storage_area
from app.schema import (
    UserCreate,
    ProfileUpdate,
    ProfileCreate
)
from fastapi import HTTPException

def get_user_by_no(db: Session, user_no: int):
    return db.query(member_user).filter(member_user.user_no == user_no).first()


def get_user_by_email(db: Session, email: str):
    return db.query(member_user).filter(member_user.email == email).first()

# 전화번호로 사용자 조회
def get_user_by_phone(db: Session, cell_phone: str):
    return (
        db.query(member_user)
        .filter(member_user.cell_phone == cell_phone)
        .first()
    )

# 회원가입
def create_user(db: Session, user: UserCreate, verification_code: str):
    hashed_password = member_user.get_password_hash(user.password)  # 비밀번호 해싱
    db_user = member_user(
        email=user.email,
        password=hashed_password,
        user_name=user.user_name,
        cell_phone=user.cell_phone,
        birthday=user.birthday,
        gender=user.gender,
        user_registrationDate=member_user.get_kst_now(),
        user_isDisabled=True,
        verification_code=verification_code  # 인증 코드 저장
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 로그인
def authenticate_user(db: Session, user_email: str, password: str):
    # 사용자 조회
    db_user = get_user_by_email(db, email=user_email)
    # 비밀번호 검증
    if db_user and db_user.verify_password(password):
        return db_user
    return None

def create_user_profile(db: Session, user_no: int, profile_data: ProfileCreate):
    user = get_user_by_no(db, user_no=user_no)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = member_profile (
        user_no=user_no,
        nickname=profile_data.nickname,
        image_url=profile_data.image_url,
        create_date=member_user.get_kst_now()
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


# 프로필 수정
def profile_update(db:Session, user_no: int, profile_data:ProfileUpdate):
    user = get_user_by_no(db, user_no=user_no)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if profile_data.nickname is not None:
        profile.nickname = profile_data.nickname
    if profile_data.image_url is not None:
        profile.image_url = profile_data.image_url
    
    profile.update_date = member_user.get_kst_now()  # 사용자 정보 수정 시각 업데이트
    db.commit()
    db.refresh(profile)
    
    return profile

# 비밀번호 변경
def update_user_password(db: Session, user: member_user, password: str):
    hashed_password = member_user.get_password_hash(password)
    user.password = hashed_password
    db.commit()
    return user

# 공간 조회
def get_user_storage_space(db: Session, user_no: int, area_no: int):
    # user_no와 area_no 일치하는 공간을 조회
    space = (
        db.query(storage_area)
        .filter(storage_area.user_no == user_no, storage_area.area_no == area_no, storage_area.storage_owner == True)
        .first()
    )
    
    if not space:
        raise HTTPException(status_code=404, detail="No storage space found for this user with the given area_no")
    
    return space

