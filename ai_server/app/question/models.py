from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class ErrorResponse(BaseModel):
    error: str = Field(description="에러 메시지")
    detail: Optional[str] = Field(default=None, description="상세 에러 정보")

# === 답변 분석 힌트(요청 내 구조화 스키마) ===
class EmotionScores(BaseModel):
    joy: Optional[float] = Field(default=None, description="0~1")
    sadness: Optional[float] = Field(default=None, description="0~1")
    anger: Optional[float] = Field(default=None, description="0~1")
    fear: Optional[float] = Field(default=None, description="0~1")
    neutral: Optional[float] = Field(default=None, description="0~1")


class AnalysisScores(BaseModel):
    sentiment: Optional[float] = Field(default=None, description="-1.0~1.0")
    emotion: Optional[EmotionScores] = Field(default=None, description="감정 스코어")
    relevance_to_question: Optional[float] = Field(default=None, description="0~1")
    relevance_to_category: Optional[float] = Field(default=None, description="0~1")
    toxicity: Optional[float] = Field(default=None, description="0~1")
    length: Optional[int] = Field(default=None, description="답변 길이")


class AnswerAnalysisHint(BaseModel):
    summary: Optional[str] = Field(default=None, description="요약")
    categories: Optional[List[str]] = Field(default=None, description="분류 라벨")
    scores: Optional[AnalysisScores] = Field(default=None, description="점수 집합")
    keywords: Optional[List[str]] = Field(default=None, description="키워드")


# === 질문 생성(최신) 요청 스키마 ===
class QuestionGenerateRequest(BaseModel):
    content: str = Field(description="질문 생성의 기반이 되는 베이스 문구")
    language: Optional[str] = Field(default="ko", description="언어 코드(기본 ko)")
    tone: Optional[str] = Field(default=None, description="톤/스타일")
    category: Optional[str] = Field(default=None, description="카테고리")
    tags: Optional[List[str]] = Field(default=None, description="태그 목록")
    subject_required: Optional[bool] = Field(default=False, description="주제 인물 필요 여부")
    mood: Optional[str] = Field(default=None, description="원하는 분위기(선택)")
    # 답변 분석 힌트(선택): summary/categories/scores/keywords 등 일부 또는 전부 포함 가능
    answer_analysis: Optional[AnswerAnalysisHint] = Field(default=None, description="답변 분석 힌트")

class QuestionInstanceResponse(BaseModel):
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

# === 멤버 할당 스키마 ===
class AssignMemberInput(BaseModel):
    member_id: int | str = Field(description="멤버 ID")
    assigned_count_30: int = Field(ge=0, description="최근 30회 내 할당 횟수(0 이상)")

class AssignOptions(BaseModel):
    epsilon: Optional[float] = Field(default=1e-9, description="가중치 하한값")

class MemberAssignRequest(BaseModel):
    family_id: int | str = Field(description="가족 ID")
    members: List[AssignMemberInput] = Field(description="후보 멤버 목록")
    pick_count: int = Field(ge=1, description="선정할 멤버 수")
    options: Optional[AssignOptions] = Field(default=None, description="선정 옵션")

class MemberAssignResponse(BaseModel):
    member_ids: List[int | str] = Field(description="선정된 멤버 ID 목록")
    version: str = Field(default="assign-v1", description="로직 버전")



