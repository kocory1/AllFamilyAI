"""
FastAPI API Schemas (Presentation Layer)

역할:
- FastAPI 입력 검증 (Pydantic)
- camelCase ↔ snake_case 변환
- HTTP 계층에서만 사용
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PersonalQuestionRequestSchema(BaseModel):
    """
    개인 질문 생성 API 요청 스키마 (Presentation Layer)

    Clean Architecture:
    - API Schema (Pydantic)와 Use Case DTO (dataclass) 분리
    - Router에서 변환 수행
    """

    model_config = ConfigDict(populate_by_name=True)

    familyId: int = Field(alias="familyId", description="가족 ID")
    memberId: str = Field(alias="memberId", description="멤버 ID (UUID)")
    roleLabel: str = Field(alias="roleLabel", description="역할 레이블 (예: 첫째 딸)")
    baseQuestion: str = Field(alias="baseQuestion", description="기준 질문")
    baseAnswer: str = Field(alias="baseAnswer", description="기준 답변")
    answeredAt: str = Field(alias="answeredAt", description="답변 시각 (ISO 8601)")


class FamilyQuestionRequestSchema(BaseModel):
    """가족 질문 생성 API 요청 스키마 (입력 구조 동일)"""

    model_config = ConfigDict(populate_by_name=True)

    familyId: int = Field(alias="familyId", description="가족 ID")
    memberId: str = Field(alias="memberId", description="답변한 멤버 ID (UUID)")
    roleLabel: str = Field(alias="roleLabel", description="역할 레이블")
    baseQuestion: str = Field(alias="baseQuestion", description="기준 질문")
    baseAnswer: str = Field(alias="baseAnswer", description="기준 답변")
    answeredAt: str = Field(alias="answeredAt", description="답변 시각 (ISO 8601)")


class FamilyRecentQuestionRequestSchema(BaseModel):
    """
    가족 최근 질문 기반 생성 API 요청 스키마 (신규 API)

    - base_qa 없음 (기존 질문/답변 입력 불필요)
    - 각 멤버의 최근 질문을 컨텍스트로 활용
    """

    model_config = ConfigDict(populate_by_name=True)

    familyId: int = Field(alias="familyId", description="가족 ID")
    targetMemberId: str = Field(
        alias="targetMemberId", description="질문 대상 멤버 ID (UUID)"
    )
    targetRoleLabel: str = Field(
        alias="targetRoleLabel", description="질문 대상 역할 라벨 (예: 아빠)"
    )
    memberIds: list[str] = Field(
        alias="memberIds", description="컨텍스트 조회할 멤버 ID 목록"
    )


class GenerateQuestionResponseSchema(BaseModel):
    """
    질문 생성 API 응답 스키마

    BE의 member_question 테이블에 바로 insert 가능한 구조
    """

    model_config = ConfigDict(populate_by_name=True)

    memberId: str = Field(
        alias="memberId", description="멤버 ID (UUID, BE에서 받은 값 그대로 반환)"
    )
    content: str = Field(description="생성된 질문 원문")
    level: int = Field(description="질문 난이도 (1-4, AI 자동 추론)", ge=1, le=4)
    priority: int = Field(description="질문 우선순위 (개인 RAG=2, 가족 RAG=3, 최근=4)", ge=1, le=4)
    metadata: dict[str, Any] = Field(description="생성 메타데이터")
