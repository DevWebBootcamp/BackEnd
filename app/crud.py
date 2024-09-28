from sqlalchemy.orm import Session, joinedload
from app.model import MemberUser as member_user
from app.model import MemberProfile as member_profile 
from app.model import Storage_Area as storage_area
from app.model import Storage_Storage as storage_storage
from app.schema import (
    UserCreate,
    UserInfo,
    ProfileUpdate,
    ProfileCreate,
    StorageCreate,
    StorageUpdate,
    Storage,
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

# 사용자 프로필 조회
def get_profile_by_user_no(db: Session, user_no: int):
    return db.query(member_profile).filter(member_profile.user_no == user_no).first()


# 프로필 등록
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

# 사용자 정보 + 프로필 조회
def get_user_info(db: Session, user_no: int):
    user = (db.query(member_user).join(member_profile).filter(member_user.user_no == user_no).first())
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 사용자 정보와 프로필 정보를 함께 반환
    user_info = UserInfo(
        email=user.email,
        user_name=user.user_name,
        nickname=user.profile.nickname,
        cell_phone=user.cell_phone,
        birthday=user.birthday,
        gender=user.gender,
        image_url=user.profile.image_url,
    )
    
    return user_info

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

# 공간 추가
def create_storage_space(db: Session, user_no: int, area_name: str):
    storage_space = storage_area(
        user_no=user_no,
        area_name=area_name,
        area_created_date=member_user.get_kst_now(),
        storage_owner=True
    )
    db.add(storage_space)
    db.commit()
    db.refresh(storage_space)
    return storage_space

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

# 공간 수정
def update_storage_space(db: Session, user_no: int, area_no: int, area_name: str):
    storage_space = db.query(storage_area).filter(storage_area.user_no == user_no, storage_area.area_no == area_no).first()
    if not storage_space:
        raise HTTPException(status_code=404, detail="Storage area not found")
    
    storage_space.area_name = area_name
    db.commit()
    db.refresh(storage_space)
    return storage_space

# 공간 삭제
def delete_storage_space(db: Session, user_no: int, area_no: int):
    storage_space = db.query(storage_area).filter(storage_area.user_no == user_no, storage_area.area_no == area_no).first()
    if not storage_space:
        raise HTTPException(status_code=404, detail="Storage area not found")
    
    db.delete(storage_space)
    db.commit()
    return {"msg": "Storage space deleted successfully"}

# 사용자가 소유한 공간 목록을 반환하는 함수
def get_areas_by_user(db: Session, user_no: int):
    return db.query(storage_area).filter(storage_area.user_no == user_no).all()

# 가구 추가
def create_storage(db: Session, storage: StorageCreate):
    db_storage = storage_storage(
        area_no=storage.area_no,
        storage_name=storage.storage_name,
        storage_column=storage.storage_column,
        storage_row=storage.storage_row,
        storage_location=storage.storage_location,
        storage_description=storage.storage_description,
    )
    db.add(db_storage)
    db.commit()
    db.refresh(db_storage)
    return db_storage

# 가구 조회
def get_storage(db: Session, storage_no: int):
    storage = (
       db.query(storage_storage).filter(storage_storage.storage_no == storage_no).first()
    )
    
    if not storage:
        raise HTTPException(status_code=404, detail="Storage not found")
    
    return storage

# 특정 공간에 있는 모든 가구 조회
def get_storages_by_area(db: Session, area_no: int):
    # 특정 공간에 있는 모든 가구 조회
    storages = db.query(storage_storage).filter(storage_storage.area_no == area_no).all()
    return storages


# 가구 수정
def update_storage(db: Session, storage_no: int, storage_data: StorageUpdate):
    db_storage = get_storage(db, storage_no)
    if not db_storage:
        raise HTTPException(status_code=404, detail="Storage not found")
    
    for key, value in storage_data.dict(exclude_unset=True).items():
        setattr(db_storage, key, value)
    db.commit()
    db.refresh(db_storage)
    return db_storage

# 가구 삭제
def delete_storage(db: Session, storage_no: int):
    db_storage = get_storage(db, storage_no)
    if not db_storage:
        raise HTTPException(status_code=404, detail="Storage not found")
    
    db.delete(db_storage)
    db.commit()
    return {"msg": "Storage deleted successfully"}