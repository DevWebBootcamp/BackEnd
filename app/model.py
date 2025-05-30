from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,   # DB의 테이블 정의에 사용되는 것
    Date,
    ForeignKey,
    Time,
    Enum,
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime   # 날짜 및 시간 데이터의 생성과 계산을 위한 것
from passlib.context import CryptContext
import pytz

# 비밀번호 해싱을 위한 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 사용자 정보 테이블
class MemberUser(Base):
    __tablename__ = "member_user"  # 데이터베이스에서 사용할 테이블 이름

    user_no = Column(Integer, primary_key=True)
    email = Column(String(128), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    #salt = Column(String(128), nullable=False)
    user_name = Column(String(20), nullable=False)
    cell_phone = Column(String(11), nullable=False, unique=True) 
    birthday = Column(DateTime, nullable=False)
    gender = Column(Enum("남성", "여성", "기타" ,name="gender_type"), nullable=False)

    user_isDisabled = Column(Boolean, default=False)  # 계정 비활성화 여부, 기본값은 False 
    user_registrationDate = Column(DateTime, nullable=False)  # 가입일자
    verification_code = Column(String(6), nullable=True)  # 인증 코드

     # 관계 설정
    profile = relationship("MemberProfile", uselist=False, back_populates="user")
    social_logins = relationship("AuthSocialLogin", back_populates="user")

    # 비밀번호 검증 메소드
    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.password)

    # 비밀번호 해싱(정적 메소드)
    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

    # UTC 시간을 KST로 변환
    @staticmethod
    def get_kst_now():
        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=pytz.utc)  # 현재 시각을 UTC로 설정
        kst_now = utc_now.astimezone(pytz.timezone("Asia/Seoul"))  # KST 시간대로 변환
        return kst_now

# 사용자 프로필 테이블
class MemberProfile(Base):
    __tablename__ = "member_profile"

    profile_id = Column(Integer, primary_key=True)
    user_no = Column(Integer, ForeignKey('member_user.user_no'))
    nickname = Column(String(12))
    image_url = Column(String(100), nullable=True)  # 이미지 파일 URL 저장
    update_date = Column(DateTime)
    create_date = Column(DateTime)

    user = relationship("MemberUser", back_populates="profile")

# 소셜 로그인 테이블
class AuthSocialLogin(Base):
    __tablename__ = "auth_social_login"

    social_login_id = Column(Integer, primary_key=True)
    user_no = Column(Integer, ForeignKey('member_user.user_no'))
    social_code = Column(Integer)
    external_id = Column(String(64))
    access_token = Column(String(256))  #없어도 되나?
    refresh_token = Column(String(256)) #

    user = relationship("MemberUser", back_populates="social_logins")

# 공간 테이블
class Storage_Area(Base):
    __tablename__ = "storage_area"

    area_no = Column(Integer, primary_key=True, nullable=False)
    user_no = Column(Integer, ForeignKey('member_user.user_no'))
    area_name = Column(String(50), nullable=False)
    area_created_date = Column(DateTime, nullable=False)
    storage_owner = Column(Boolean, default=True)

    rooms = relationship("Storage_Room", back_populates="storage_area")

# 방 테이블
class Storage_Room(Base):
    __tablename__ = "storage_room"

    room_no = Column(Integer, primary_key=True)
    area_no = Column(Integer, ForeignKey('storage_area.area_no'))
    room_name = Column(String(50), nullable=False)
    room_create_date = Column(DateTime, default=MemberUser.get_kst_now)
    room_modification_date = Column(DateTime, onupdate=MemberUser.get_kst_now)

    storage_area = relationship("Storage_Area", back_populates="rooms")
    storages = relationship("Storage_Storage", back_populates="room")

# 가구 테이블
class Storage_Storage(Base):
    __tablename__ = "storage_storage"

    storage_no = Column(Integer, primary_key=True, index=True)
    room_no = Column(Integer, ForeignKey('storage_room.room_no'))
    storage_name = Column(String(50), nullable=False)  
    storage_row = Column(Integer, nullable=False)  # 행
    storage_created_date = Column(DateTime, default=MemberUser.get_kst_now)  # 생성 날짜
    storage_modification_date = Column(DateTime, onupdate=MemberUser.get_kst_now)

    room = relationship("Storage_Room", back_populates="storages")
    items = relationship("Item", back_populates="storage")
    
# 물건 테이블
class Item(Base):
    __tablename__ = "item"

    item_id = Column(Integer, primary_key=True, index=True)
    storage_no = Column(Integer, ForeignKey("storage_storage.storage_no"))
    item_name = Column(String(50), nullable=False)
    row_num = Column(Integer, nullable=False) 
    item_imageURL = Column(String(100), nullable=True)
    item_type = Column(Enum("식품", "전자제품", "의류", "사무용품", "생활용품", "기타", name="item_type_enum"), nullable=False)
    item_quantity = Column(Integer, nullable=False, default=1)
    item_Expiration_date = Column(String(50), nullable=True)
    item_received_date = Column(DateTime, default=MemberUser.get_kst_now)
    item_modification_date = Column(DateTime, onupdate=MemberUser.get_kst_now)

    storage = relationship("Storage_Storage", back_populates="items")