from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime

from app.answer.models import AnswerAnalysisRequest, AnswerAnalysisResponse
from app.answer.openai_answer_analyzer import OpenAIAnswerAnalyzer
from app.answer.service.answer_service import AnswerService
from app.vector.chroma_service import ChromaVectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["답변 분석"])

service_api = AnswerService(OpenAIAnswerAnalyzer())
vector_service = ChromaVectorService()  # VectorService 초기화

@router.post(
    "/answer/api",
    response_model=AnswerAnalysisResponse,
    summary="답변 분석",
    description="질문/카테고리/태그/톤 맥락을 반영해 답변을 분석하고 JSON 스키마로 반환합니다. 분석 후 ChromaDB에 자동 저장됩니다."
)
async def analyze_answer(request: AnswerAnalysisRequest) -> AnswerAnalysisResponse:
    logger.info(f"[답변 분석 요청] user_id={request.user_id}, answer_length={len(request.answer_text)}")
    
    try:
        # 1. 답변 분석 (기존 로직)
        analysis_result = await service_api.analyze(request)
        logger.info(f"[답변 분석 완료] user_id={request.user_id}, sentiment={analysis_result.scores.get('sentiment', 0)}")
        
        # 2. ChromaDB에 자동 저장 (RAG용)
        try:
            # 고유 ID 생성: user_id + 타임스탬프 (밀리초)
            answer_id = f"{request.user_id}_{int(datetime.now().timestamp() * 1000)}"
            
            await vector_service.store_answer(
                answer_id=answer_id,
                user_id=request.user_id,
                question_text=request.question_content,
                answer_text=request.answer_text,
                category=request.question_category,
                sentiment=analysis_result.scores.get("sentiment", 0),  # 분석 결과 활용
                # timestamp는 자동 생성 (Optional)
            )
            logger.info(f"[벡터 저장 성공] answer_id={answer_id}")
        except Exception as e:
            # 저장 실패해도 분석 결과는 반환 (Graceful degradation)
            logger.error(f"[벡터 저장 실패] user_id={request.user_id}, error={str(e)}")
        
        # 3. 분석 결과 반환
        return analysis_result
        
    except Exception as e:
        logger.error(f"[답변 분석 실패] user_id={request.user_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"답변 분석에 실패했습니다: {str(e)}")

@router.post(
    "/answer/langchain",
    response_model=AnswerAnalysisResponse,
    summary="(준비중) LangChain 기반 답변 분석",
    description="LangChain 구현은 준비 중입니다."
)
async def analyze_answer_langchain(request: AnswerAnalysisRequest) -> AnswerAnalysisResponse:
    raise HTTPException(status_code=501, detail="LangChain 구현은 준비 중입니다.")


