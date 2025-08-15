from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from app.routers import question_router, mcp_router, answers_router, family_router
from app.core.config import settings
from app.database.database import init_db

# 환경 변수 로드
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 데이터베이스 초기화
    await init_db()
    yield
    # 종료 시 정리 작업 (필요 시)

# FastAPI 앱 생성
app = FastAPI(
    title="온식구 AI 서버 (MCP 강화)",
    description="가족 유대감을 위한 AI 질문 생성 서버 - Model Context Protocol 지원",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(question_router.router, prefix="/api/v1", tags=["기본 질문"])
app.include_router(mcp_router.router, prefix="/api/v1", tags=["MCP 질문"])
app.include_router(answers_router.router, prefix="/api/v1", tags=["답변 관리"])
app.include_router(family_router.router, prefix="/api/v1", tags=["가족 관리"])

@app.get("/")
async def root():
    return {
        "message": "온식구 AI 서버에 오신 것을 환영합니다! 🏠", 
        "version": "2.0.0",
        "features": [
            "기본 질문 생성",
            "MCP 기반 개인화 질문",
            "후속 질문 생성",
            "테마별 질문 생성",
            "가족 패턴 분석",
            "대화 효과성 분석"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "온식구 AI 서버 (MCP 강화)", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    ) 