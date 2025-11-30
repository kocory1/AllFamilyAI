from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnswerAnalysisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    answer_text: str = Field(alias="answerText", description="분석 대상 답변 텍스트")
    language: str = Field(default="ko", description="분석 기준 언어 코드(기본: ko)")
    question_content: str = Field(alias="questionContent", description="해당 질문 원문")
    question_category: str = Field(alias="questionCategory", description="질문 카테고리")
    question_tags: List[str] = Field(default_factory=list, alias="questionTags", description="질문/템플릿 태그")
    question_tone: Optional[str] = Field(default=None, alias="questionTone", description="질문 톤/스타일")
    
    # RAG용 추가 필드
    user_id: str = Field(alias="userId", description="사용자 ID (벡터 DB 저장용)")


class AnswerAnalysisRaw(BaseModel):
    text: str = Field(description="LLM 원문 응답 문자열")
    parseOk: bool = Field(description="JSON 파싱 성공 여부")


class AnswerAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    analysis_prompt: str = Field(alias="analysisPrompt", description="실제 사용된 분석 프롬프트")
    analysis_parameters: Dict[str, Any] = Field(alias="analysisParameters", description="LLM 호출 파라미터")
    analysis_raw: AnswerAnalysisRaw = Field(alias="analysisRaw", description="LLM 원문 응답 및 파싱 여부")
    analysis_version: str = Field(alias="analysisVersion", description="분석 버전(모델/규칙 태그)")
    summary: str = Field(description="요약")
    categories: List[str] = Field(description="분석 결과 주제/카테고리")
    keywords: List[str] = Field(description="키워드 목록")
    scores: Dict[str, Any] = Field(description="분석 점수 집합")
    created_at: datetime = Field(alias="createdAt", description="분석 시각")



