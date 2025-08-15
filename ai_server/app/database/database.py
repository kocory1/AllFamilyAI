from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import settings

# PostgreSQL 비동기 엔진 생성
engine = create_async_engine(
    settings.database_url,
    echo=True,  # 개발 시 SQL 쿼리 로깅
    future=True
)

# 세션 팩토리 생성
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """
    데이터베이스 세션을 가져오는 의존성 함수
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    데이터베이스 테이블 초기화
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        