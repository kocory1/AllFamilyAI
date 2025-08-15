from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.database.database import get_db
from app.models.enhanced_models import (
    MCPQuestionRequest, FollowUpQuestionRequest, ThemedQuestionsRequest,
    ConversationAnalysisRequest, ConversationAnalysisResponse,
    FamilyAnalysisResponse, MCPErrorResponse, SuccessResponse
)
from app.models.question import QuestionResponse
from app.services.enhanced_openai_service import EnhancedOpenAIService
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP (Model Context Protocol)"])

@router.post(
    "/questions/generate",
    response_model=QuestionResponse,
    summary="MCP 기반 개인화 질문 생성",
    description="과거 질문-답변 데이터를 분석하여 개인화된 질문을 생성합니다."
)
async def generate_mcp_question(
    request: MCPQuestionRequest,
    db: AsyncSession = Depends(get_db)
) -> QuestionResponse:
    """
    MCP를 활용한 개인화된 질문을 생성합니다.
    """
    try:
        enhanced_service = EnhancedOpenAIService(db)
        db_service = DatabaseService(db)
        
        # MCP 기반 질문 생성
        question = await enhanced_service.generate_contextual_question(
            target_member=request.target_member,
            family_id=request.family_id,
            category=request.category,
            family_context=request.family_context,
            mood=request.mood,
            use_mcp=request.use_mcp
        )
        
        # 생성된 질문을 DB에 저장
        await db_service.save_question(question, request.family_id)
        
        return question
        
    except Exception as e:
        logger.error(f"MCP 질문 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"개인화된 질문 생성에 실패했습니다: {str(e)}"
        )

@router.post(
    "/questions/follow-up",
    response_model=QuestionResponse,
    summary="후속 질문 생성",
    description="이전 답변을 바탕으로 자연스러운 후속 질문을 생성합니다."
)
async def generate_follow_up_question(
    request: FollowUpQuestionRequest,
    db: AsyncSession = Depends(get_db)
) -> QuestionResponse:
    """
    이전 답변을 분석하여 후속 질문을 생성합니다.
    """
    try:
        enhanced_service = EnhancedOpenAIService(db)
        db_service = DatabaseService(db)
        
        # 후속 질문 생성
        question = await enhanced_service.generate_follow_up_question(
            target_member=request.target_member,
            previous_answer=request.previous_answer,
            original_question=request.original_question,
            family_id=request.family_id
        )
        
        # 생성된 질문을 DB에 저장
        await db_service.save_question(question, request.family_id)
        
        return question
        
    except Exception as e:
        logger.error(f"후속 질문 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"후속 질문 생성에 실패했습니다: {str(e)}"
        )

@router.post(
    "/questions/themed",
    response_model=List[QuestionResponse],
    summary="테마별 질문 생성",
    description="특정 테마에 맞는 여러 질문을 한번에 생성합니다."
)
async def generate_themed_questions(
    request: ThemedQuestionsRequest,
    db: AsyncSession = Depends(get_db)
) -> List[QuestionResponse]:
    """
    특정 테마에 맞는 여러 질문을 생성합니다.
    """
    try:
        enhanced_service = EnhancedOpenAIService(db)
        db_service = DatabaseService(db)
        
        # 테마별 질문 생성
        questions = await enhanced_service.generate_themed_questions(
            target_member=request.target_member,
            theme=request.theme,
            count=request.count,
            family_id=request.family_id
        )
        
        # 생성된 질문들을 DB에 저장
        for question in questions:
            await db_service.save_question(question, request.family_id)
        
        return questions
        
    except Exception as e:
        logger.error(f"테마별 질문 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"테마별 질문 생성에 실패했습니다: {str(e)}"
        )

