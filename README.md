# 온식구 AI 서버 (MCP 강화) 🏠🤖

가족 유대감을 위한 AI 질문 생성 서버입니다. OpenAI API와 **Model Context Protocol (MCP)**를 활용하여 과거 대화 기록을 분석하고 가족 구성원에게 맞춤화된 질문을 생성합니다.

## 🚀 주요 기능

### 기본 기능
- **AI 질문 생성**: OpenAI GPT를 활용한 가족 맞춤형 질문 생성
- **카테고리별 질문**: 가족, 추억, 일상, 꿈, 관계, 감정, 취미, 미래 등 다양한 카테고리
- **맞춤형 질문**: 가족 구성원 정보와 원하는 분위기를 반영한 개인화된 질문
- **일일 질문**: 요일별 분위기를 고려한 오늘의 질문 생성
- **랜덤 질문**: 랜덤 카테고리로 다양한 질문 생성

### MCP 강화 기능 ✨ 
- **개인화 질문 생성**: 과거 답변 패턴을 분석하여 각 가족 구성원에게 최적화된 질문 생성
- **후속 질문 생성**: 이전 답변을 바탕으로 자연스러운 대화 이어가기
- **테마별 질문 세트**: 특정 주제에 대한 다양한 관점의 질문들을 한번에 생성
- **가족 패턴 분석**: 각 구성원의 답변 스타일, 선호 주제, 감정 패턴 분석
- **대화 효과성 분석**: 대화의 질과 참여도를 분석하여 개선점 제안
- **지능형 중복 방지**: 과거 질문과 중복되지 않도록 스마트한 질문 생성

## 📁 프로젝트 구조

```
온식구_ai/
├── ai_server/                        # AI 서버 (FastAPI)
│   ├── app/
│   │   ├── core/                     # 설정 및 핵심 기능
│   │   │   └── config.py             # 애플리케이션 설정
│   │   ├── database/                 # 데이터베이스 관련 🆕
│   │   │   ├── database.py           # DB 연결 및 설정
│   │   │   └── models.py             # SQLAlchemy 모델
│   │   ├── models/                   # Pydantic 모델
│   │   │   ├── question.py           # 기본 질문 모델
│   │   │   └── enhanced_models.py    # MCP 강화 모델 🆕
│   │   ├── routers/                  # API 라우터
│   │   │   ├── question_router.py    # 기본 질문 API
│   │   │   ├── mcp_router.py         # MCP 기능 API 🆕
│   │   │   ├── answers_router.py     # 답변 관리 API 🆕
│   │   │   └── family_router.py      # 가족 관리 API 🆕
│   │   ├── services/                 # 비즈니스 로직
│   │   │   ├── openai_service.py     # 기본 OpenAI 서비스
│   │   │   ├── enhanced_openai_service.py  # MCP 강화 서비스 🆕
│   │   │   ├── mcp_service.py        # MCP 핵심 서비스 🆕
│   │   │   └── database_service.py   # DB CRUD 서비스 🆕
│   │   └── main.py                   # FastAPI 애플리케이션
│   ├── requirements.txt              # Python 의존성
│   ├── env.example                   # 환경 변수 예시
│   └── run.py                       # 서버 실행 스크립트
└── README.md                        # 프로젝트 설명서
```

🆕 **새로 추가된 기능들**

## 🛠️ 설치 및 실행

### 1. 환경 설정

```bash
cd ai_server
cp env.example .env
```

`.env` 파일을 편집하여 필요한 설정을 입력하세요:

```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here

# 서버 설정
HOST=0.0.0.0
PORT=8001

# 데이터베이스 설정 (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/family_questions
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/family_questions

# 로깅 설정
LOG_LEVEL=INFO

# MCP 설정
MCP_CONTEXT_WINDOW=10
MCP_SIMILARITY_THRESHOLD=0.7
MCP_ANALYSIS_DEPTH=deep
```

### 1-1. 데이터베이스 설정 🆕

PostgreSQL 데이터베이스를 설치하고 설정하세요:

```bash
# PostgreSQL 설치 (macOS)
brew install postgresql
brew services start postgresql

# 데이터베이스 생성
createdb family_questions

# 또는 psql로 직접 생성
psql postgres
CREATE DATABASE family_questions;
\q
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
python run.py
```

또는

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🔌 API 엔드포인트

### 기본 질문 생성 API

#### 1. AI 질문 생성
```
POST /api/v1/questions/generate
```

#### 2. 랜덤 질문 생성
```
GET /api/v1/questions/random?target_member=민수&family_context=부모님&mood=재미있는
```

#### 3. 오늘의 질문 생성
```
GET /api/v1/questions/daily?target_member=민수&family_context=부모님
```

#### 4. 질문 카테고리 목록
```
GET /api/v1/questions/categories
```

### MCP 강화 질문 API 🆕

#### 1. MCP 기반 개인화 질문 생성
```
POST /api/v1/mcp/questions/generate
```

**요청 예시:**
```json
{
  "target_member": "민수",
  "family_id": "kim_family",
  "category": "가족",
  "family_context": "부모님, 자녀 2명",
  "mood": "따뜻한",
  "use_mcp": true
}
```

