import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

# Clean Architecture Router
from app.presentation.routers import question_router

# 환경 변수 로드
load_dotenv()

# Langsmith 환경변수 설정 (Langchain이 자동으로 읽음)
os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

# 로거 설정
logger = logging.getLogger(__name__)

# Langsmith 활성화 여부 로깅
if settings.langchain_tracing_v2.lower() == "true":
    logger.info(f"✅ Langsmith 추적 활성화: project={settings.langchain_project}")
else:
    logger.info("⚠️  Langsmith 추적 비활성화 (LANGCHAIN_TRACING_V2=false)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작/종료 훅 (DB 미사용 모드)
    yield


# FastAPI 앱 생성
app = FastAPI(
    title="온식구 AI 서버",
    description="가족 유대감을 위한 AI 질문 생성 서버",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Validation 에러 핸들러 (422 에러 상세 로깅)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"[422 Validation Error] method={request.method}, path={request.url.path}")
    logger.error(f"[422 Validation Error] body={body.decode('utf-8') if body else 'empty'}")
    logger.error(f"[422 Validation Error] errors={exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "요청 데이터 검증에 실패했습니다."},
    )


# 라우터 등록 (Clean Architecture)
app.include_router(question_router.router, prefix="/api/v1", tags=["질문 생성"])


@app.get("/")
async def root():
    return {
        "message": "온식구 AI 서버에 오신 것을 환영합니다! 🏠",
        "version": "2.0.0",
        "architecture": "Clean Architecture (DDD + TDD)",
        "endpoints": {
            "personal": "/api/v1/questions/generate/personal",
            "family": "/api/v1/questions/generate/family",
            "family-recent": "/api/v1/questions/generate/family-recent",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "온식구 AI 서버", "version": "2.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
