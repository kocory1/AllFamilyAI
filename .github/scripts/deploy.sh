#!/bin/bash
set -e

OPENAI_API_KEY=$1

echo "=========================================="
echo "온식구 AI 서버 배포 시작"
echo "시작 시간: $(date)"
echo "=========================================="

# 기존 서버 종료
echo "1. 기존 서버 종료 중..."
pkill -f "uvicorn app.main:app" || true
sleep 2

# 기존 프로젝트 완전 삭제
echo "2. 기존 프로젝트 삭제 중..."
rm -rf ~/onsikgu_ai

# 프로젝트 새로 클론
echo "3. 프로젝트 클론 중..."
cd ~
git clone https://github.com/kocory1/AllFamilyAI.git onsikgu_ai
cd onsikgu_ai/ai_server

# python3-venv 설치
echo "4. Python venv 설치 확인 중..."
sudo apt install -y python3.12-venv

# 가상환경 생성
echo "5. 가상환경 생성 중..."
python3 -m venv venv

# 가상환경 활성화 및 의존성 설치
echo "6. 의존성 설치 중..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 환경변수 파일 생성
echo "7. 환경변수 설정 중..."
cat > .env << EOF
OPENAI_API_KEY=${OPENAI_API_KEY}
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DEFAULT_MODEL=gpt-5-nano
MAX_TOKENS=4000
TEMPERATURE=0.8
MAX_QUESTION_LENGTH=200
PROFILE_DECAY=0.9
PROFILE_CATEGORY_GAIN=0.25
PROFILE_TAG_GAIN=0.15
PROFILE_TONE_GAIN=0.1
PROFILE_TABOO_THRESHOLD=0.6
PROFILE_TABOO_PENALTY=0.2
PROFILE_ALPHA_LENGTH=0.5
PROFILE_TOP_N_PRUNE=10
EOF

# 서버 시작 (별도 스크립트로 분리하여 백그라운드 실행)
echo "8. 서버 시작 중..."
cd ~/onsikgu_ai/ai_server

# 서버 시작 스크립트 생성
cat > ~/start_server.sh << 'STARTEOF'
#!/bin/bash
cd ~/onsikgu_ai/ai_server
~/onsikgu_ai/ai_server/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1
STARTEOF

chmod +x ~/start_server.sh

# 백그라운드에서 서버 시작 (nohup + setsid + 리다이렉션)
nohup setsid bash ~/start_server.sh < /dev/null > /dev/null 2>&1 &

sleep 3

# 서버 시작 확인
if pgrep -f "uvicorn app.main:app" > /dev/null; then
  echo "✅ 서버가 성공적으로 시작되었습니다."
else
  echo "⚠️  서버 시작 대기 중... (로그 확인: tail -f ~/onsikgu_ai/ai_server/server.log)"
fi

echo "=========================================="
echo "배포 완료!"
echo "로그 확인: tail -f ~/onsikgu_ai/ai_server/server.log"
echo "완료 시간: $(date)"
echo "=========================================="