#### 2. 후속 질문 생성
```
POST /api/v1/mcp/questions/follow-up
```

**요청 예시:**
```json
{
  "target_member": "민수",
  "previous_answer": "어릴 때 할머니와 함께 김치를 담근 추억이 가장 소중해요.",
  "original_question": "어릴 때 가장 소중한 추억이 무엇인가요?",
  "family_id": "kim_family"
}
```

#### 3. 테마별 질문 생성
```
POST /api/v1/mcp/questions/themed
```

**요청 예시:**
```json
{
  "target_member": "민수",
  "theme": "어린시절 추억",
  "count": 5,
  "family_id": "kim_family"
}
```

#### 4. 가족 패턴 분석
```
GET /api/v1/mcp/analysis/family/{target_member}?family_id=kim_family
```

#### 5. 대화 효과성 분석
```
POST /api/v1/mcp/analysis/conversation
```

### 답변 관리 API 🆕

#### 1. 답변 저장
```
POST /api/v1/answers/
```

#### 2. 질문별 답변 조회
```
GET /api/v1/answers/question/{question_uuid}
```

#### 3. 구성원별 답변 조회
```
GET /api/v1/answers/member/{answerer_name}
```

### 가족 관리 API 🆕

#### 1. 가족 구성원 등록
```
POST /api/v1/family/members
```

#### 2. 가족 구성원 목록 조회
```
GET /api/v1/family/members
```

#### 3. 질문/답변 통계
```
GET /api/v1/family/statistics/questions
GET /api/v1/family/statistics/answers
```

## 🎯 사용 예시

### Python 클라이언트 예시

#### 기본 질문 생성
```python
import httpx

async def generate_family_question():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/questions/generate",
            json={
                "target_member": "민수",
                "category": "가족",
                "family_context": "부모님, 자녀 2명",
                "mood": "따뜻한"
            }
        )
        return response.json()
```

#### MCP 기반 개인화 질문 생성 🆕
```python
async def generate_mcp_question():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/mcp/questions/generate",
            json={
                "target_member": "민수",
                "family_id": "kim_family",
                "category": "추억",
                "use_mcp": True
            }
        )
        return response.json()
```

#### 답변 저장 및 후속 질문 생성 🆕
```python
async def save_answer_and_generate_followup():
    async with httpx.AsyncClient() as client:
        # 1. 답변 저장
        await client.post(
            "http://localhost:8001/api/v1/answers/",
            json={
                "question_uuid": "question-uuid-here",
                "answer_text": "어릴 때 할머니와 함께 김치를 담근 추억이 가장 소중해요.",
                "answerer_name": "민수"
            }
        )
        
        # 2. 후속 질문 생성
        followup = await client.post(
            "http://localhost:8001/api/v1/mcp/questions/follow-up",
            json={
                "target_member": "민수",
                "previous_answer": "어릴 때 할머니와 함께 김치를 담근 추억이 가장 소중해요.",
                "original_question": "어릴 때 가장 소중한 추억이 무엇인가요?",
                "family_id": "kim_family"
            }
        )
        return followup.json()
```

### cURL 예시

#### 기본 질문 생성
```bash
curl -X POST "http://localhost:8001/api/v1/questions/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "target_member": "민수",
    "category": "가족",
    "family_context": "부모님, 자녀 2명",
    "mood": "따뜻한"
  }'
```

#### MCP 기반 개인화 질문 생성 🆕
```bash
curl -X POST "http://localhost:8001/api/v1/mcp/questions/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "target_member": "민수",
    "family_id": "kim_family",
    "category": "추억",
    "use_mcp": true
  }'
```

#### 가족 패턴 분석 🆕
```bash
curl "http://localhost:8001/api/v1/mcp/analysis/family/민수?family_id=kim_family"
```

## 🔧 개발 환경

- **Python**: 3.8+
- **FastAPI**: 0.115.6
- **OpenAI**: 1.57.0
- **PostgreSQL**: 13+
- **SQLAlchemy**: 2.0.25
- **Pydantic**: 2.10.4

## 🧠 MCP (Model Context Protocol) 소개

**Model Context Protocol**은 이 프로젝트에서 구현한 핵심 기능으로, 과거 대화 기록을 분석하여 더 개인화된 AI 응답을 생성하는 시스템입니다.

### 주요 구성 요소:
1. **컨텍스트 수집**: 과거 질문-답변 데이터 수집 및 정리
2. **패턴 분석**: 개인별 답변 스타일, 선호 주제, 감정 패턴 분석
3. **지능형 생성**: 분석된 패턴을 바탕으로 맞춤형 질문 생성
4. **피드백 루프**: 새로운 답변을 통한 지속적인 학습 및 개선

### 데이터 보호:
- 모든 개인 데이터는 로컬 데이터베이스에 안전하게 저장
- 외부로 전송되는 데이터는 익명화 처리
- 사용자가 원할 때 언제든 데이터 삭제 가능

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**온식구 AI 서버**로 가족의 따뜻한 대화를 만들어보세요! 🏠💕
