# 온식구 AI 서버 🏠🤖

가족 유대감을 위한 AI 질문 생성 서버입니다. OpenAI API를 활용해 간단한 질문 생성과 템플릿 기반 question_instance 생성을 제공합니다. 

## 🚀 주요 기능

### 기본 기능(간소화)
- **AI 질문 생성**: OpenAI GPT를 활용한 질문 생성


## 📁 프로젝트 구조 (도메인 기준)

```
온식구_ai/
├── ai_server/
│   ├── app/
│   │   ├── adapters/                 # 외부 의존 어댑터
│   │   │   └── openai_client.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── question/                 # 질문(생성) 도메인
│   │   │   ├── models.py
│   │   │   ├── base.py               # QuestionGenerator 인터페이스
│   │   │   ├── openai_question_generator.py
│   │   │   └── service/
│   │   │       └── question_service.py
│   │   ├── answer/                   # 답변(분석) 도메인
│   │   │   ├── models.py
│   │   │   ├── base.py               # AnswerAnalyzer 인터페이스
│   │   │   ├── openai_answer_analyzer.py
│   │   │   └── service/
│   │   │       └── answer_service.py
│   │   ├── routers/
│   │   │   ├── question_router.py
│   │   │   └── analysis_router.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── env.example
│   └── run.py
└── README.md
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

# 로깅 설정
LOG_LEVEL=INFO
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

### 2. Python 버전 및 의존성 설치

```bash
# 권장 Python 버전: 3.12
# pyenv 예시
pyenv install 3.12.6 -s
pyenv local 3.12.6

# 가상환경 권장
python -m venv venv
source venv/bin/activate

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

### 질문 인스턴스 생성 API

#### 2. 템플릿 기반 question_instance 생성 (신규)
```
POST /api/v1/questions/instance
```

요청 예시:
```json
{
  "template": {
    "id": 10,
    "owner_family_id": 3,
    "content": "{{subject}}에게 오늘 가장 고마웠던 일을 물어보는 질문",
    "category": "가족",
    "tags": ["감사", "일상"],
    "subject_required": false,
    "reuse_scope": "per_family",
    "cooldown_days": 7,
    "language": "ko",
    "tone": "따뜻한",
    "is_active": true
  },
  "planned_date": "2025-09-15",
  "subject_member_id": null,
  "mood": "따뜻한",
  "extra_context": {"locale": "KR"},
  "answer_analysis": {"summary": "최근 긍정적", "key_phrases": ["여행", "학교"], "sentiment": "positive"}
}
```

응답 예시:
```json
{
  "template_id": 10,
  "family_id": 3,
  "subject_member_id": null,
  "content": "오늘 가장 고마웠던 순간은 무엇이었나요?",
  "planned_date": "2025-09-15",
  "status": "draft",
  "generated_by": "ai",
  "generation_model": "gpt-4.1-nano",
  "generation_parameters": {"max_tokens": 100, "temperature": 0.8},
  "generation_prompt": "...",
  "generation_metadata": {"length": 23, "rules": {"length_ok": true, "ends_question": true}},
  "generation_confidence": 0.9,
  "generated_at": "2025-09-07T12:34:56"
}
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



### cURL 예시


#### 템플릿 기반 question_instance 생성 (cURL)
```bash
curl -X POST "http://localhost:8001/api/v1/questions/instance" \
  -H "Content-Type: application/json" \
  -d '{
    "template": {"id": 10, "owner_family_id": 3, "content": "{{subject}}에게 오늘 가장 고마웠던 일을 물어보는 질문", "language": "ko"},
    "mood": "따뜻한"
  }'
```

## 🔧 개발 환경

- **Python**: 3.12 권장 (3.13은 일부 DB 드라이버 빌드 이슈 존재)
- **FastAPI**: 0.115.6
- **OpenAI**: 1.57.0
- **PostgreSQL**: 13+
- **SQLAlchemy**: 2.0.25
- **Pydantic**: 2.10.4

## 🧩 비고
- MCP/DB 관련 문서 블록은 현재 버전에서 비활성화되었습니다. 향후 재도입 시 별도 섹션으로 복원합니다.

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
