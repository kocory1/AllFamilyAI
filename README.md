# 온식구 AI 서버 🏠

가족 유대감을 위한 AI 질문 생성 서버입니다. OpenAI API를 활용하여 가족 구성원들이 함께 대화할 수 있는 따뜻한 질문을 생성합니다.

## 🚀 주요 기능

- **AI 질문 생성**: OpenAI GPT를 활용한 가족 맞춤형 질문 생성
- **카테고리별 질문**: 가족, 추억, 일상, 꿈, 관계, 감정, 취미, 미래 등 다양한 카테고리
- **맞춤형 질문**: 가족 구성원 정보와 원하는 분위기를 반영한 개인화된 질문
- **일일 질문**: 요일별 분위기를 고려한 오늘의 질문 생성
- **랜덤 질문**: 랜덤 카테고리로 다양한 질문 생성

## 📁 프로젝트 구조

```
온식구_ai/
├── ai_server/                 # AI 서버 (FastAPI)
│   ├── app/
│   │   ├── core/             # 설정 및 핵심 기능
│   │   │   └── config.py     # 애플리케이션 설정
│   │   ├── models/           # Pydantic 모델
│   │   │   └── question.py   # 질문 관련 모델
│   │   ├── routers/          # API 라우터
│   │   │   └── question_router.py  # 질문 관련 API
│   │   ├── services/         # 비즈니스 로직
│   │   │   └── openai_service.py   # OpenAI 서비스
│   │   └── main.py           # FastAPI 애플리케이션
│   ├── requirements.txt      # Python 의존성
│   ├── env.example           # 환경 변수 예시
│   └── run.py               # 서버 실행 스크립트
└── README.md                # 프로젝트 설명서
```

## 🛠️ 설치 및 실행

### 1. 환경 설정

```bash
cd ai_server
cp env.example .env
```

`.env` 파일을 편집하여 OpenAI API 키를 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=INFO
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

### 질문 생성 API

#### 1. AI 질문 생성
```
POST /api/v1/questions/generate
```

**요청 예시:**
```json
{
  "target_member": "민수",
  "category": "가족",
  "family_context": "부모님, 자녀 2명",
  "mood": "따뜻한"
}
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

## 🎯 사용 예시

### Python 클라이언트 예시

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

# 사용 예시
question = await generate_family_question()
print(f"생성된 질문: {question['content']}")
```

### cURL 예시

```bash
# AI 질문 생성
curl -X POST "http://localhost:8001/api/v1/questions/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "target_member": "민수",
    "category": "가족",
    "family_context": "부모님, 자녀 2명",
    "mood": "따뜻한"
  }'

# 랜덤 질문 생성
curl "http://localhost:8001/api/v1/questions/random?target_member=민수&family_context=부모님&mood=재미있는"

# 오늘의 질문 생성
curl "http://localhost:8001/api/v1/questions/daily?target_member=민수&family_context=부모님"
```

## 🔧 개발 환경

- **Python**: 3.8+
- **FastAPI**: 0.104.1
- **OpenAI**: 1.3.7
- **Pydantic**: 2.5.0

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