@router.get(
    "/analysis/family/{target_member}",
    response_model=FamilyAnalysisResponse,
    summary="가족 구성원 패턴 분석",
    description="특정 가족 구성원의 질문-답변 패턴을 분석합니다."
)
async def analyze_family_patterns(
    target_member: str,
    family_id: str = "default",
    db: AsyncSession = Depends(get_db)
) -> FamilyAnalysisResponse:
    """
    가족 구성원의 대화 패턴을 분석합니다.
    """
    try:
        enhanced_service = EnhancedOpenAIService(db)
        
        # 가족 패턴 분석
        analysis = await enhanced_service.mcp_service.analyze_family_patterns(
            family_id=family_id,
            target_member=target_member
        )
        
        return FamilyAnalysisResponse(**analysis)
        
    except Exception as e:
        logger.error(f"가족 패턴 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"가족 패턴 분석에 실패했습니다: {str(e)}"
        )

@router.post(
    "/analysis/conversation",
    response_model=ConversationAnalysisResponse,
    summary="대화 효과성 분석",
    description="대화의 질과 효과성을 분석하여 개선점을 제안합니다."
)
async def analyze_conversation_effectiveness(
    request: ConversationAnalysisRequest,
    db: AsyncSession = Depends(get_db)
) -> ConversationAnalysisResponse:
    """
    대화의 효과성을 분석합니다.
    """
    try:
        enhanced_service = EnhancedOpenAIService(db)
        db_service = DatabaseService(db)
        
        # 대화 효과성 분석
        analysis = await enhanced_service.analyze_conversation_effectiveness(
            conversation_data=request.conversation_data
        )
        
        # 대화 기록 저장
        await db_service.save_conversation_history(
            question_uuid=request.question_uuid,
            conversation_data=request.conversation_data,
            participants=request.participants,
            emotional_tone=analysis.get("dominant_tone"),
            topics_discussed=analysis.get("topics", [])
        )
        
        return ConversationAnalysisResponse(**analysis)
        
    except Exception as e:
        logger.error(f"대화 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"대화 분석에 실패했습니다: {str(e)}"
        )

@router.get(
    "/context/{target_member}",
    summary="MCP 컨텍스트 조회",
    description="특정 가족 구성원의 MCP 컨텍스트 데이터를 조회합니다."
)
async def get_mcp_context(
    target_member: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    MCP 컨텍스트 데이터를 조회합니다.
    """
    try:
        enhanced_service = EnhancedOpenAIService(db)
        
        # 컨텍스트 데이터 수집
        from app.models.question import QuestionCategory
        cat = QuestionCategory(category) if category else None
        
        context_data = await enhanced_service.mcp_service.get_contextual_question_data(
            target_member=target_member,
            category=cat
        )
        
        return {
            "success": True,
            "target_member": target_member,
            "context_data": context_data,
            "generated_at": context_data.get("analysis_timestamp")
        }
        
    except Exception as e:
        logger.error(f"MCP 컨텍스트 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"컨텍스트 조회에 실패했습니다: {str(e)}"
        )

@router.delete(
    "/data/cleanup",
    response_model=SuccessResponse,
    summary="오래된 데이터 정리",
    description="지정된 기간보다 오래된 MCP 데이터를 정리합니다."
)
async def cleanup_old_mcp_data(
    days_to_keep: int = 365,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    오래된 MCP 데이터를 정리합니다.
    """
    try:
        db_service = DatabaseService(db)
        
        # 데이터 정리 실행
        cleanup_result = await db_service.cleanup_old_data(days_to_keep)
        
        if "error" in cleanup_result:
            raise Exception(cleanup_result["error"])
        
        return SuccessResponse(
            success=True,
            message=f"데이터 정리 완료: 대화 {cleanup_result.get('deleted_conversations', 0)}개, 컨텍스트 {cleanup_result.get('deleted_contexts', 0)}개 삭제",
            data=cleanup_result
        )
        
    except Exception as e:
        logger.error(f"데이터 정리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"데이터 정리에 실패했습니다: {str(e)}"
        )