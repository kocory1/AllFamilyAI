"""
Question Router (Clean Architecture Version)

Clean Architecture 원칙:
- Router는 HTTP 요청만 처리
- API Schema → Use Case DTO 변환
- Use Case로 위임
- Use Case DTO → API Response 변환
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.application.dto.question_dto import (
    FamilyRecentQuestionInput,
    GenerateFamilyQuestionInput,
    GeneratePersonalQuestionInput,
)
from app.application.use_cases.family_recent_question import FamilyRecentQuestionUseCase
from app.application.use_cases.generate_family_question import GenerateFamilyQuestionUseCase
from app.application.use_cases.generate_personal_question import (
    GeneratePersonalQuestionUseCase,
)
from app.presentation.dependencies import (
    get_family_question_use_case,
    get_family_recent_question_use_case,
    get_personal_question_use_case,
)
from app.presentation.schemas.question_schemas import (
    FamilyQuestionRequestSchema,
    FamilyRecentQuestionRequestSchema,
    GenerateQuestionResponseSchema,
    PersonalQuestionRequestSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["질문 생성"])


# === 질문 생성 API ===


@router.post(
    "/generate/personal",
    response_model=GenerateQuestionResponseSchema,
    summary="개인 파생 질문 생성 (P2)",
    description="RAG로 개인의 과거 답변을 검색하여 맞춤형 후속 질문 생성",
)
async def generate_personal_question(
    request: PersonalQuestionRequestSchema,
    use_case: GeneratePersonalQuestionUseCase = Depends(get_personal_question_use_case),
) -> GenerateQuestionResponseSchema:
    """
    개인 파생 질문 생성 API (Clean Architecture)

    Router 책임:
    1. HTTP 요청 검증 (FastAPI 자동)
    2. API Schema → Use Case DTO 변환
    3. Use Case 호출
    4. Use Case DTO → API Response 변환
    5. 예외 처리
    """
    try:
        logger.info(
            f"[API] 개인 질문 생성 요청: family_id={request.familyId}, "
            f"member_id={request.memberId}"
        )

        # 1. API Schema → Use Case DTO 변환 (Adapter 역할)
        use_case_input = GeneratePersonalQuestionInput(
            family_id=request.familyId,
            member_id=request.memberId,
            role_label=request.roleLabel,
            base_question=request.baseQuestion,
            base_answer=request.baseAnswer,
            answered_at=datetime.fromisoformat(request.answeredAt.replace("Z", "+00:00")),
        )

        # 2. Use Case 실행
        output = await use_case.execute(use_case_input)

        # 3. Use Case DTO → API Response 변환 (BE member_question 테이블 구조)
        response = GenerateQuestionResponseSchema(
            memberId=request.memberId,  # BE에서 받은 값 그대로
            content=output.question,  # 질문 원문
            level=output.level.value,  # AI 자동 추론 (1-4)
            priority=2,  # 개인 RAG = 2
            metadata=output.metadata,
        )

        logger.info(f"[API] 개인 질문 생성 완료: {response.content[:30]}...")
        return response

    except Exception as e:
        logger.error(f"[API] 개인 질문 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 생성 실패: {str(e)}") from e


@router.post(
    "/generate/family",
    response_model=GenerateQuestionResponseSchema,
    summary="가족 파생 질문 생성 (P3)",
    description="RAG로 가족 구성원들의 과거 답변을 종합하여 가족 대화 질문 생성",
)
async def generate_family_question(
    request: FamilyQuestionRequestSchema,
    use_case: GenerateFamilyQuestionUseCase = Depends(get_family_question_use_case),
) -> GenerateQuestionResponseSchema:
    """
    가족 파생 질문 생성 API (Clean Architecture)

    Router 책임:
    1. HTTP 요청 검증
    2. API Schema → Use Case DTO 변환
    3. Use Case 호출
    4. Use Case DTO → API Response 변환
    5. 예외 처리
    """
    try:
        logger.info(
            f"[API] 가족 질문 생성 요청: family_id={request.familyId}, "
            f"member_id={request.memberId}"
        )

        # 1. API Schema → Use Case DTO 변환
        use_case_input = GenerateFamilyQuestionInput(
            family_id=request.familyId,
            member_id=request.memberId,
            role_label=request.roleLabel,
            base_question=request.baseQuestion,
            base_answer=request.baseAnswer,
            answered_at=datetime.fromisoformat(request.answeredAt.replace("Z", "+00:00")),
        )

        # 2. Use Case 실행
        output = await use_case.execute(use_case_input)

        # 3. Use Case DTO → API Response 변환 (BE member_question 테이블 구조)
        response = GenerateQuestionResponseSchema(
            memberId=request.memberId,  # BE에서 받은 값 그대로
            content=output.question,  # 질문 원문
            level=output.level.value,  # AI 자동 추론 (1-4)
            priority=3,  # 가족 RAG = 3
            metadata=output.metadata,
        )

        logger.info(f"[API] 가족 질문 생성 완료: {response.content[:30]}...")
        return response

    except Exception as e:
        logger.error(f"[API] 가족 질문 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 생성 실패: {str(e)}") from e


@router.post(
    "/generate/family-recent",
    response_model=GenerateQuestionResponseSchema,
    summary="가족 최근 질문 기반 생성 (P4)",
    description="가족 전체의 최근 질문을 컨텍스트로 활용하여 특정 멤버에게 질문 생성 (base_qa 불필요)",
)
async def generate_family_recent_question(
    request: FamilyRecentQuestionRequestSchema,
    use_case: FamilyRecentQuestionUseCase = Depends(get_family_recent_question_use_case),
) -> GenerateQuestionResponseSchema:
    """
    가족 최근 질문 기반 생성 API (신규)

    특징:
    - base_qa 없이 동작
    - family_id 기준으로 모든 멤버의 최근 질문 자동 조회 (멤버당 3개)
    - 벡터 DB 저장 없음
    """
    try:
        logger.info(
            f"[API] 가족 최근 질문 생성 요청: family_id={request.familyId}, "
            f"target={request.targetMemberId}"
        )

        # 1. API Schema → Use Case DTO 변환
        use_case_input = FamilyRecentQuestionInput(
            family_id=request.familyId,
            target_member_id=request.targetMemberId,
            target_role_label=request.targetRoleLabel,
        )

        # 2. Use Case 실행
        output = await use_case.execute(use_case_input)

        # 3. Use Case DTO → API Response 변환
        response = GenerateQuestionResponseSchema(
            memberId=request.targetMemberId,  # 대상 멤버 ID
            content=output.question,  # 질문 원문
            level=output.level.value,  # AI 자동 추론 (1-4)
            priority=4,  # 최근 기반 = 4
            metadata=output.metadata,
        )

        logger.info(f"[API] 가족 최근 질문 생성 완료: {response.content[:30]}...")
        return response

    except Exception as e:
        logger.error(f"[API] 가족 최근 질문 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 생성 실패: {str(e)}") from e
