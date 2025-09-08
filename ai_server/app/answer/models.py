from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnswerAnalysisRequest(BaseModel):
    answer_text: str = Field(description="분석 대상 답변 텍스트")
    language: str = Field(default="ko", description="분석 기준 언어 코드(기본: ko)")
    question_content: str = Field(description="해당 질문 원문")
    question_category: str = Field(description="질문 카테고리")
    question_tags: List[str] = Field(default_factory=list, description="질문/템플릿 태그")
    question_tone: Optional[str] = Field(default=None, description="질문 톤/스타일")
    subject_member_id: Optional[int] = Field(default=None, description="주제 인물 ID (없으면 NULL)")
    family_id: Optional[int] = Field(default=None, description="가족 그룹 식별자")


class AnswerAnalysisRaw(BaseModel):
    text: str = Field(description="LLM 원문 응답 문자열")
    parseOk: bool = Field(description="JSON 파싱 성공 여부")


class AnswerAnalysisResponse(BaseModel):
    analysis_prompt: str = Field(description="실제 사용된 분석 프롬프트")
    analysis_parameters: Dict[str, Any] = Field(description="LLM 호출 파라미터")
    analysis_raw: AnswerAnalysisRaw = Field(description="LLM 원문 응답 및 파싱 여부")
    analysis_version: str = Field(description="분석 버전(모델/규칙 태그)")
    summary: str = Field(description="요약")
    categories: List[str] = Field(description="분석 결과 주제/카테고리")
    scores: Dict[str, Any] = Field(description="분석 점수 집합")
    created_at: datetime = Field(description="분석 시각")



