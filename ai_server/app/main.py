# ruff: noqa: E402  # P0: load_dotenv() must run before other imports
from dotenv import load_dotenv

load_dotenv()

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

# Clean Architecture Router
from app.presentation.routers import question_router, summary_router

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
    # 시작 훅: 첫 요청 전에 의존성(Chroma/체인) 초기화
    # - 첫 요청에서 터지지 않게 fail-fast
    # - 권한/경로 문제를 부팅 단계에서 바로 발견
    # - 실패 시 로그에 전체 traceback 남김 (502 원인 확인: docker logs <container>)
    logger.info("[lifespan] startup: initializing dependencies (chroma + generators)")
    try:
        # Chroma persist directory 쓰기 가능 여부 확인 (권한 이슈 조기 감지)
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        write_test_path = persist_dir / ".write_test"
        try:
            write_test_path.write_text("ok", encoding="utf-8")
            write_test_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(
                f"[lifespan] chroma persist dir not writable: {persist_dir}", exc_info=True
            )
            raise RuntimeError(f"Chroma persist directory is not writable: {persist_dir}") from e

        # DI 싱글톤 생성(초기화) 트리거
        from app.presentation.dependencies import (
            get_chroma_collection,
            get_family_generator,
            get_personal_generator,
            get_summary_generator,
            get_vector_store,
        )

        get_chroma_collection()
        get_vector_store()
        get_personal_generator()
        get_family_generator()
        get_summary_generator()

        logger.info("[lifespan] startup: initialization complete")
    except Exception:
        logger.exception("[lifespan] startup failed (502 원인 확인: docker logs <container>)")
        raise

    yield
    logger.info("[lifespan] shutdown")


# FastAPI 앱 생성
app = FastAPI(
    title="온식구 AI 서버",
    description="가족 유대감을 위한 AI 질문 생성 서버",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 설정 (cors_allowed_origins: "*" 또는 쉼표 구분 목록, 운영에서는 구체적 origin 권장)
_cors_origins = (
    ["*"]
    if settings.cors_allowed_origins.strip() == "*"
    else [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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
app.include_router(question_router.router, prefix="/api/v1")
app.include_router(summary_router.router, prefix="/api/v1")


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
            "summary": "/api/v1/summary",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "온식구 AI 서버", "version": "2.0.0"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
