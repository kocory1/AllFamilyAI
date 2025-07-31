from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

from app.routers import question_router
from app.core.config import settings

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="온식구 AI 서버",
    description="가족 유대감을 위한 AI 질문 생성 서버",
    version="1.0.0"
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
app.include_router(question_router.router, prefix="/api/v1", tags=["questions"])

@app.get("/")
async def root():
    return {"message": "온식구 AI 서버에 오신 것을 환영합니다! 🏠"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "온식구 AI 서버"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    ) 