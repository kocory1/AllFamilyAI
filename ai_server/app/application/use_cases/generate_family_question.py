"""
가족 질문 생성 Use Case (하위 호환성 유지)

"""

# 하위 호환성을 위한 re-export
from app.application.dto.question_dto import (
    GenerateFamilyQuestionInput,
    GenerateFamilyQuestionOutput,
)
from app.application.use_cases.family_rag_question import FamilyRAGQuestionUseCase

# Alias for backward compatibility
GenerateFamilyQuestionUseCase = FamilyRAGQuestionUseCase

__all__ = [
    "GenerateFamilyQuestionUseCase",
    "GenerateFamilyQuestionInput",
    "GenerateFamilyQuestionOutput",
]
