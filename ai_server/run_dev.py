#!/usr/bin/env python3
"""
온식구 AI 서버 개발용 실행 스크립트 (reload 없음)
"""

import uvicorn
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    print("🏠 온식구 AI 서버를 시작합니다... (개발 모드)")
    print(f"📍 서버 주소: http://{settings.host}:{settings.port}")
    print(f"📚 API 문서: http://{settings.host}:{settings.port}/docs")
    print("🔄 자동 재시작 비활성화됨 (수동으로 재시작 필요)")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # reload 비활성화
        log_level=settings.log_level.lower()
    ) 