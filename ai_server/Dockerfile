# Multi-stage build for optimized image size
FROM python:3.11-slim AS builder

WORKDIR /app

# 빌드 도구 설치 (chroma-hnswlib 컴파일용)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
ENV POETRY_VERSION=2.3.0 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# 의존성 파일만 먼저 복사 (캐싱 최적화)
COPY pyproject.toml poetry.lock ./

# 의존성 설치 (개발 의존성 제외)
RUN poetry install --without dev --no-interaction --no-ansi

# 소스 코드 복사
COPY . .

# ============================================
# 런타임 스테이지 (경량화)
# ============================================
FROM python:3.11-slim

WORKDIR /app

# 런타임 필수 라이브러리만 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# builder에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 소스 코드 복사
COPY --from=builder /app /app

# 데이터 디렉토리 마운트 포인트
VOLUME ["/data/chroma"]

# 환경변수 기본값
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 비-root 유저로 실행 (보안)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 서버 시작
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
