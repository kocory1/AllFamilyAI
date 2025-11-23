from fastapi import APIRouter, HTTPException
import logging

from app.member_profile.models import MemberProfileComputeRequest, MemberProfileSummary
from app.member_profile.updater import DefaultProfileUpdater
from app.member_profile.service.profile_service import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/member/profile", tags=["사용자 프로필"])

service_api = ProfileService(DefaultProfileUpdater())


@router.post(
    "/analysis",
    response_model=MemberProfileSummary,
    summary="사용자 프로필 분석",
    description="답변 분석 결과를 입력으로 받아 preferences/engagement(avg_length)을 계산합니다."
)
async def compute_member_profile(request: MemberProfileComputeRequest) -> MemberProfileSummary:
    try:
        # 저장은 BE에서 수행. 본 엔드포인트는 계산(요약)만 반환
        return service_api.compute(request)
    except Exception as e:
        logger.error(f"[프로필 계산 실패] error={str(e)}")
        raise HTTPException(status_code=500, detail=f"member_profile 계산 실패: {str(e)}")


