from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.database.database import get_db
from app.models.enhanced_models import (
    AnswerRequest, AnswerResponse, ConversationHistoryRequest,
    ConversationHistoryResponse, SuccessResponse
)
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/answers", tags=["답변 관리"])

@router.post(
    "/",
    response_model=AnswerResponse,
    summary="답변 저장",
    description="질문에 대한 답변을 저장합니다."
)
async def save_answer(
    request: AnswerRequest,
    db: AsyncSession = Depends(get_db)
) -> AnswerResponse:
    """
    질문에 대한 답변을 저장합니다.
    """
    try:
        db_service = DatabaseService(db)
        
        # 답변 저장
        answer_db = await db_service.save_answer(
            question_uuid=request.question_uuid,
            answer_text=request.answer_text,
            answerer_name=request.answerer_name
        )
        
        # 응답 모델로 변환
        return AnswerResponse(
            id=answer_db.id,
            question_uuid=request.question_uuid,
            answer_text=answer_db.answer_text,
            answerer_name=answer_db.answerer_name,
            sentiment_score=answer_db.sentiment_score,
            keywords=answer_db.keywords,
            created_at=answer_db.created_at
        )
        
    except Exception as e:
        logger.error(f"답변 저장 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"답변 저장에 실패했습니다: {str(e)}"
        )

@router.get(
    "/question/{question_uuid}",
    response_model=List[AnswerResponse],
    summary="질문별 답변 조회",
    description="특정 질문의 모든 답변을 조회합니다."
)
async def get_answers_by_question(
    question_uuid: str,
    db: AsyncSession = Depends(get_db)
) -> List[AnswerResponse]:
    """
    특정 질문의 모든 답변을 조회합니다.
    """
    try:
        db_service = DatabaseService(db)
        
        # 질문의 답변들 조회
        answers = await db_service.get_answers_by_question(question_uuid)
        
        # 응답 모델로 변환
        return [
            AnswerResponse(
                id=answer.id,
                question_uuid=question_uuid,
                answer_text=answer.answer_text,
                answerer_name=answer.answerer_name,
                sentiment_score=answer.sentiment_score,
                keywords=answer.keywords,
                created_at=answer.created_at
            )
            for answer in answers
        ]
        
    except Exception as e:
        logger.error(f"질문별 답변 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"답변 조회에 실패했습니다: {str(e)}"
        )

@router.get(
    "/member/{answerer_name}",
    response_model=List[AnswerResponse],
    summary="구성원별 답변 조회",
    description="특정 가족 구성원의 모든 답변을 조회합니다."
)
async def get_answers_by_member(
    answerer_name: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> List[AnswerResponse]:
    """
    특정 가족 구성원의 모든 답변을 조회합니다.
    """
    try:
        db_service = DatabaseService(db)
        
        # 구성원의 답변들 조회
        answers = await db_service.get_answers_by_member(answerer_name, limit)
        
        # 응답 모델로 변환
        answer_responses = []
        for answer in answers:
            # 질문 UUID 조회 (answer.question 관계를 통해)
            question = await db_service.get_question_by_uuid(answer.question.question_uuid)
            question_uuid = question.question_uuid if question else "unknown"
            
            answer_responses.append(
                AnswerResponse(
                    id=answer.id,
                    question_uuid=question_uuid,
                    answer_text=answer.answer_text,
                    answerer_name=answer.answerer_name,
                    sentiment_score=answer.sentiment_score,
                    keywords=answer.keywords,
                    created_at=answer.created_at
                )
            )
        
        return answer_responses
        
    except Exception as e:
        logger.error(f"구성원별 답변 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"답변 조회에 실패했습니다: {str(e)}"
        )

@router.post(
    "/conversation-history",
    response_model=SuccessResponse,
    summary="대화 기록 저장",
    description="전체 대화 내용을 기록으로 저장합니다."
)
async def save_conversation_history(
    request: ConversationHistoryRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    대화 기록을 저장합니다.
    """
    try:
        db_service = DatabaseService(db)
        
        # 대화 기록 저장
        conversation = await db_service.save_conversation_history(
            question_uuid=request.question_uuid,
            conversation_data=request.conversation_data,
            participants=request.participants,
            conversation_summary=request.conversation_summary,
            emotional_tone=request.emotional_tone,
            topics_discussed=request.topics_discussed
        )
        
        return SuccessResponse(
            success=True,
            message="대화 기록이 성공적으로 저장되었습니다.",
            data={"conversation_id": conversation.id}
        )
        
    except Exception as e:
        logger.error(f"대화 기록 저장 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"대화 기록 저장에 실패했습니다: {str(e)}"
        )

@router.get(
    "/conversation-history",
    response_model=List[ConversationHistoryResponse],
    summary="대화 기록 조회",
    description="저장된 대화 기록들을 조회합니다."
)
async def get_conversation_history(
    family_id: str = "default",
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> List[ConversationHistoryResponse]:
    """
    대화 기록을 조회합니다.
    """
    try:
        db_service = DatabaseService(db)
        
        # 대화 기록 조회
        conversations = await db_service.get_conversation_history(family_id, limit)
        
        # 응답 모델로 변환
        return [
            ConversationHistoryResponse(
                id=conv.id,
                question_content=conv.question.content if conv.question else None,
                conversation_summary=conv.conversation_summary,
                emotional_tone=conv.emotional_tone,
                topics_discussed=conv.topics_discussed,
                participants=conv.participants,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"대화 기록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"대화 기록 조회에 실패했습니다: {str(e)}"
        )