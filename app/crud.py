from sqlalchemy.orm import Session, joinedload
from app.model import MemberUser as member_user
from app.model import MemberProfile as member_profile 
from app.model import Storage_Area as storage_area
from app.model import Storage_Storage as storage_storage
from app.model import Detail_Storage as detail_storage
from app.model import Item as db_item
from app.schema import (
    UserCreate,
    UserInfo,
    ProfileUpdate,
    ProfileCreate,
    StorageCreate,
    StorageUpdate,
    Storage,
    DetailStorageCreate, 
    DetailStorageUpdate, 
    ItemCreate, 
    ItemUpdate
)
from fastapi import HTTPException
import base64
import shutil
import os
from typing import Optional
from fastapi import UploadFile

# 이미지 파일을 저장할 경로
IMAGE_DIR = "images/profile/"

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


# 프로필 등록
def create_user_profile(db: Session, user_no: int, profile_data: ProfileCreate, image_url: str):
    user = get_user_by_no(db, user_no=user_no)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_profile = get_profile_by_user_no(db=db, user_no=user_no)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user.")

    profile = member_profile(
        user_no=user_no,
        nickname=profile_data.nickname,
        image_url=image_url,  # 이미지 URL 저장
        create_date=member_user.get_kst_now()
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
    
# 프로필 조회 // 이미지 조회에 필요
def get_profile_by_user_no(db: Session, user_no: int):
    return db.query(member_profile).filter(member_profile.user_no == user_no).first()

# 사용자 정보 + 프로필 조회
def get_user_info_with_profile(db: Session, user_no: int) -> UserInfo:
    user = get_user_by_no(db, user_no)
    profile = get_profile_by_user_no(db, user_no)

    if not user or not profile:
        raise HTTPException(status_code=404, detail="User or profile not found")

    return UserInfo(
        email=user.email,
        user_name=user.user_name,
        nickname=profile.nickname,
        cell_phone=user.cell_phone,
        birthday=user.birthday,
        gender=user.gender,
         image_url=f"/images/profile/{os.path.basename(profile.image_url)}" if profile.image_url else None
    )

# 프로필 수정
def profile_update(db: Session, user_no: int, profile_data: ProfileUpdate, image_url: Optional[UploadFile] = None):
    user = get_user_by_no(db, user_no=user_no)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile_data.nickname is not None:
        profile.nickname = profile_data.nickname

    # 새 이미지가 업로드된 경우 파일을 저장하고 URL 갱신
    if image_url:
        unique_filename = f"{uuid.uuid4().hex}_{image_url.filename}"
        image_path = os.path.join(IMAGE_UPLOAD_DIR, unique_filename)
        
        with open(image_path, "wb") as image:
            shutil.copyfileobj(image_file.file, image)
        
        profile.image_url = f"/images/profile/{unique_filename}"

    # 수정 시각 업데이트
    profile.update_date = member_user.get_kst_now()
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

# 모든 공간 조회
def load_user_storage_space(db: Session, user_no: int):
    spaces = (
        db.query(storage_area)
        .filter(storage_area.user_no == user_no, storage_area.storage_owner == True)
        .all()
    )

    if not spaces:
        raise HTTPException(status_code=404, detail="No storage spaces found for this user with the given area_no")
    return spaces


# 특정 공간 조회
def get_user_storage_space(db: Session, user_no: int, area_no: int):
    # user_no와 area_no 일치하는 특정 공간을 조회
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

# 상세 저장 위치 추가
def create_detail_storage(db: Session, storage_no: int, detail_storage_name: str, storage_description: str = None):
    
    storage = db.query(storage_storage).filter(storage_storage.storage_no == storage_no).first()

    if not storage:
        raise HTTPException(status_code=404, detail="Storage not found")

    area_no = storage.area_no
    
    # Detail_Storage 객체 생성
    db_detail_storage = detail_storage(
        area_no=area_no,
        storage_no=storage_no,
        detail_storage_name=detail_storage_name,
        storage_description=storage_description,
        storage_created_date=member_user.get_kst_now(),
    )
    db.add(db_detail_storage)
    db.commit()
    db.refresh(db_detail_storage)
    return db_detail_storage

# 상세 저장 위치 조회
def get_detail_storage(db: Session, detail_storage_no: int):
    db_detail_storage = (
       db.query(detail_storage).filter(detail_storage.detail_storage_no == detail_storage_no).first()
    )

    if not db_detail_storage:
        raise HTTPException(status_code=404, detail="Detail storage not found")
    
    return db_detail_storage

# 사용자가 소유한 모든 상세 저장 위치 조회
def get_all_detail_storages_by_user(db: Session, user_no: int):
    # 사용자의 모든 공간(area_no)을 가져온 후 그 공간들에 포함된 상세 저장 위치 조회
    user_areas = db.query(storage_area.area_no).filter(storage_area.user_no == user_no).all()
    area_nos = [area.area_no for area in user_areas]  # area_no 목록 추출
    
    # 해당 사용자가 소유한 모든 상세 저장 위치 반환
    return db.query(detail_storage).filter(detail_storage.area_no.in_(area_nos)).all()

# 상세 저장 위치 수정
def update_detail_storage(db: Session, detail_storage_no: int, detail_storage_data: DetailStorageUpdate):
    db_detail_storage = get_detail_storage(db, detail_storage_no)
    if not db_detail_storage:
        raise HTTPException(status_code=404, detail="Detail storage not found")
    
    for key, value in detail_storage_data.dict(exclude_unset=True).items():
        setattr(db_detail_storage, key, value)
    db.commit()
    db.refresh(db_detail_storage)
    return db_detail_storage

# 상세 저장 위치 삭제
def delete_detail_storage(db: Session, detail_storage_no: int):
    db_detail_storage = get_detail_storage(db, detail_storage_no)
    if not db_detail_storage:
        raise HTTPException(status_code=404, detail="Detail storage not found")
    
    db.delete(db_detail_storage)
    db.commit()
    return {"msg": "Detail storage deleted successfully"}

# 물건 추가
def create_item(db: Session, item: ItemCreate):
    # 먼저 detail_storage_no가 존재하는지 확인
    detail_storage_instance = db.query(detail_storage).filter(detail_storage.detail_storage_no == item.detail_storage_no).first()
    if not detail_storage_instance:
        raise HTTPException(status_code=404, detail="Detail storage not found")
    
    # db_item 객체 생성
    db_item_instance = db_item(
        detail_storage_no=item.detail_storage_no,
        item_name=item.item_name,
        item_type=item.item_type,
        item_quantity=item.item_quantity,
    )
    db.add(db_item_instance)
    db.commit()
    db.refresh(db_item_instance)
    return db_item_instance

# 물건 조회
def get_item(db: Session, item_id: int):
    db_item_instance = db.query(db_item).filter(db_item.item_id == item_id).first()
    if not db_item_instance:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item_instance

# 물건 수정
def update_item(db: Session, item_id: int, item_data: ItemUpdate):
    db_item_instance = get_item(db, item_id)
    if not db_item_instance:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item_data.dict(exclude_unset=True).items():
        setattr(db_item_instance, key, value)
    db.commit()
    db.refresh(db_item_instance)
    return db_item_instance

# 물건 삭제
def delete_item(db: Session, item_id: int):
    db_item_instance = get_item(db, item_id)
    if not db_item_instance:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item_instance)
    db.commit()
    return {"msg": "Item deleted successfully"}