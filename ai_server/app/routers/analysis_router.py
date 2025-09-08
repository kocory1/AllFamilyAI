from fastapi import APIRouter, HTTPException
import logging

from app.answer.models import AnswerAnalysisRequest, AnswerAnalysisResponse
from app.answer.openai_answer_analyzer import OpenAIAnswerAnalyzer
from app.answer.service.answer_service import AnswerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["답변 분석"])

service_api = AnswerService(OpenAIAnswerAnalyzer())

@router.post(
    "/answer/api",
    response_model=AnswerAnalysisResponse,
    summary="답변 분석",
    description="질문/카테고리/태그/톤 맥락을 반영해 답변을 분석하고 JSON 스키마로 반환합니다."
)
async def analyze_answer(request: AnswerAnalysisRequest) -> AnswerAnalysisResponse:
    try:
        return await service_api.analyze(request)
    except Exception as e:
        logger.error(f"답변 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"답변 분석에 실패했습니다: {str(e)}")

@router.post(
    "/answer/langchain",
    response_model=AnswerAnalysisResponse,
    summary="(준비중) LangChain 기반 답변 분석",
    description="LangChain 구현은 준비 중입니다."
)
async def analyze_answer_langchain(request: AnswerAnalysisRequest) -> AnswerAnalysisResponse:
    raise HTTPException(status_code=501, detail="LangChain 구현은 준비 중입니다.")


