#!/usr/bin/env python3
"""
온식구 AI 서버 실행 스크립트
"""

import uvicorn
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    print("🏠 온식구 AI 서버를 시작합니다...")
    print(f"📍 서버 주소: http://{settings.host}:{settings.port}")
    print(f"📚 API 문서: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=["app"],  # app 폴더만 감시
        reload_excludes=["venv/*", "*/venv/*"],  # venv 폴더 제외
        log_level=settings.log_level.lower()
    ) 