from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from app.question.models import (QuestionGenerateRequest, QuestionInstanceResponse, MemberAssignRequest, MemberAssignResponse)
from app.question.openai_question_generator import OpenAIQuestionGenerator
from app.question.service.question_service import QuestionService
from app.question.service.assignment_service import AssignmentService

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["기본 질문"])

service_api = QuestionService(OpenAIQuestionGenerator())

@router.post(
    "/api",
    response_model=QuestionInstanceResponse,
    summary="질문 생성",
    description="content를 기반으로 질문을 생성합니다. 선택적으로 language/tone/category/tags/mood/subject_required/answer_analysis를 반영합니다."
)
async def generate_question(request: QuestionGenerateRequest) -> QuestionInstanceResponse:
    try:
        content_preview = request.content[:50] if len(request.content) > 50 else request.content
        logger.info(f"[질문생성 요청] content: '{content_preview}...', category: {request.category}, tone: {request.tone}")
        result = await service_api.generate(request)
        logger.info(f"[질문생성 성공] 생성된 질문: '{result.content}'")
        return result
    except Exception as e:
        logger.error(f"질문 생성 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 생성에 실패했습니다: {str(e)}")

@router.post(
    "/instance/langchain",
    response_model=QuestionInstanceResponse,
    summary="(준비중) LangChain 기반 질문 생성",
    description="LangChain 구현은 준비 중입니다."
)
async def create_question_instance_langchain(request: QuestionGenerateRequest) -> QuestionInstanceResponse:
    raise HTTPException(status_code=501, detail="LangChain 구현은 준비 중입니다.")


@router.post(
    "/assign",
    response_model=MemberAssignResponse,
    summary="멤버 할당",
    description="최근 30회 기준으로 덜 받은 멤버에 확률을 부여해 pick_count명 선정"
)
async def assign_members(request: MemberAssignRequest) -> MemberAssignResponse:
    try:
        service = AssignmentService()
        return await service.assign_members(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"멤버 할당 실패: {str(e)}")