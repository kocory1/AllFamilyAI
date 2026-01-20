"""
개인 질문 생성 Use Case

Clean Architecture 원칙:
- Port (인터페이스)에만 의존
- Infrastructure 구현체 모름
- 순수 비즈니스 로직만 포함
"""

import logging

from app.application.dto.question_dto import (
    GeneratePersonalQuestionInput,
    GeneratePersonalQuestionOutput,
)
from app.domain.entities.qa_document import QADocument
from app.domain.ports.question_generator_port import QuestionGeneratorPort
from app.domain.ports.vector_store_port import VectorStorePort

logger = logging.getLogger(__name__)


class GeneratePersonalQuestionUseCase:
    """
    개인 질문 생성 Use Case

    Clean Architecture 원칙:
    - 인터페이스(Port)에만 의존 → 의존성 역전
    - LangChain, ChromaDB 등 구체 구현 모름
    - 순수 비즈니스 로직만 포함

    의존성:
    - VectorStorePort (인터페이스)
    - QuestionGeneratorPort (인터페이스)
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

    async def execute(
        self, input_dto: GeneratePersonalQuestionInput
    ) -> GeneratePersonalQuestionOutput:
        """
        Use Case 실행

        비즈니스 플로우:
        1. Input DTO → Domain Entity 변환
        2. 벡터 스토어에 저장 (Port 호출)
        3. RAG 검색 (Port 호출)
        4. 질문 생성 (Port 호출)
        5. Output DTO 반환

        Args:
            input_dto: 입력 DTO

        Returns:
            출력 DTO
        """
        logger.info(f"[Use Case] 개인 질문 생성 시작: member_id={input_dto.member_id}")

        # 1. Domain Entity 생성
        base_qa = QADocument(
            family_id=input_dto.family_id,
            member_id=input_dto.member_id,
            role_label=input_dto.role_label,
            question=input_dto.base_question,
            answer=input_dto.base_answer,
            answered_at=input_dto.answered_at,
        )

        # 2. 저장 (Port 호출 - 구체 구현 모름)
        await self.vector_store.store(base_qa)
        logger.info("[Use Case] 벡터 스토어 저장 완료")

        # 3. RAG 검색 (Port 호출 - 구체 구현 모름)
        rag_context = await self.vector_store.search_by_member(
            member_id=input_dto.member_id,
            query_doc=base_qa,
            top_k=5,
        )
        logger.info(f"[Use Case] RAG 검색 완료: {len(rag_context)}개")

        # 4. 질문 생성 (Port 호출 - 구체 구현 모름)
        question, level = await self.question_generator.generate_question(
            base_qa=base_qa,
            rag_context=rag_context,
        )
        logger.info(f"[Use Case] 질문 생성 완료: {question[:30]}...")

        # 5. Output DTO 구성
        output = GeneratePersonalQuestionOutput(
            question=question,
            level=level,
            metadata={
                "rag_count": len(rag_context),
                "member_id": input_dto.member_id,
                "family_id": input_dto.family_id,
            },
        )

        return output
