"""
Mock 데이터 상수 모음
conftest.py의 가독성을 위해 분리
"""

# ====================
# OpenAI API 응답 Mock 데이터
# ====================

# 답변 분석 응답 (실제 OpenAI API 응답 구조)
MOCK_OPENAI_ANSWER_ANALYSIS = {
    "id": "chatcmpl-test123",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": """```json
{
  "summary": "가족과 주말에 등산을 다녀온 경험에 대한 답변",
  "keywords": ["등산", "가족", "주말", "운동"],
  "sentiment": 0.8,
  "scores": {
    "openness": 0.7,
    "specificity": 0.8,
    "emotional_depth": 0.75
  }
}
```"""
            },
            "finish_reason": "stop"
        }
    ]
}

# 질문 생성 응답
MOCK_OPENAI_QUESTION_GENERATION = {
    "id": "chatcmpl-test456",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "오늘 저녁에는 뭐 드셨어요?"
            },
            "finish_reason": "stop"
        }
    ]
}

# Embedding 응답
MOCK_OPENAI_EMBEDDING_RESPONSE = {
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "embedding": [0.1] * 1536,  # 1536차원 벡터
            "index": 0
        }
    ],
    "model": "text-embedding-3-small",
    "usage": {
        "prompt_tokens": 8,
        "total_tokens": 8
    }
}

# ====================
# ChromaDB 검색 결과 Mock
# ====================

MOCK_VECTOR_SEARCH_RESULTS = {
    "ids": [["answer_1", "answer_2", "answer_3"]],
    "documents": [
        [
            "지난 주말에 가족과 함께 등산을 다녀왔어요. 날씨도 좋고 경치가 아름다웠어요.",
            "주말마다 아이들과 공원에서 자전거를 타요. 함께하는 시간이 소중해요.",
            "가족들과 저녁 식사 후 산책하는 것을 좋아해요. 대화도 많이 나누고요."
        ]
    ],
    "metadatas": [
        [
            {"user_id": "test_user_123", "question": "주말에 주로 뭐해요?", "timestamp": "2025-01-01T10:00:00"},
            {"user_id": "test_user_123", "question": "가족과 함께하는 시간은?", "timestamp": "2025-01-02T10:00:00"},
            {"user_id": "test_user_123", "question": "최근 좋았던 순간은?", "timestamp": "2025-01-03T10:00:00"}
        ]
    ],
    "distances": [[0.15, 0.22, 0.28]]
}

# ====================
# 포맷된 검색 결과 (VectorService.search_similar_answers 반환값)
# ====================

MOCK_FORMATTED_SEARCH_RESULTS = [
    {
        "answer": "지난 주말에 가족과 함께 등산을 다녀왔어요. 날씨도 좋고 경치가 아름다웠어요.",
        "question": "주말에 주로 뭐해요?",
        "similarity": 0.85,
        "timestamp": "2025-01-01T10:00:00"
    },
    {
        "answer": "주말마다 아이들과 공원에서 자전거를 타요. 함께하는 시간이 소중해요.",
        "question": "가족과 함께하는 시간은?",
        "similarity": 0.78,
        "timestamp": "2025-01-02T10:00:00"
    },
    {
        "answer": "가족들과 저녁 식사 후 산책하는 것을 좋아해요. 대화도 많이 나누고요.",
        "question": "최근 좋았던 순간은?",
        "similarity": 0.72,
        "timestamp": "2025-01-03T10:00:00"
    }
]

# ====================
# 테스트 요청 데이터
# ====================

SAMPLE_QUESTION_REQUEST = {
    "category": "일상",
    "tone": "편안한",
    "subjectMemberId": "test_user_123",
    "useRag": False
}

SAMPLE_ANSWER_REQUEST = {
    "userId": "test_user_123",
    "questionContent": "오늘 저녁에는 뭐 드셨어요?",
    "answerText": "가족들과 함께 삼겹살을 구워먹었어요. 오랜만에 모여서 즐거웠어요.",
    "questionCategory": "일상"
}

