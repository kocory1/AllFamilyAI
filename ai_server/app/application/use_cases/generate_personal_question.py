"""
개인 질문 생성 Use Case (하위 호환성 유지)

"""

# 하위 호환성을 위한 re-export
from app.application.dto.question_dto import (
    GeneratePersonalQuestionInput,
    GeneratePersonalQuestionOutput,
)
from app.application.use_cases.personal_rag_question import PersonalRAGQuestionUseCase

# Alias for backward compatibility
GeneratePersonalQuestionUseCase = PersonalRAGQuestionUseCase

__all__ = [
    "GeneratePersonalQuestionUseCase",
    "GeneratePersonalQuestionInput",
    "GeneratePersonalQuestionOutput",
]
