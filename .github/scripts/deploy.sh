#!/bin/bash
set -e

OPENAI_API_KEY=$1
LANGCHAIN_API_KEY=$2
LANGCHAIN_PROJECT=${3:-"onsikgu-ai"}

echo "=========================================="
echo "온식구 AI 서버 배포 시작"
echo "시작 시간: $(date)"
echo "=========================================="

# 기존 서버 종료
echo "1. 기존 서버 종료 중..."
pkill -f "uvicorn app.main:app" || true
pkill -f "poetry install" || true  # Poetry 프로세스도 종료
sleep 2

# 데이터 디렉토리 확인 (프로젝트 외부, 영구 보존)
echo "2. 데이터 디렉토리 확인 중..."
if [ -d ~/onsikgu_data/chroma ]; then
  echo "   ✅ 기존 데이터 디렉토리 발견! (데이터 보존됨)"
  echo "   📊 현재 데이터 크기: $(du -sh ~/onsikgu_data/chroma 2>/dev/null | cut -f1 || echo '계산 불가')"
else
  echo "   🆕 새로운 데이터 디렉토리 생성 중..."
  mkdir -p ~/onsikgu_data/chroma
  chmod 755 ~/onsikgu_data/chroma
  echo "   ✅ 데이터 디렉토리 생성 완료"
fi
echo "   데이터 경로: ~/onsikgu_data/chroma"

# 기존 프로젝트 완전 삭제 (데이터는 외부 폴더에 있으므로 안전!)
echo "3. 기존 프로젝트 삭제 중..."
rm -rf ~/onsikgu_ai

# 프로젝트 새로 클론
echo "4. 프로젝트 클론 중..."
cd ~
git clone https://github.com/kocory1/AllFamilyAI.git onsikgu_ai
cd onsikgu_ai/ai_server

# Poetry 설치
echo "5. Poetry 설치 확인 중..."
if ! command -v poetry &> /dev/null; then
  echo "   📦 Poetry 설치 중..."
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
  echo "   ✅ Poetry 설치 완료"
else
  echo "   ✅ Poetry 이미 설치됨"
fi

# Poetry 경로 설정
export PATH="$HOME/.local/bin:$PATH"

# 의존성 설치 (Poetry)
echo "6. 의존성 설치 중 (Poetry)..."
poetry install --no-interaction --no-ansi --without dev

# nginx 설치 및 설정
echo "7. nginx 설치 및 설정 중..."
if ! command -v nginx &> /dev/null; then
  echo "   📦 nginx 설치 중..."
  sudo apt update
  sudo apt install -y nginx
  echo "   ✅ nginx 설치 완료"
else
  echo "   ✅ nginx 이미 설치됨"
fi

# nginx 설정 파일 복사
echo "   📝 nginx 설정 파일 적용 중..."
sudo cp ~/onsikgu_ai/.github/scripts/nginx_onsikgu.conf /etc/nginx/sites-available/onsikgu_ai

# 심볼릭 링크 생성 (활성화)
if [ ! -L /etc/nginx/sites-enabled/onsikgu_ai ]; then
  sudo ln -s /etc/nginx/sites-available/onsikgu_ai /etc/nginx/sites-enabled/
  echo "   ✅ nginx 사이트 활성화 완료"
fi

# 기본 nginx 사이트 비활성화 (충돌 방지)
if [ -L /etc/nginx/sites-enabled/default ]; then
  sudo rm /etc/nginx/sites-enabled/default
  echo "   ✅ 기본 사이트 비활성화 완료"
fi

# nginx 설정 테스트
if sudo nginx -t; then
  echo "   ✅ nginx 설정 검증 완료"
  sudo systemctl reload nginx || sudo systemctl restart nginx
  echo "   ✅ nginx 재시작 완료"
else
  echo "   ⚠️  nginx 설정 오류 발생 (계속 진행)"
fi

# 환경변수 파일 생성
echo "8. 환경변수 설정 중..."
cd ~/onsikgu_ai/ai_server
cat > .env << EOF
# OpenAI API
OPENAI_API_KEY=${OPENAI_API_KEY}

# Langsmith (AI Tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT}

# 서버 설정
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO

# AI 모델 설정
DEFAULT_MODEL=gpt-4o-mini
MAX_TOKENS=10000
TEMPERATURE=0.8
MAX_QUESTION_LENGTH=90

# ChromaDB 설정 (RAG용 벡터 DB)
CHROMA_PERSIST_DIRECTORY=/home/ubuntu/onsikgu_data/chroma
CHROMA_COLLECTION_NAME=qa_history
EMBEDDING_MODEL=text-embedding-3-small
RAG_TOP_K=5
RAG_MIN_ANSWERS=5
EOF

# 서버 시작 (Poetry 사용)
echo "9. 서버 시작 중 (Poetry)..."
cd ~/onsikgu_ai/ai_server

# Poetry 경로 확인
export PATH="$HOME/.local/bin:$PATH"

# nohup으로 백그라운드 실행 (Poetry 사용)
nohup poetry run uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  > ~/onsikgu_ai/ai_server/server.log 2>&1 &

echo "   서버 PID: $!"
sleep 3

# Health Check (재시도 로직)
echo "10. Health Check 시작 (최대 50초 대기)..."
MAX_RETRIES=10
RETRY_INTERVAL=5

for i in $(seq 1 $MAX_RETRIES); do
  echo "   Health check attempt $i/$MAX_RETRIES..."
  
  if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Server is up!"
    echo "   ✅ Health Check 성공 (시도 횟수: $i/$MAX_RETRIES)"
    break
  fi
  
  if [ $i -eq $MAX_RETRIES ]; then
    echo "   ❌ Server failed to start after 50s."
    echo ""
    echo "=========================================="
    echo "🔍 서버 로그 (마지막 20줄):"
    echo "=========================================="
    tail -20 ~/onsikgu_ai/ai_server/server.log
    echo "=========================================="
    echo ""
    echo "전체 로그: tail -f ~/onsikgu_ai/ai_server/server.log"
    exit 1
  fi
  
  sleep $RETRY_INTERVAL
done

# 서버 시작 확인
if pgrep -f "uvicorn app.main:app" > /dev/null; then
  echo "✅ 서버가 정상적으로 실행 중입니다."
else
  echo "⚠️  서버 프로세스를 찾을 수 없습니다. (로그 확인 필요)"
  exit 1
fi

echo "=========================================="
echo "배포 완료!"
echo "📍 서버: http://3.38.113.60"
echo "📝 Health: http://3.38.113.60/health"
echo "📚 API 문서: http://3.38.113.60/docs"
echo "로그 확인: tail -f ~/onsikgu_ai/ai_server/server.log"
echo "완료 시간: $(date)"
echo "=========================================="

