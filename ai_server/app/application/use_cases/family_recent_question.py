"""
가족 최근 질문 기반 Use Case (신규 API)

QuestionGenerationUseCase 직접 상속:
- RAG 사용 안 함 (최신 질문 조회)
- base_qa 없음
- 저장 안 함
"""

import logging

from app.application.dto.question_dto import (
    FamilyRecentQuestionInput,
    FamilyRecentQuestionOutput,
)
from app.application.use_cases.base import QuestionGenerationUseCase
from app.domain.entities.qa_document import QADocument

logger = logging.getLogger(__name__)


class FamilyRecentQuestionUseCase(QuestionGenerationUseCase):
    """
    가족 최근 질문 기반 Use Case

    특징:
    - base_qa 없음 (사용자 입력 질문/답변 없음)
    - 각 멤버별 최근 2개 질문을 컨텍스트로 사용
    - 벡터 DB 저장 안 함
    """

    async def execute(
        self, input_dto: FamilyRecentQuestionInput
    ) -> FamilyRecentQuestionOutput:
        """
        Use Case 실행

        비즈니스 플로우:
        1. 각 멤버별 최근 질문 조회
        2. 질문 생성 + 중복 체크
        3. Output DTO 반환 (저장 없음)
        """
        logger.info(
            f"[Use Case] 가족 최근 질문 생성 시작: "
            f"family_id={input_dto.family_id}, target={input_dto.member_id}"
        )

        # 1. 가족 전체의 최근 질문 조회 (멤버별 3개씩)
        context = await self.vector_store.get_recent_questions_by_family(
            family_id=input_dto.family_id,
            limit_per_member=3,
        )
        logger.info(f"[Use Case] 컨텍스트 조회 완료: {len(context)}개")

        # 2. 타겟 멤버의 role_label 추출 (컨텍스트에서)
        target_role_label = self._extract_role_label(context, input_dto.member_id)
        if not target_role_label:
            logger.warning(
                f"[Use Case] 타겟 멤버의 role_label을 찾을 수 없음: member_id={input_dto.member_id}"
            )
            target_role_label = "멤버"  # 기본값

        # 3. 질문 생성 + 중복 체크 (base 클래스의 공통 메서드 사용)
        question, level, regeneration_count, similarity_warning = (
            await self._generate_for_target_with_retry(
                member_id=input_dto.member_id,
                role_label=target_role_label,
                context=context,
            )
        )

        # 3. Output DTO 구성 (저장 없음)
        return FamilyRecentQuestionOutput(
            question=question,
            level=level,
            metadata={
                "context_count": len(context),
                "member_id": input_dto.member_id,
                "family_id": input_dto.family_id,
                "regeneration_count": regeneration_count,
                "similarity_warning": similarity_warning,
            },
        )

    def _extract_role_label(
        self, context: list[QADocument], target_member_id: str
    ) -> str | None:
        """
        컨텍스트에서 타겟 멤버의 role_label 추출

        Args:
            context: 가족 최근 질문 리스트
            target_member_id: 타겟 멤버 ID

        Returns:
            role_label 또는 None (찾지 못한 경우)
        """
        for doc in context:
            if doc.member_id == target_member_id:
                return doc.role_label
        return None
