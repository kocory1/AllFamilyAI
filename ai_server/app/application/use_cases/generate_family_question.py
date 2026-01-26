"""
가족 질문 생성 Use Case

Clean Architecture 원칙:
- Port (인터페이스)에만 의존
- Infrastructure 구현체 모름
- 순수 비즈니스 로직만 포함
"""

import logging

from app.application.dto.question_dto import (
    GenerateFamilyQuestionInput,
    GenerateFamilyQuestionOutput,
)
from app.domain.entities.qa_document import QADocument
from app.domain.ports.question_generator_port import QuestionGeneratorPort
from app.domain.ports.vector_store_port import VectorStorePort

logger = logging.getLogger(__name__)


class GenerateFamilyQuestionUseCase:
    """
    가족 질문 생성 Use Case

    개인 질문 생성과 차이점:
    - RAG 검색 시 family_id 필터 사용
    - top_k=10 (더 많은 맥락)
    """

    def __init__(
        self,
        vector_store: VectorStorePort,
        question_generator: QuestionGeneratorPort,
    ):
        """
        Use Case 초기화

        Args:
            vector_store: VectorStorePort 인터페이스
            question_generator: QuestionGeneratorPort 인터페이스
        """
        self.vector_store = vector_store
        self.question_generator = question_generator

    async def execute(self, input_dto: GenerateFamilyQuestionInput) -> GenerateFamilyQuestionOutput:
        """
        Use Case 실행

        비즈니스 플로우:
        1. Input DTO → Domain Entity 변환
        2. 벡터 스토어에 저장
        3. RAG 검색 (family_id 필터)
        4. 질문 생성
        5. Output DTO 반환

        Args:
            input_dto: 입력 DTO

        Returns:
            출력 DTO
        """
        logger.info(f"[Use Case] 가족 질문 생성 시작: family_id={input_dto.family_id}")

        # 설정값
        MAX_REGENERATION = 3
        SIMILARITY_THRESHOLD = 0.9

        # 1. Domain Entity 생성
        base_qa = QADocument(
            family_id=input_dto.family_id,
            member_id=input_dto.member_id,
            role_label=input_dto.role_label,
            question=input_dto.base_question,
            answer=input_dto.base_answer,
            answered_at=input_dto.answered_at,
        )

        # 2. RAG 검색 (family_id 필터, top_k=10, 과거 데이터만)
        rag_context = await self.vector_store.search_by_family(
            family_id=input_dto.family_id,
            query_doc=base_qa,
            top_k=10,
        )
        logger.info(f"[Use Case] RAG 검색 완료: {len(rag_context)}개")

        # 3. 질문 생성 + 중복 체크 (최대 3회)
        regeneration_count = 0
        similarity_warning = False

        for attempt in range(MAX_REGENERATION):
            question, level = await self.question_generator.generate_question(
                base_qa=base_qa,
                rag_context=rag_context,
            )
            logger.info(f"[Use Case] 질문 생성 (시도 {attempt + 1}): {question[:30]}...")

            # 유사도 검색
            similarity = await self.vector_store.search_similar_questions(
                question_text=question,
                member_id=input_dto.member_id,
            )

            # 유사도가 임계값 미만이면 성공
            if similarity < SIMILARITY_THRESHOLD:
                logger.info(f"[Use Case] 고유 질문 확인 (유사도: {similarity:.2f})")
                break

            # 마지막 시도면 경고 플래그 설정하고 탈출
            if attempt == MAX_REGENERATION - 1:
                similarity_warning = True
                logger.warning("[Use Case] 최대 재생성 횟수 도달, 마지막 질문 사용")
                break

            # 재생성 필요 (마지막 제외)
            regeneration_count += 1
            logger.warning(
                f"[Use Case] 중복 질문 감지 (유사도: {similarity:.2f}), "
                f"재생성 {regeneration_count}/{MAX_REGENERATION - 1}"
            )

        # 4. 저장 (다음 RAG를 위해)
        stored = await self.vector_store.store(base_qa)
        if not stored:
            raise Exception("벡터 DB 저장 실패")
        logger.info("[Use Case] 벡터 스토어 저장 완료")

        # 5. Output DTO 구성
        output = GenerateFamilyQuestionOutput(
            question=question,
            level=level,
            metadata={
                "rag_count": len(rag_context),
                "member_id": input_dto.member_id,
                "family_id": input_dto.family_id,
                "regeneration_count": regeneration_count,
                "similarity_warning": similarity_warning,
            },
        )

        return output
