"""
가족 RAG 질문 생성 Use Case

RAGQuestionUseCase 상속:
- RAG 검색: family_id 기반, top_k=10
"""

from app.application.dto.question_dto import (
    GenerateFamilyQuestionInput,
    GenerateFamilyQuestionOutput,
)
from app.application.use_cases.base import RAGQuestionUseCase
from app.domain.entities.qa_document import QADocument
from app.domain.value_objects.question_level import QuestionLevel


class FamilyRAGQuestionUseCase(RAGQuestionUseCase):
    """
    가족 질문 생성 Use Case

    RAG 검색:
    - family_id 기반 필터
    - top_k=10 (더 많은 맥락)
    """

    async def _search_rag_context(
        self, input_dto: GenerateFamilyQuestionInput, base_qa: QADocument
    ) -> list[QADocument]:
        """family_id 기반 RAG 검색"""
        return await self.vector_store.search_by_family(
            family_id=input_dto.family_id,
            query_doc=base_qa,
            top_k=10,
        )

    def _get_log_prefix(self) -> str:
        return "가족 질문 생성"

    def _create_output_dto(
        self,
        question: str,
        level: QuestionLevel,
        input_dto: GenerateFamilyQuestionInput,
        rag_count: int,
        regeneration_count: int,
        similarity_warning: bool,
    ) -> GenerateFamilyQuestionOutput:
        """Output DTO 생성"""
        return GenerateFamilyQuestionOutput(
            question=question,
            level=level,
            metadata={
                "rag_count": rag_count,
                "member_id": input_dto.member_id,
                "family_id": input_dto.family_id,
                "regeneration_count": regeneration_count,
                "similarity_warning": similarity_warning,
            },
        )
