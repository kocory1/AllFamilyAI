"""
Members Router (탈퇴 등)

POST /members/delete: ChromaDB에서 해당 member_id 이력 전부 삭제.
- 검색 결과 없으면 400 + 서버 로그
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.domain.ports.vector_store_port import VectorStorePort
from app.presentation.dependencies import get_vector_store
from app.presentation.schemas.members_schemas import (
    MemberDeleteRequestSchema,
    MemberDeleteResponseSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/members", tags=["멤버"])


@router.post(
    "/delete",
    response_model=MemberDeleteResponseSchema,
    summary="회원 탈퇴 시 ChromaDB 이력 삭제",
    description="해당 member_id의 ChromaDB QA 이력 전부 삭제. 저장된 이력이 없으면 400.",
)
async def delete_member_data(
    request: MemberDeleteRequestSchema,
    vector_store: Annotated[VectorStorePort, Depends(get_vector_store)],
) -> MemberDeleteResponseSchema:
    member_id = request.memberId
    deleted = await vector_store.delete_by_member(member_id)
    if deleted == 0:
        logger.warning(
            "[API] members/delete: ChromaDB에 해당 member_id 이력 없음, 400 반환. member_id=%s",
            member_id,
        )
        raise HTTPException(
            status_code=400,
            detail="해당 멤버의 AI 저장 이력이 없습니다. 이미 삭제되었거나 가입 후 답변이 없을 수 있습니다.",
        )
    return MemberDeleteResponseSchema(deletedCount=deleted)
