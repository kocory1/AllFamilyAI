"""
Members API Schemas (Presentation Layer)

탈퇴 등 멤버 관련 API 요청/응답 스키마.
"""

from pydantic import BaseModel, ConfigDict, Field


class MemberDeleteRequestSchema(BaseModel):
    """회원 탈퇴 시 ChromaDB 이력 삭제 요청 (POST /members/delete)"""

    model_config = ConfigDict(populate_by_name=True)

    memberId: str = Field(alias="memberId", description="멤버 ID (UUID)")


class MemberDeleteResponseSchema(BaseModel):
    """회원 탈퇴 시 ChromaDB 이력 삭제 응답"""

    deletedCount: int = Field(description="삭제된 문서 수")
