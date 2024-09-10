# Pydantic을 사용하여 요청과 응답 스키마 정의
from pydantic import BaseModel, EmailStr, Field, constr, HttpUrl, validator
from enum import Enum
from typing import Optional
from datetime import datetime, date, time


# gender를 위한 Enum 정의
class GenderTypeEnum(str, Enum):
    male = "남성"
    female = "여성"
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


# UserCreate의 확장으로 추가 데이터 없이 모든 속성 상속
class User(UserInDB):
    pass

class ProfileCreate(BaseModel):
    nickname: Optional[str] = None
    image_url: Optional[str] = None


class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    image_url: Optional[str] = None

class ChangePassword(BaseModel):
    password: constr(max_length=128)