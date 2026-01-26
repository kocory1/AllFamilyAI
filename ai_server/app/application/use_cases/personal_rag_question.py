"""
개인 RAG 질문 생성 Use Case

RAGQuestionUseCase 상속:
- RAG 검색: member_id 기반, top_k=5
"""

from app.application.dto.question_dto import (
    GeneratePersonalQuestionInput,
    GeneratePersonalQuestionOutput,
)
from app.application.use_cases.base import RAGQuestionUseCase
from app.domain.entities.qa_document import QADocument
from app.domain.value_objects.question_level import QuestionLevel


class PersonalRAGQuestionUseCase(RAGQuestionUseCase):
    """
    개인 질문 생성 Use Case

    RAG 검색:
    - member_id 기반 필터
    - top_k=5
    """

    async def _search_rag_context(
        self, input_dto: GeneratePersonalQuestionInput, base_qa: QADocument
    ) -> list[QADocument]:
        """member_id 기반 RAG 검색"""
        return await self.vector_store.search_by_member(
            member_id=input_dto.member_id,
            query_doc=base_qa,
            top_k=5,
        )

    def _get_log_prefix(self) -> str:
        return "개인 질문 생성"

    def _create_output_dto(
        self,
        question: str,
        level: QuestionLevel,
        input_dto: GeneratePersonalQuestionInput,
        rag_count: int,
        regeneration_count: int,
        similarity_warning: bool,
    ) -> GeneratePersonalQuestionOutput:
        """Output DTO 생성"""
        return GeneratePersonalQuestionOutput(
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
