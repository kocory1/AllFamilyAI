# 🚀 배포 체크리스트 (Clean Architecture)

## ✅ 배포 전 필수 확인 사항

### 1. 코드 품질 ✅
- [x] Linter 검사 통과 (`ruff check`)
- [x] 테스트 통과 (18 tests, 0.02s)
- [x] Legacy 코드 제거 완료
- [x] Clean Architecture 적용 완료

### 2. 환경 변수 설정 ✅
**GitHub Secrets에 다음 값이 설정되어 있어야 합니다:**
- `OPENAI_API_KEY` - OpenAI API 키
- `LANGCHAIN_API_KEY` - Langsmith API 키
- `LANGCHAIN_PROJECT` - Langsmith 프로젝트명 (기본: "onsikgu-ai")
- `EC2_HOST` - EC2 서버 IP
- `EC2_USER` - EC2 사용자명 (보통 "ubuntu")
- `EC2_SSH_KEY` - EC2 SSH 비밀키

### 3. 서버 환경 ✅
- [x] Python 3.11 설치
- [x] Poetry 설치 스크립트 포함
- [x] nginx 설정 포함
- [x] ChromaDB 데이터 디렉토리 분리 (`~/onsikgu_data/chroma`)

### 4. API 엔드포인트 ✅
```
POST /api/v1/questions/generate/personal  # Clean Architecture
POST /api/v1/questions/generate/family    # Clean Architecture
GET  /health                               # Health Check
GET  /docs                                 # API 문서 (Swagger)
```

---

## 🚀 배포 방법

### Option 1: GitHub Actions (자동 배포) ⭐ 추천
1. `main` 브랜치에 Push
2. CI Test 자동 실행
3. CI Test 성공 시 자동 배포
4. Health Check 자동 확인

```bash
git add .
git commit -m "Deploy Clean Architecture"
git push origin main
```

### Option 2: 수동 배포 (긴급 상황)
```bash
# EC2 서버 접속
ssh ubuntu@3.38.113.60

# 배포 스크립트 실행
cd ~
./deploy.sh "OPENAI_API_KEY" "LANGCHAIN_API_KEY" "onsikgu-ai"
```

---

## 🔍 배포 후 확인 사항

### 1. Health Check
```bash
curl http://3.38.113.60/health
# 응답: {"status":"healthy","service":"온식구 AI 서버","version":"2.0.0"}
```

### 2. API 테스트
```bash
curl -X POST http://3.38.113.60/api/v1/questions/generate/personal \
  -H "Content-Type: application/json" \
  -d '{
    "familyId": 1,
    "memberId": 10,
    "roleLabel": "첫째 딸",
    "baseQuestion": "오늘 뭐 했어?",
    "baseAnswer": "친구들과 놀았어요",
    "answeredAt": "2026-01-20T14:30:00Z"
  }'
```

### 3. 로그 확인
```bash
ssh ubuntu@3.38.113.60
tail -f ~/onsikgu_ai/ai_server/server.log
```

### 4. Langsmith 확인
- https://smith.langchain.com
- 프로젝트: `onsikgu-ai`
- Trace 확인

### 5. ChromaDB 데이터 확인
```bash
ssh ubuntu@3.38.113.60
du -sh ~/onsikgu_data/chroma
# 데이터가 축적되는지 확인
```

---

## ⚠️ 트러블슈팅

### 문제 1: Health Check 실패
**원인**: 서버 시작 실패 또는 포트 충돌

**해결**:
```bash
# 로그 확인
ssh ubuntu@3.38.113.60
tail -100 ~/onsikgu_ai/ai_server/server.log

# 프로세스 확인
ps aux | grep uvicorn

# 포트 확인
sudo netstat -tlnp | grep 8000
```

### 문제 2: 502 Bad Gateway (nginx)
**원인**: 백엔드 서버 응답 없음 (앱 기동 실패 또는 연결 불가)

**해결**:
```bash
# 1) Docker 사용 시: 컨테이너 로그에서 기동 실패 원인 확인 (lifespan 예외 등)
docker logs onsikgu-ai-server --tail 200
# 또는
docker compose -f ... logs ai-server --tail 200

# 2) 컨테이너가 재시작 루프인지 확인
docker ps -a   # STATUS가 Restarting이면 lifespan/기동 실패 가능성 높음

# 3) 호스트에서 앱 포트 직접 호출 (프록시 제외)
curl -s http://localhost:8000/health   # 실패 시 앱 자체 문제

# 4) nginx 상태 및 로그
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

**자주 나오는 기동 실패 원인**
- `Chroma persist directory is not writable` → 볼륨 경로 `chown 1000:1000` (또는 appuser uid)
- `OPENAI_API_KEY` 누락/오류 → env_file 또는 환경변수 확인
- `get_chroma_collection()` / LLM 초기화 예외 → 위 로그에 traceback 출력됨

### 문제 3: OpenAI API 에러
**원인**: API 키 미설정 또는 잘못된 키

**해결**:
```bash
# .env 파일 확인
ssh ubuntu@3.38.113.60
cat ~/onsikgu_ai/ai_server/.env | grep OPENAI_API_KEY

# 환경 변수 재설정 후 서버 재시작
pkill -f "uvicorn app.main:app"
cd ~/onsikgu_ai/ai_server
nohup poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 > server.log 2>&1 &
```

### 문제 4: ChromaDB Segmentation Fault
**원인**: NumPy 버전 충돌

**해결**: 이미 해결됨 (`numpy = "<2.0"` 설정)

---

## 📊 모니터링

### 1. 서버 상태
```bash
# 프로세스 확인
ps aux | grep uvicorn

# 메모리 사용량
free -h

# 디스크 사용량
df -h
```

### 2. API 성능
- Langsmith에서 Latency 확인
- 평균 응답 시간: ~2-3초 (LLM 호출 포함)

### 3. 데이터 축적
```bash
# ChromaDB 데이터 크기
du -sh ~/onsikgu_data/chroma

# 데이터 개수 (로그에서 확인)
grep "기존 데이터" ~/onsikgu_ai/ai_server/server.log | tail -1
```

---

## 🎯 배포 완료 확인

- [ ] Health Check 성공
- [ ] API 테스트 성공
- [ ] Langsmith Trace 확인
- [ ] ChromaDB 데이터 확인
- [ ] 로그 정상 확인

---

## 🚀 다음 단계

1. **프론트엔드 연동**
   - API 엔드포인트 업데이트
   - `/api/v1/questions/generate/personal`
   - `/api/v1/questions/generate/family`

2. **모니터링 설정**
   - CloudWatch 또는 Datadog
   - 에러 알림 설정

3. **성능 최적화**
   - 캐싱 전략
   - 인덱싱 최적화

4. **백업 설정**
   - ChromaDB 데이터 백업
   - 정기 스냅샷

---

**✅ 배포 준비 완료!**
