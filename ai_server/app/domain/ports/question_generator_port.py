"""
Question Generator Port (인터페이스)

Clean Architecture - 의존성 역전 원칙:
- Domain Layer가 정의하는 인터페이스
- Infrastructure Layer가 구현
- Use Case는 이 인터페이스에만 의존
"""

from abc import ABC, abstractmethod

from app.domain.entities.qa_document import QADocument
from app.domain.value_objects.question_level import QuestionLevel


class QuestionGeneratorPort(ABC):
    """
    질문 생성기 인터페이스 (Port)

    구현체는 Infrastructure Layer에 위치:
    - LangchainPersonalGenerator (LangChain 기반 개인 질문 생성)
    - LangchainFamilyGenerator (LangChain 기반 가족 질문 생성)
    - SemanticKernelGenerator (향후: Semantic Kernel 기반)
    - MockQuestionGenerator (테스트용)

    의존성 방향: Domain ← Infrastructure (역전)

    Use Case는 LangChain의 존재를 모름!
    """

    @abstractmethod
    async def generate_question(
        self,
        base_qa: QADocument,
        rag_context: list[QADocument],
    ) -> tuple[str, QuestionLevel]:
        """
        파생 질문 생성

        Args:
            base_qa: 기준 QA (Domain Entity)
            rag_context: RAG 검색된 과거 QA 목록 (Domain Entities)

        Returns:
            (생성된 질문, 난이도) 튜플
        """
        pass

    @abstractmethod
    async def generate_question_for_target(
        self,
        target_member_id: str,
        target_role_label: str,
        context: list[QADocument],
    ) -> tuple[str, QuestionLevel]:
        """
        특정 멤버를 대상으로 질문 생성 (base_qa 없이)

        Args:
            target_member_id: 질문 대상 멤버 ID
            target_role_label: 질문 대상 역할 라벨 (예: "아빠", "엄마")
            context: 최근 QA 컨텍스트 목록 (Domain Entities)

        Returns:
            (생성된 질문, 난이도) 튜플
        """
        pass
