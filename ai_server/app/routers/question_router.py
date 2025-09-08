from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from app.question.models import (
    QuestionInstanceCreateRequest,
    QuestionInstanceResponse
)
from app.question.openai_question_generator import OpenAIQuestionGenerator
from app.question.service.question_service import QuestionService

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["기본 질문"])

# 구현체 인스턴스
service_api = QuestionService(OpenAIQuestionGenerator())

@router.post(
    "/instance/api",
    response_model=QuestionInstanceResponse,
    summary="템플릿 기반 question_instance 생성",
    description="템플릿과 선택적 컨텍스트를 바탕으로 question_instance 정보를 생성하여 반환합니다."
)
async def create_question_instance(request: QuestionInstanceCreateRequest) -> QuestionInstanceResponse:
    try:
        instance = await service_api.generate_from_template(request)
        return instance
    except Exception as e:
        logger.error(f"question_instance 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"question_instance 생성에 실패했습니다: {str(e)}"
        )

@router.post(
    "/instance/langchain",
    response_model=QuestionInstanceResponse,
    summary="(준비중) LangChain 기반 question_instance 생성",
    description="LangChain 구현은 준비 중입니다."
)
async def create_question_instance_langchain(request: QuestionInstanceCreateRequest) -> QuestionInstanceResponse:
    raise HTTPException(status_code=501, detail="LangChain 구현은 준비 중입니다.")