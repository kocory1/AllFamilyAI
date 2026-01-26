"""Use Cases - 비즈니스 플로우"""

# 추상 클래스
from app.application.use_cases.base import (
    QuestionGenerationUseCase,
    RAGQuestionUseCase,
)
from app.application.use_cases.family_rag_question import FamilyRAGQuestionUseCase
from app.application.use_cases.family_recent_question import FamilyRecentQuestionUseCase
from app.application.use_cases.generate_family_question import (
    GenerateFamilyQuestionUseCase,
)

# 하위 호환성 (Deprecated - 새 코드는 위의 클래스 사용)
from app.application.use_cases.generate_personal_question import (
    GeneratePersonalQuestionUseCase,
)

# 구체 클래스
from app.application.use_cases.personal_rag_question import PersonalRAGQuestionUseCase

__all__ = [
    # 추상
    "QuestionGenerationUseCase",
    "RAGQuestionUseCase",
    # 구체
    "PersonalRAGQuestionUseCase",
    "FamilyRAGQuestionUseCase",
    "FamilyRecentQuestionUseCase",
    # 하위 호환
    "GeneratePersonalQuestionUseCase",
    "GenerateFamilyQuestionUseCase",
]
