from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from app.question.models import (QuestionGenerateRequest, QuestionInstanceResponse, MemberAssignRequest, MemberAssignResponse)
from app.question.openai_question_generator import OpenAIQuestionGenerator
from app.question.service.question_service import QuestionService
from app.question.service.assignment_service import AssignmentService
from app.vector.chroma_service import ChromaVectorService
from app.core.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["기본 질문"])

service_api = QuestionService(OpenAIQuestionGenerator())
vector_service = ChromaVectorService()  # 🆕 VectorService 초기화

@router.post(
    "/api",
    response_model=QuestionInstanceResponse,
    summary="질문 생성 (RAG 자동 적용)",
    description=(
        "content를 기반으로 질문을 생성합니다. "
        "useRag=true(기본): 과거 답변이 5개 이상이면 맥락 포함, 미만이면 기본 방식. "
        "useRag=false: 항상 기본 방식 사용."
    )
)
async def generate_question(request: QuestionGenerateRequest) -> QuestionInstanceResponse:
    content_preview = request.content[:50] if len(request.content) > 50 else request.content
    logger.info(
        f"[질문 생성 요청] content: '{content_preview}...', "
        f"category: {request.category}, use_rag: {request.use_rag}"
    )
    
    past_answers = None
    
    # Early return: useRag=false면 바로 기본 방식
    if not request.use_rag:
        logger.info("[RAG 비활성화] useRag=false")
    else:
        # RAG 시도 (질문을 받을 사용자 = subject_member_id)
        user_id = request.subject_member_id
        
        # subject_member_id가 없으면 RAG 불가
        if not user_id:
            logger.warning("[RAG 비활성화] subjectMemberId 없음")
        else:
            try:
                # 1. 답변 개수 확인
                answer_count = vector_service.collection.count(
                    where={"user_id": user_id}
                )
                logger.info(f"[답변 개수 확인] user_id={user_id}, count={answer_count}")
                
                # Early return: 답변 < 5개면 기본 방식
                if answer_count < 5:
                    logger.info(f"[RAG 비활성화] 답변 부족 (count={answer_count} < 5)")
                else:
                    # 2. RAG 검색
                    past_answers = await vector_service.search_similar_answers(
                        user_id=user_id,
                        query=request.content or request.category or "",
                        top_k=settings.rag_top_k,
                        category=request.category
                    )
                    
                    if past_answers:
                        logger.info(f"[RAG 활성화] 유사 답변 {len(past_answers)}개 검색됨")
                    else:
                        logger.info("[RAG 비활성화] 검색 결과 없음")
            
            except Exception as e:
                logger.error(f"[RAG 검색 실패] error={str(e)}")
                # past_answers=None으로 기본 방식 사용
    
    # 질문 생성 (past_answers 있으면 RAG, 없으면 기존)
    try:
        result = await service_api.generate(
            request=request,
            past_answers=past_answers
        )
        
        logger.info(
            f"[질문 생성 완료] content: '{result.content}', "
            f"rag_used: {result.generation_metadata.get('ragEnabled', False)}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[질문 생성 실패] error={str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"질문 생성에 실패했습니다: {str(e)}"
        )

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