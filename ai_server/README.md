# 온식구 AI 서버

가족 대화 기록 기반 RAG 질문 생성 서버

## 개요

가족 구성원의 과거 Q&A 데이터를 벡터 DB에 저장하고, 유사 문맥을 검색(RAG)하여 개인화된 후속 질문을 생성하는 AI 서버.

## 기술 스택

- **Framework**: FastAPI (async)
- **LLM**: OpenAI GPT-4o-mini (LangChain)
- **Vector DB**: ChromaDB (PersistentClient)
- **Embedding**: text-embedding-3-small
- **Architecture**: Clean Architecture (DDD + Ports & Adapters)

## 아키텍처

```
app/
├── domain/              # 핵심 비즈니스 로직 (프레임워크 독립)
│   ├── entities/        # QADocument (불변 객체)
│   ├── ports/           # VectorStorePort, QuestionGeneratorPort (인터페이스)
│   └── value_objects/   # QuestionLevel
├── application/         # Use Cases
│   ├── dto/             # 입출력 DTO
│   └── use_cases/       # PersonalRAG, FamilyRAG, FamilyRecent
├── infrastructure/      # 외부 서비스 구현체
│   ├── llm/             # LangChain 기반 Generator
│   └── vector/          # ChromaDB VectorStore
└── presentation/        # API 계층
    ├── routers/         # FastAPI Router
    └── schemas/         # Pydantic Request/Response
```

## RAG 파이프라인

### 1. 저장 (Indexing)
```
Input Q&A → OpenAI Embedding → ChromaDB 저장
                              (metadata: family_id, member_id, role_label, answered_at)
```

### 2. 검색 + 생성 (Retrieval + Generation)
```
Input Q&A → Embedding → ChromaDB Query (member/family 필터)
                              ↓
                        Top-K 유사 문서
                              ↓
                        LangChain Prompt (system + user + RAG context)
                              ↓
                        GPT-4o-mini → 후속 질문 생성
                              ↓
                        유사도 검사 (threshold: 0.9)
                              ↓
                        중복 시 재생성 (최대 3회)
```

## API 엔드포인트

| Method | Endpoint | 설명 | 우선순위 |
|--------|----------|------|----------|
| POST | `/api/v1/questions/generate/personal` | 개인 RAG 질문 생성 | P2 |
| POST | `/api/v1/questions/generate/family` | 가족 RAG 질문 생성 | P3-base |
| POST | `/api/v1/questions/generate/family-recent` | 가족 최근 기반 질문 생성 | P3-recent |

### 요청 예시 (Personal)
```json
{
  "familyId": "uuid",
  "memberId": "uuid",
  "roleLabel": "첫째 딸",
  "baseQuestion": "오늘 뭐 했어?",
  "baseAnswer": "친구 만났어",
  "answeredAt": "2026-01-20T10:00:00"
}
```

### 응답 예시
```json
{
  "memberId": "uuid",
  "content": "친구랑 무슨 이야기를 나눴나요?",
  "level": 2,
  "priority": 2,
  "metadata": {
    "rag_count": 5,
    "regeneration_count": 0,
    "similarity_warning": false
  }
}
```

## 중복 질문 방지

- 생성된 질문을 기존 질문들과 벡터 유사도 비교
- Threshold: 0.9 이상 시 재생성
- 최대 재생성 횟수: 3회
- 초과 시 `similarity_warning: true` 반환

## 프롬프트 구조

```yaml
# prompts/personal_generate.yaml
system: |
  당신은 가족 유대감을 높이는 질문 생성 전문가입니다.
  ...
user: |
  **대상:** {role_label}
  {base_qa}
  **유사한 과거 답변 기록 (참고용):**
  {rag_context}
  ...
```

## 환경 설정

```bash
# .env
OPENAI_API_KEY=sk-...
CHROMA_PERSIST_DIRECTORY=/data/chroma  # Docker 볼륨 경로
MAX_REGENERATION=3
SIMILARITY_THRESHOLD=0.9
```

## 실행

### 로컬 개발
```bash
cd ai_server
poetry install
poetry run python run_dev.py
```

### Docker
```bash
docker-compose up -d
```

## 테스트

```bash
poetry run pytest tests/refactoring/ -v
```

## 디렉토리별 책임

| 디렉토리 | 책임 | 의존성 |
|----------|------|--------|
| domain | 비즈니스 규칙 | 없음 (순수 Python) |
| application | 유스케이스 오케스트레이션 | domain |
| infrastructure | 외부 서비스 구현 | domain, 외부 라이브러리 |
| presentation | HTTP 처리 | application |
