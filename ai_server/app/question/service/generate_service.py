"""질문 생성 서비스 (RAG 통합)"""

import logging

from app.question.chains.family_generate import FamilyGenerateChain
from app.question.chains.personal_generate import PersonalGenerateChain
from app.question.models import (
    FamilyQuestionRequest,
    GenerateQuestionResponse,
    PersonalQuestionRequest,
)
from app.vector.base import VectorService

logger = logging.getLogger(__name__)


class GenerateService:
    """질문 생성 서비스 (DI 패턴)"""

    def __init__(
        self,
        vector_service: VectorService,
        personal_chain: PersonalGenerateChain,
        family_chain: FamilyGenerateChain,
    ):
        """
        서비스 초기화

        Args:
            vector_service: VectorService 구현체 (DI)
            personal_chain: PersonalGenerateChain 구현체 (DI)
            family_chain: FamilyGenerateChain 구현체 (DI)
        """
        self.vector_service = vector_service
        self.personal_chain = personal_chain
        self.family_chain = family_chain

    async def generate_personal_question(
        self, request: PersonalQuestionRequest
    ) -> GenerateQuestionResponse:
        """
        개인 파생 질문 생성 (P2)

        프로세스:
        1. RAG로 해당 멤버의 과거 QA 검색
        2. PersonalGenerateChain 실행
        3. 응답 포맷팅

        Args:
            request: PersonalQuestionRequest

        Returns:
            GenerateQuestionResponse
        """
        try:
            logger.info(
                f"[개인 질문 생성 요청] family_id={request.family_id}, "
                f"member_id={request.member_id}, role={request.role_label}"
            )

            # 1. RAG 검색 (개인)
            if request.context:
                rag_results = await self.vector_service.search_for_personal(
                    member_id=request.member_id,
                    query=request.context,
                    top_k=5,
                )
                logger.info(f"[RAG 검색 완료] 결과 개수={len(rag_results)}")
            else:
                logger.info("[RAG 건너뜀] context 없음")
                rag_results = []

            # 2. Chain 실행
            chain_result = await self.personal_chain.generate(
                member_id=request.member_id,
                role_label=request.role_label,
                rag_results=rag_results,
                context=request.context,
            )

            # 3. 응답 구성
            response = GenerateQuestionResponse(
                question=chain_result["question"],
                level=chain_result["level"],
                metadata=chain_result["metadata"],
            )

            logger.info(
                f"[개인 질문 생성 완료] question='{response.question[:30]}...', "
                f"level={response.level}"
            )

            return response

        except Exception as e:
            logger.error(f"[개인 질문 생성 실패] error={str(e)}", exc_info=True)
            raise

    async def generate_family_question(
        self, request: FamilyQuestionRequest
    ) -> GenerateQuestionResponse:
        """
        가족 파생 질문 생성 (P3)

        프로세스:
        1. RAG로 가족 전체의 과거 QA 검색
        2. FamilyGenerateChain 실행
        3. 응답 포맷팅

        Args:
            request: FamilyQuestionRequest

        Returns:
            GenerateQuestionResponse
        """
        try:
            logger.info(
                f"[가족 질문 생성 요청] family_id={request.family_id}, "
                f"members_count={len(request.members)}"
            )

            # 1. RAG 검색 (가족)
            if request.context:
                rag_results = await self.vector_service.search_for_family(
                    family_id=request.family_id,
                    query=request.context,
                    top_k=10,  # 가족은 더 많이
                )
                logger.info(f"[RAG 검색 완료] 결과 개수={len(rag_results)}")
            else:
                logger.info("[RAG 건너뜀] context 없음")
                rag_results = []

            # 2. Chain 실행
            members_dict = [
                {"member_id": m.member_id, "role_label": m.role_label} for m in request.members
            ]

            chain_result = await self.family_chain.generate(
                family_id=request.family_id,
                members=members_dict,
                rag_results=rag_results,
                context=request.context,
            )

            # 3. 응답 구성
            response = GenerateQuestionResponse(
                question=chain_result["question"],
                level=chain_result["level"],
                metadata=chain_result["metadata"],
            )

            logger.info(
                f"[가족 질문 생성 완료] question='{response.question[:30]}...', "
                f"level={response.level}"
            )

            return response

        except Exception as e:
            logger.error(f"[가족 질문 생성 실패] error={str(e)}", exc_info=True)
            raise
