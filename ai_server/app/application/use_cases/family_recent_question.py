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
from app.domain.value_objects.question_level import QuestionLevel

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
            f"family_id={input_dto.family_id}, target={input_dto.target_member_id}"
        )

        # 1. 가족 전체의 최근 질문 조회 (멤버별 3개씩)
        context = await self.vector_store.get_recent_questions_by_family(
            family_id=input_dto.family_id,
            limit_per_member=3,
        )
        logger.info(f"[Use Case] 컨텍스트 조회 완료: {len(context)}개")

        # 2. 질문 생성 + 중복 체크
        question, level, regeneration_count, similarity_warning = (
            await self._generate_for_target_with_retry(
                target_member_id=input_dto.target_member_id,
                target_role_label=input_dto.target_role_label,
                context=context,
            )
        )

        # 3. Output DTO 구성 (저장 없음)
        return FamilyRecentQuestionOutput(
            question=question,
            level=level,
            metadata={
                "context_count": len(context),
                "target_member_id": input_dto.target_member_id,
                "family_id": input_dto.family_id,
                "regeneration_count": regeneration_count,
                "similarity_warning": similarity_warning,
            },
        )

    async def _generate_for_target_with_retry(
        self,
        target_member_id: str,
        target_role_label: str,
        context: list[QADocument],
    ) -> tuple[str, QuestionLevel, int, bool]:
        """
        타겟 멤버용 질문 생성 + 중복 체크 (재생성 로직)
        """
        regeneration_count = 0
        similarity_warning = False

        for attempt in range(self.MAX_REGENERATION):
            question, level = await self.question_generator.generate_question_for_target(
                target_member_id=target_member_id,
                target_role_label=target_role_label,
                context=context,
            )
            logger.info(f"[Use Case] 질문 생성 (시도 {attempt + 1}): {question[:30]}...")

            # 유사도 검색
            similarity = await self.vector_store.search_similar_questions(
                question_text=question,
                member_id=target_member_id,
            )

            # 유사도가 임계값 미만이면 성공
            if similarity < self.SIMILARITY_THRESHOLD:
                logger.info(f"[Use Case] 고유 질문 확인 (유사도: {similarity:.2f})")
                break

            # 마지막 시도면 경고 플래그 설정하고 탈출
            if attempt == self.MAX_REGENERATION - 1:
                similarity_warning = True
                logger.warning("[Use Case] 최대 재생성 횟수 도달, 마지막 질문 사용")
                break

            # 재생성 필요 (마지막 제외)
            regeneration_count += 1
            logger.warning(
                f"[Use Case] 중복 질문 감지 (유사도: {similarity:.2f}), "
                f"재생성 {regeneration_count}/{self.MAX_REGENERATION - 1}"
            )

        return question, level, regeneration_count, similarity_warning
