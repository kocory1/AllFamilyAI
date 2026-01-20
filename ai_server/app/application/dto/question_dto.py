"""
Question Generation DTOs

Use Case 입출력 전용 DTO
- API Schema와 분리
- Domain 개념 기반
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects.question_level import QuestionLevel


@dataclass
class GeneratePersonalQuestionInput:
    """개인 질문 생성 Use Case 입력 DTO"""

    family_id: int
    member_id: int
    role_label: str
    base_question: str
    base_answer: str
    answered_at: datetime


@dataclass
class GeneratePersonalQuestionOutput:
    """개인 질문 생성 Use Case 출력 DTO"""

    question: str
    level: QuestionLevel
    metadata: dict


# 가족 질문은 동일한 DTO 사용 (입력 구조 동일)
GenerateFamilyQuestionInput = GeneratePersonalQuestionInput
GenerateFamilyQuestionOutput = GeneratePersonalQuestionOutput
