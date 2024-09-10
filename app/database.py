from sqlalchemy import create_engine  # SQLAlchemy 엔진을 생성하기 위한 모듈
from sqlalchemy.ext.declarative import (
    declarative_base,
)  # 모델 클래스를 선언하는 기본 클래스 생성
from sqlalchemy.orm import sessionmaker  # 데이터베이스 세션 생성을 위한 세션메이커
from dotenv import load_dotenv
import os

# .env 파일의 환경 변수를 불러옴
load_dotenv()

# .env 파일에서 데이터베이스 URL 환경 변수 가져오기
SQLALCHEMY_DATABASE_URL = os.getenv("DB_ADDRESS")


# 데이터베이스 엔진 생성
# SQLAlchemy 엔진은 데이터베이스와의 모든 통신을 처리
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 세션 로컬 클래스 생성
# 이 클래스는 실제 데이터베이스 세션을 생성하며, 각 요청에 대해 새 세션 인스턴스를 제공
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# declarative_base 인스턴스 생성
# 이 인스턴스는 모든 모델 클래스가 상속받는 기본 클래스 역할을 하며, ORM 모델을 정의
Base = declarative_base()


# 데이터베이스 테이블 생성 함수 -> 메인 모듈 또는 시작점에서 이 부분을 호출
def create_tables():
    # Base.metadata.create_all을 호출하여 연결된 데이터베이스 엔진에 모든 테이블을 생성
    Base.metadata.create_all(bind=engine)