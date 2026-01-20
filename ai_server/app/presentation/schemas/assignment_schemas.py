"""
Member Assignment Schemas (Presentation Layer)

할당자 선정 API Schema
"""

from pydantic import BaseModel, Field


class MemberAssignRequestSchema(BaseModel):
    """할당자 선정 요청 Schema"""

    familyId: int = Field(alias="familyId", description="가족 ID")
    memberIds: list[str] = Field(alias="memberIds", description="선택 가능한 멤버 ID 리스트 (UUID)")
    pickCount: int = Field(alias="pickCount", description="선택할 멤버 수", ge=1, le=10)

    class Config:
        populate_by_name = True


class MemberAssignResponseSchema(BaseModel):
    """할당자 선정 응답 Schema"""

    selectedMemberIds: list[str] = Field(
        alias="selectedMemberIds", description="선택된 멤버 ID 리스트 (UUID)"
    )
    metadata: dict = Field(description="선정 메타데이터")

    class Config:
        populate_by_name = True
