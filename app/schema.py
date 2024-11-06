# Pydantic을 사용하여 요청과 응답 스키마 정의
from pydantic import BaseModel, EmailStr, Field, constr, HttpUrl, validator
from enum import Enum
from typing import Optional
from datetime import datetime, date, time
from fastapi import UploadFile


# gender를 위한 Enum 정의
class GenderTypeEnum(str, Enum):
    male = "남성"
    female = "여성"
    other = "기타"

# item_type을 위한 Enum 정의
class ItemTypeEnum(str, Enum):
    food = "식품"
    electronics = "전자제품"
    clothing = "의류"
    office_supplies = "사무용품"
    household_goods = "생활용품"
    other = "기타"

# 사용자 생성을 위한 필드 정의
class UserCreate(BaseModel):
    email: EmailStr  # 유효한 이메일 형식인지 검증
    password: constr(min_length=6, max_length=128)
    user_name: constr(max_length=20)
    cell_phone: constr(pattern=r"^\d{11}$")  # 숫자만 11자리
    birthday: datetime
    gender: GenderTypeEnum


class UserInDB(UserCreate):
    password: str  # DB에 저장된 해시된 비밀번호
    user_registrationDate: datetime = datetime.utcnow()  # 사용자 등록 날짜
    user_isDisabled: bool = True  # 계정 비활성화 여부

    class Config:
        from_attributes = True

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    verification_code: constr(max_length=6)

# UserCreate의 확장으로 추가 데이터 없이 모든 속성 상속
class User(UserInDB):
    pass

class UserInfo(BaseModel):
    email: EmailStr
    user_name: str
    nickname: Optional[str]
    cell_phone: str
    birthday: datetime
    gender: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileCreate(BaseModel):
    nickname: Optional[str] = None
    image_url: Optional[UploadFile] = None  # 이미지 파일 업로드 지원

class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    image_url: Optional[UploadFile] = None

class ChangePassword(BaseModel):
    password: constr(max_length=128)

class StorageAreaSchema(BaseModel):
    area_no: int
    user_no: int
    area_name: str
    area_created_date: datetime
    storage_owner: bool

    class Config: 
        from_attributes = True
        __dict__ = True

# 공간 추가
class StorageAreaCreate(BaseModel):
    area_name: str

# 공간 수정
class StorageAreaUpdate(BaseModel):
    area_name: str

# 방 추가
class RoomCreate(BaseModel):
    area_no: int
    room_name: str

# 방 수정
class RoomUpdate(BaseModel):
    room_name: Optional[str] = None

# 방 조회
class RoomSchema(BaseModel):
    room_no: int
    area_no: int
    room_name: str
    room_create_date: datetime
    room_modification_date: Optional[datetime]

    class Config:
        from_attributes = True


# 가구 추가
class StorageCreate(BaseModel):
    room_no: int
    storage_name: str
    storage_row: int
    storage_location: str
    storage_description: Optional[str] = None

# 가구 수정
class StorageUpdate(BaseModel):
    storage_name: Optional[str] = None
    storage_row: Optional[int] = None
    storage_location: Optional[str] = None
    storage_description: Optional[str] = None

# 가구 조회
class Storage(BaseModel):
    storage_no: int
    room_no: int
    storage_name: str
    storage_row: int
    storage_location: str
    storage_description: Optional[str]
    storage_created_date: datetime
    storage_modification_date: Optional[datetime] = None

    class Config:
        from_attributes = True

# 물건 추가
class ItemCreate(BaseModel):
    storage_no: int
    item_name: str
    item_type: ItemTypeEnum
    item_quantity: int = Field(..., gt=0)  # 1 이상만 허용
    row_num: Optional[int] = None  # 행 번호
    item_imageURL: Optional[str] = None  # 이미지 URL
    item_Expiration_date: Optional[date] = None

# 물건 수정
class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_type: Optional[ItemTypeEnum] = None
    item_quantity: Optional[int] = Field(None, gt=0)
    row_num: Optional[int] = None
    item_imageURL: Optional[str] = None 
    item_Expiration_date: Optional[date] = None
