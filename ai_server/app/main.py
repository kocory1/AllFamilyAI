import logging
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers import question_router

# 환경 변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


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
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용 # 배포시 변경해라 !!!!!!!!!!!!!!!!!
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


# 라우터 등록 (기본 OpenAI 질문 생성만 제공)
app.include_router(question_router.router, prefix="/api/v1", tags=["기본 질문"])


@app.get("/")
async def root():
    return {
        "message": "온식구 AI 서버에 오신 것을 환영합니다! 🏠",
        "version": "2.0.0",
        "features": ["기본 질문 생성"],
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "온식구 AI 서버", "version": "2.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
