import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_family_chain, get_personal_chain, get_vector_service
from app.question.chains.family_generate import FamilyGenerateChain
from app.question.chains.personal_generate import PersonalGenerateChain
from app.question.models import (
    FamilyQuestionRequest,
    GenerateQuestionResponse,
    MemberAssignRequest,
    MemberAssignResponse,
    PersonalQuestionRequest,
)
from app.question.service.assignment_service import AssignmentService
from app.question.service.generate_service import GenerateService
from app.vector.chroma_service import ChromaVectorService

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["질문 생성"])


# === 멤버 할당 API ===


@router.post(
    "/assign",
    response_model=MemberAssignResponse,
    summary="멤버 할당",
    description="최근 30회 기준으로 덜 받은 멤버에 확률을 부여해 pick_count명 선정",
)
async def assign_members(request: MemberAssignRequest) -> MemberAssignResponse:
    try:
        service = AssignmentService()
        return await service.assign_members(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"멤버 할당 실패: {str(e)}") from e


# === Phase 3: 파생 질문 생성 API ===


@router.post(
    "/generate/personal",
    response_model=GenerateQuestionResponse,
    summary="개인 파생 질문 생성 (P2)",
    description="RAG로 개인의 과거 답변을 검색하여 맞춤형 후속 질문 생성",
)
async def generate_personal_question(
    request: PersonalQuestionRequest,
    vector_service: ChromaVectorService = Depends(get_vector_service),
) -> GenerateQuestionResponse:
    """개인 파생 질문 생성 (P2)"""
    try:
        logger.info(
            f"[개인 파생 질문 요청] family_id={request.family_id}, "
            f"member_id={request.member_id}, role={request.role_label}"
        )

        # GenerateService 생성 (DI)
        service = GenerateService(vector_service=vector_service)

        # 질문 생성
        response = await service.generate_personal_question(request)

        logger.info(
            f"[개인 파생 질문 완료] question='{response.question[:30]}...', "
            f"level={response.level}"
        )

        return response

    except Exception as e:
        logger.error(f"[개인 파생 질문 실패] error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"개인 질문 생성 실패: {str(e)}") from e


@router.post(
    "/generate/family",
    response_model=GenerateQuestionResponse,
    summary="가족 파생 질문 생성 (P3)",
    description="RAG로 가족 구성원들의 과거 답변을 종합하여 가족 대화 질문 생성",
)
async def generate_family_question(
    request: FamilyQuestionRequest,
    vector_service: ChromaVectorService = Depends(get_vector_service),
    personal_chain: PersonalGenerateChain = Depends(get_personal_chain),
    family_chain: FamilyGenerateChain = Depends(get_family_chain),
) -> GenerateQuestionResponse:
    """가족 파생 질문 생성"""
    try:
        service = GenerateService(
            vector_service=vector_service,
            personal_chain=personal_chain,
            family_chain=family_chain,
        )
        return await service.generate_family_question(request)
    except Exception as e:
        logger.error(f"[가족 파생 질문 실패] error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"가족 질문 생성 실패: {str(e)}") from e
