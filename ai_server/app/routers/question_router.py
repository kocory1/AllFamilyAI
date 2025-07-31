from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from app.models.question import (
    QuestionRequest, 
    QuestionResponse, 
    QuestionListResponse,
    QuestionCategory,
    ErrorResponse
)
from app.services.openai_service import OpenAIService

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()

# OpenAI 서비스 인스턴스 생성
openai_service = OpenAIService()

@router.post(
    "/questions/generate",
    response_model=QuestionResponse,
    summary="AI 질문 생성",
    description="OpenAI API를 사용하여 가족을 위한 질문을 생성합니다."
)
async def generate_question(request: QuestionRequest) -> QuestionResponse:
    """
    AI를 사용하여 특정 가족 구성원을 위한 질문을 생성합니다.
    """
    try:
        question = await openai_service.generate_question(
            target_member=request.target_member,
            category=request.category,
            family_context=request.family_context,
            mood=request.mood
        )
        return question
        
    except Exception as e:
        logger.error(f"질문 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"질문 생성에 실패했습니다: {str(e)}"
        )

@router.get(
    "/questions/categories",
    response_model=List[str],
    summary="질문 카테고리 목록",
    description="사용 가능한 질문 카테고리 목록을 반환합니다."
)
async def get_question_categories() -> List[str]:
    """
    사용 가능한 질문 카테고리 목록을 반환합니다.
    """
    return [category.value for category in QuestionCategory]

@router.get(
    "/questions/random",
    response_model=QuestionResponse,
    summary="랜덤 질문 생성",
    description="랜덤 카테고리로 질문을 생성합니다."
)
async def generate_random_question(
    target_member: str,
    family_context: Optional[str] = None,
    mood: Optional[str] = None
) -> QuestionResponse:
    """
    랜덤 카테고리로 질문을 생성합니다.
    """
    try:
        import random
        random_category = random.choice(list(QuestionCategory))
        
        question = await openai_service.generate_question(
            target_member=target_member,
            category=random_category,
            family_context=family_context,
            mood=mood
        )
        return question
        
    except Exception as e:
        logger.error(f"랜덤 질문 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"랜덤 질문 생성에 실패했습니다: {str(e)}"
        )

@router.get(
    "/questions/daily",
    response_model=QuestionResponse,
    summary="오늘의 질문 생성",
    description="오늘 날짜를 기반으로 한 일일 질문을 생성합니다."
)
async def generate_daily_question(
    target_member: str,
    family_context: Optional[str] = None
) -> QuestionResponse:
    """
    오늘 날짜를 기반으로 한 일일 질문을 생성합니다.
    """
    try:
        from datetime import datetime
        
        # 오늘 날짜 정보를 활용한 분위기 설정
        today = datetime.now()
        weekday = today.weekday()
        
        # 요일별 분위기 설정
        mood_map = {
            0: "새로운 한 주를 시작하는 에너지 넘치는",
            1: "차분하고 집중된",
            2: "활기찬",
            3: "따뜻한",
            4: "기대감 가득한",
            5: "편안하고 여유로운",
            6: "평온한"
        }
        
        mood = mood_map.get(weekday, "따뜻한")
        
        question = await openai_service.generate_question(
            target_member=target_member,
            family_context=family_context,
            mood=mood
        )
        return question
        
    except Exception as e:
        logger.error(f"일일 질문 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"일일 질문 생성에 실패했습니다: {str(e)}"
        ) 