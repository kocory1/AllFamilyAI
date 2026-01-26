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
    member_id: str  # UUID
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


@dataclass
class FamilyRecentQuestionInput:
    """가족 최근 질문 기반 생성 Use Case 입력 DTO"""

    family_id: int
    target_member_id: str  # 질문 대상 멤버 UUID
    target_role_label: str  # 질문 대상 역할 라벨
    member_ids: list[str]  # 컨텍스트 조회할 멤버 ID 목록


@dataclass
class FamilyRecentQuestionOutput:
    """가족 최근 질문 기반 생성 Use Case 출력 DTO"""

    question: str
    level: QuestionLevel
    metadata: dict
