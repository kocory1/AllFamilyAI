# 온식구 AI 서버 🏠🤖

가족 유대감을 위한 AI 질문 생성 서버입니다. OpenAI API를 활용해 템플릿 기반 question_instance 생성, 답변 분석, 멤버 할당을 제공합니다.

## 🚀 주요 기능

### 기능
- **질문 인스턴스 생성**: BE가 전달한 템플릿 파라미터로 인스턴스를 생성(메타 포함, DB 미사용)
- **답변 분석**: 질문 맥락(카테고리/태그/톤)을 반영해 구조화된 분석 JSON 반환
- **멤버 할당**: 최근 30회 할당 횟수 기반 가중치로 비복원 랜덤 선택


## 📁 프로젝트 구조 (도메인 기준)

```
온식구_ai/
├── ai_server/
│   ├── app/
│   │   ├── adapters/                 # 외부 의존 어댑터
│   │   │   └── openai_client.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── question/                 # 질문 도메인
│   │   │   ├── models.py
│   │   │   ├── base.py               # QuestionGenerator 인터페이스
│   │   │   ├── openai_question_generator.py
│   │   │   └── service/
│   │   │       ├── question_service.py
│   │   │       └── assignment_service.py
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

🧩 설계 포인트
- 전략 패턴 + DI: `QuestionService(QuestionGenerator)`, `AnswerService(AnswerAnalyzer)`로 구현 교체 용이
- OpenAI 어댑터: `app/adapters/openai_client.py`에서 OpenAI 호출을 단일화
- DB/MCP 제거: 모든 생성/분석은 BE 전달 파라미터 기반으로 동작

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

### 질문 인스턴스 생성

```
POST /api/v1/questions/instance/api       # OpenAI 구현
POST /api/v1/questions/instance/langchain  # (501 Not Implemented)
```

요청 예시(요약):
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
  "answer_analysis": {"summary": "최근 긍정적"}
}
```

응답 예시(요약):
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
  "generation_metadata": {"length": 23},
  "generation_confidence": 0.9,
  "generated_at": "2025-09-07T12:34:56"
}
```

### 답변 분석
```
POST /api/v1/analysis/answer/api        # OpenAI 구현
POST /api/v1/analysis/answer/langchain   # (501 Not Implemented)
```

요청 필드(요약): `answer_text`, `language`(기본 ko), `question_content`, `question_category`, `question_tags`, `question_tone`, `subject_member_id`(옵션), `family_id`

응답(요약): `summary`, `categories`, `scores(sentiment, emotion, relevance, toxicity, keywords, length)`

### 멤버 할당
```
POST /api/v1/questions/assign
```

요청 예시:
```json
{
  "family_id": 0,
  "members": [
    {"member_id": 1, "assigned_count_30": 4},
    {"member_id": 2, "assigned_count_30": 10},
    {"member_id": 3, "assigned_count_30": 6}
  ],
  "pick_count": 1,
  "options": {"epsilon": 1e-9}
}
```

응답 예시:
```json
{ "member_ids": [3], "version": "assign-v1" }
```

설명:
- 가중치: (w_i = (1/N) * (1 - c_i / S)), S는 최근 30회 합계
- 비복원 샘플링, `epsilon`으로 하한 보정(선택)
- seed는 제거됨(재현성 필요 시 BE에서 별도 관리)

## 🎯 사용 예시

### Python 클라이언트 예시



### cURL 예시


#### 템플릿 기반 question_instance 생성 (OpenAI 구현)
```bash
curl -X POST "http://localhost:8001/api/v1/questions/instance/api" \
  -H "Content-Type: application/json" \
  -d '{
    "template": {"id": 10, "owner_family_id": 3, "content": "{{subject}}에게 오늘 가장 고마웠던 일을 물어보는 질문", "language": "ko"},
    "mood": "따뜻한"
  }'
```

#### 멤버 할당
```bash
curl -X POST "http://localhost:8001/api/v1/questions/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "family_id": 0,
    "members": [
      {"member_id": 1, "assigned_count_30": 4},
      {"member_id": 2, "assigned_count_30": 10}
    ],
    "pick_count": 1,
    "options": {"epsilon": 1e-9}
  }'
```

#### 답변 분석
```bash
curl -X POST "http://localhost:8001/api/v1/analysis/answer/api" \
  -H "Content-Type: application/json" \
  -d '{
    "answer_text": "퇴근하고 아내가 끓여준 라면이 최고!!",
    "language": "ko",
    "question_content": "가장 좋아하는 음식이 무엇인가요?",
    "question_category": "음식",
    "question_tags": ["일상", "취향"],
    "question_tone": "편안",
    "subject_member_id": null,
    "family_id": 0
  }'
```

## 🔧 개발 환경

- **Python**: 3.12
- **FastAPI**: 0.115.6
- **OpenAI**: 1.57.0
- **Pydantic**: 2.10.4

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.


**온식구 AI 서버**로 가족의 따뜻한 대화를 만들어보세요! 🏠💕

## 📦 OpenAPI 정적 내보내기

```bash
cd ai_server
curl -sS http://127.0.0.1:8001/openapi.json -o openapi.json
```

- Swagger Editor에서 열기: `https://editor.swagger.io` → File → Import file → `ai_server/openapi.json`
- ReDoc 단일 HTML(옵션): `npx redoc-cli bundle openapi.json -o api-docs.html`
