from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
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
    category: Optional[QuestionCategory] = Field(default=None, description="질문 카테고리 (선택사항)")
    target_member: str = Field(description="질문 대상 가족 구성원의 이름/닉네임 (예: 민수, 영희, 아빠, 엄마)")
    family_context: Optional[str] = Field(default=None, description="전체 가족 구성원 정보 (예: 부모님, 자녀 2명)")
    mood: Optional[str] = Field(default=None, description="원하는 분위기 (예: 따뜻한, 재미있는, 진지한)")

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

# === 템플릿 기반 question_instance 생성 스키마 ===
class QuestionTemplateInput(BaseModel):
    id: int = Field(description="question_template ID")
    owner_family_id: int = Field(description="템플릿 소유 가족 ID (인스턴스의 family_id로 사용)")
    content: str = Field(description="템플릿 본문(치환 전)")
    category: Optional[str] = Field(default=None, description="카테고리")
    tags: Optional[List[str]] = Field(default=None, description="태그 목록")
    subject_required: Optional[bool] = Field(default=False, description="주제 인물 필요 여부")
    reuse_scope: Optional[str] = Field(default=None, description="재사용 범위: global|per_family|per_subject")
    cooldown_days: Optional[int] = Field(default=None, description="재사용 쿨다운 일수")
    language: Optional[str] = Field(default="ko", description="언어 코드(ex. ko, en)")
    tone: Optional[str] = Field(default=None, description="톤/스타일")
    is_active: Optional[bool] = Field(default=True, description="활성 여부")

class QuestionInstanceCreateRequest(BaseModel):
    template: QuestionTemplateInput = Field(description="인스턴스 생성을 위한 템플릿 데이터")
    planned_date: Optional[date] = Field(default=None, description="계획 날짜 (옵션)")
    subject_member_id: Optional[int] = Field(default=None, description="주제 인물 ID (없으면 NULL)")
    extra_context: Optional[Dict[str, Any]] = Field(default=None, description="추가 컨텍스트(선택)")
    mood: Optional[str] = Field(default=None, description="원하는 분위기(선택)")
    # 이전 답변 분석(선택). 제공되면 프롬프트에 반영, 없으면 미사용
    answer_analysis: Optional[Dict[str, Any]] = Field(default=None, description="이전 답변 분석 힌트(요약/키워드/감정 등)")

class QuestionInstanceResponse(BaseModel):
    template_id: int = Field(description="사용된 템플릿 ID")
    family_id: int = Field(description="가족 ID (owner_family_id 복사)")
    subject_member_id: Optional[int] = Field(default=None, description="주제 인물 ID")
    content: str = Field(description="생성된 질문 내용")
    planned_date: Optional[date] = Field(default=None, description="계획 날짜")
    status: str = Field(default="draft", description="상태: draft|scheduled|sent 등")
    generated_by: str = Field(description="생성 주체: ai|manual")
    generation_model: str = Field(description="사용 모델명")
    generation_parameters: Dict[str, Any] = Field(description="모델 호출 파라미터")
    generation_prompt: str = Field(description="프롬프트 원문")
    generation_metadata: Dict[str, Any] = Field(description="생성 메타데이터")
    generation_confidence: float = Field(description="생성 신뢰도(0~1)")
    generated_at: datetime = Field(description="생성 시각")



