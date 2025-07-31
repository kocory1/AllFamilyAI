from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class QuestionCategory(str, Enum):
    FAMILY = "가족"
    MEMORY = "추억"
    DAILY = "일상"
    DREAM = "꿈"
    RELATIONSHIP = "관계"
    EMOTION = "감정"
    HOBBY = "취미"
    FUTURE = "미래"

class QuestionRequest(BaseModel):
    category: Optional[QuestionCategory] = Field(
        default=None, 
        description="질문 카테고리 (선택사항)"
    )
    target_member: str = Field(
        description="질문 대상 가족 구성원의 이름/닉네임 (예: 민수, 영희, 아빠, 엄마)"
    )
    family_context: Optional[str] = Field(
        default=None,
        description="전체 가족 구성원 정보 (예: 부모님, 자녀 2명)"
    )
    mood: Optional[str] = Field(
        default=None,
        description="원하는 분위기 (예: 따뜻한, 재미있는, 진지한)"
    )

class QuestionResponse(BaseModel):
    id: str = Field(description="질문 고유 ID")
    content: str = Field(description="질문 내용")
    category: QuestionCategory = Field(description="질문 카테고리")
    target_member: str = Field(description="질문 대상 가족 구성원")
    created_at: datetime = Field(description="생성 시간")
    family_context: Optional[str] = Field(default=None, description="전체 가족 구성원 정보")
    mood: Optional[str] = Field(default=None, description="분위기")

class QuestionListResponse(BaseModel):
    questions: List[QuestionResponse] = Field(description="질문 목록")
    total_count: int = Field(description="총 질문 수")

class ErrorResponse(BaseModel):
    error: str = Field(description="에러 메시지")
    detail: Optional[str] = Field(default=None, description="상세 에러 정보") 