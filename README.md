# AllFamilyAI (온식구)

가족 대화 기록을 활용한 **맞춤형 후속 질문 생성** 및 주간/월간 요약을 제공하는 AI 백엔드 프로젝트입니다.  
FE–BE–AI 분리 구조에서 **AI 서버** 레포지토리입니다.

---

## 프로젝트 구성

| 디렉터리 | 설명 |
|----------|------|
| **ai_server/** | FastAPI 기반 AI 서버 (RAG 질문 생성, 요약 API). 상세는 [ai_server/README.md](ai_server/README.md) 참고 |
| **.github/** | CI 테스트, Docker 배포 워크플로, Nginx 설정 예시 |
| **docs/** | 기획·요구사항 문서 |
| **DB_SCHEMA.md, ERD.md** | 데이터베이스 스키마·ERD |

---

## AI 서버 요약

- **역할:** 가족/멤버별 과거 Q&A를 벡터 검색(RAG)해 개인화된 후속 질문 생성, 주간/월간 요약 생성
- **기술:** FastAPI, LangChain, OpenAI (Embedding + GPT-4o-mini), ChromaDB
- **아키텍처:** Clean Architecture (Domain / Application / Infrastructure / Presentation)
- **주요 API:** `POST /api/v1/questions/generate/personal`, `.../family`, `.../family-recent`, `GET /api/v1/summary`

로컬 실행·환경 변수·API 스펙은 **ai_server/README.md**를 참고하세요.

---

## 로컬 실행 (AI 서버만)

```bash
cd ai_server
cp .env.example .env   # OPENAI_API_KEY 등 설정
poetry install
poetry run python run_dev.py
```

Docker: `cd ai_server && docker-compose up -d`

---

## 라이선스

(필요 시 추가)
